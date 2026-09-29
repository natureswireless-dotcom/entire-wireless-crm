"""Sales & Growth extension. Additive SQLite tables; no outbound marketing messages."""
import os
import csv
import html
import io
import json
import re
import secrets
import hashlib
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from types import SimpleNamespace
from urllib.parse import urlencode
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response

ZIPS = {'60953': 'Milford', '60963': 'Rossville', '60970': 'Watseka', '60942': 'Hoopeston'}
STAGES = ['New inquiry', 'Address checked', 'Quote sent', 'Decision pending', 'Paid', 'Activated', 'Unavailable', 'Lost', 'Follow up later']
CLOSED = ('Unavailable', 'Lost')
DEFAULTS = dict(service=8500, lease=1000, activation=2500, wholesale_service=7000,
                wholesale_modem=1000, other_monthly=0, overhead=0, launch_budget=5000,
                goal=5, public_enabled=False)

def esc(value): return html.escape(str(value if value is not None else ''), quote=True)
def dollars(cents): return f'${int(cents)/100:,.2f}'
def cents(value):
    try:
        n = Decimal(str(value))
        if not n.is_finite() or n < 0 or n > 1000000 or n.as_tuple().exponent < -2: raise ValueError()
        return int(n * 100)
    except (InvalidOperation, ValueError): raise HTTPException(400, 'Enter a nonnegative dollar amount with at most two decimal places.')
def day(value, required=False):
    if not value and not required: return ''
    try: return date.fromisoformat(value).isoformat()
    except (ValueError, TypeError): raise HTTPException(400, 'Enter a valid date.')
def text(f, key, limit=2000, required=False):
    v = str(f.get(key, '')).strip()
    if len(v) > limit or (required and not v): raise HTTPException(400, f'Check {key}: required values and length limits apply.')
    return v
def select(name, options, current=''):
    return f'<label>{esc(name.replace("_", " ").title())}</label><select name="{esc(name)}">'+''.join(f'<option value="{esc(v)}" {"selected" if str(v)==str(current) else ""}>{esc(label)}</option>' for v,label in options)+'</select>'
def field(name, value='', kind='text', required=False, label=None):
    return f'<label>{esc(label or name.replace("_", " ").title())}</label><input name="{esc(name)}" type="{kind}" value="{esc(value)}" {"required" if required else ""} {"step=0.01 min=0" if kind=="number" else ""} maxlength="2000">'
def area(name, value='', label=None):
    return f'<label>{esc(label or name.replace("_", " ").title())}</label><textarea name="{esc(name)}" maxlength="10000">{esc(value)}</textarea>'
def table(headers, rows):
    return '<div style="overflow-x:auto"><table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+(''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in r)+'</tr>' for r in rows) or f'<tr><td colspan="{len(headers)}">No records yet.</td></tr>')+'</tbody></table></div>'

def install(namespace):
    m = SimpleNamespace(**namespace)
    app = m.app
    def today(): return m.business_now().date().isoformat()
    def settings():
        with m.conn() as c: r=c.execute("SELECT value FROM settings WHERE key='growth_config'").fetchone()
        return {**DEFAULTS, **(json.loads(r['value']) if r else {})}
    def token(request):
        if 'growth_csrf' not in request.session: request.session['growth_csrf']=secrets.token_urlsafe(32)
        return f'<input type="hidden" name="csrf" value="{request.session["growth_csrf"]}">'
    def form(request, action, body, button='Save'):
        return f'<form method="post" action="{action}">{token(request)}{body}<button class="btn">{esc(button)}</button></form>'
    async def checked(request, admin=False):
        (m.require_admin if admin else m.require_staff)(request)
        f=await request.form()
        if not secrets.compare_digest(str(f.get('csrf','')), request.session.get('growth_csrf','missing')): raise HTTPException(403, 'Form expired. Reload and try again.')
        return f
    def record(c, lid):
        r=c.execute('SELECT * FROM growth_leads WHERE id=?',(lid,)).fetchone()
        if not r: raise HTTPException(404, 'Lead not found.')
        return dict(r)
    def log(c,request,lid,action,detail=''):
        actor=request.session.get('user_email','Public inquiry') if request else 'system'
        c.execute('INSERT INTO growth_events(lead_id,actor,action,details) VALUES (?,?,?,?)',(lid,actor,action,detail))
    def task(c, title, due, lid=None, partner=None, key=None):
        owner=c.execute('SELECT owner_id FROM growth_leads WHERE id=?',(lid,)).fetchone() if lid else None
        c.execute('INSERT OR IGNORE INTO growth_tasks(title,due_date,lead_id,partner_id,unique_key,owner_id) VALUES (?,?,?,?,?,?)',(title,due,lid,partner,key,owner['owner_id'] if owner else None))
    def shell(request,title,body):
        links='<div class="actions"><a class="btn secondary" href="/growth">Overview</a><a class="btn secondary" href="/growth/leads">Leads</a><a class="btn secondary" href="/growth/tasks">Tasks</a><a class="btn secondary" href="/growth/partners">Partners</a><a class="btn secondary" href="/growth/areas">Coverage research</a><a class="btn secondary" href="/growth/reports">Reports & spending</a><a class="btn secondary" href="/growth/setup">Launch setup</a></div>'
        return m.page(request,title,f'<h1>{esc(title)}</h1>{links}<section class="section">{body}</section>')
    def migrate():
        with m.conn() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS growth_leads(
              id INTEGER PRIMARY KEY, first_name TEXT NOT NULL,last_name TEXT NOT NULL,
              email TEXT NOT NULL DEFAULT '',phone TEXT NOT NULL DEFAULT '',service_address TEXT NOT NULL,
              city TEXT NOT NULL DEFAULT '',zip TEXT NOT NULL,rural TEXT NOT NULL DEFAULT 'Unknown',
              preferred_contact TEXT NOT NULL DEFAULT 'Phone',source TEXT NOT NULL DEFAULT 'Direct',
              partner_id INTEGER,owner_id INTEGER,current_provider TEXT DEFAULT '',current_price INTEGER DEFAULT 0,
              problem TEXT DEFAULT '',needs TEXT DEFAULT '',timing TEXT DEFAULT '',eligibility TEXT DEFAULT 'Unchecked',
              eligibility_notes TEXT DEFAULT '',stage TEXT NOT NULL DEFAULT 'New inquiry',next_action TEXT DEFAULT '',next_date TEXT DEFAULT '',
              lost_reason TEXT DEFAULT '',do_not_contact INTEGER DEFAULT 0,contact_consent INTEGER DEFAULT 0,
              notes TEXT DEFAULT '',customer_id INTEGER UNIQUE,invoice_id INTEGER,quote_id INTEGER,
              paid_at TEXT,activated_at TEXT,cancelled_at TEXT,agreement_evidence TEXT DEFAULT '',test_results TEXT DEFAULT '',
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS growth_quotes(id INTEGER PRIMARY KEY,lead_id INTEGER NOT NULL,
              service INTEGER NOT NULL,lease INTEGER NOT NULL,activation INTEGER NOT NULL,wholesale_service INTEGER NOT NULL,
              wholesale_modem INTEGER NOT NULL,other_monthly INTEGER NOT NULL,contract_months INTEGER NOT NULL,
              terms TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(lead_id) REFERENCES growth_leads(id));
            CREATE TABLE IF NOT EXISTS growth_events(id INTEGER PRIMARY KEY,lead_id INTEGER,actor TEXT,action TEXT,details TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS growth_partners(id INTEGER PRIMARY KEY,name TEXT NOT NULL,kind TEXT,contact TEXT,email TEXT,phone TEXT,zip TEXT,permission TEXT DEFAULT 'Not asked',notes TEXT,next_date TEXT);
            CREATE TABLE IF NOT EXISTS growth_tasks(id INTEGER PRIMARY KEY,title TEXT NOT NULL,due_date TEXT NOT NULL,lead_id INTEGER,partner_id INTEGER,owner_id INTEGER,status TEXT DEFAULT 'Open',completed_at TEXT,notes TEXT DEFAULT '',unique_key TEXT UNIQUE);
            CREATE TABLE IF NOT EXISTS growth_expenses(id INTEGER PRIMARY KEY,spent_on TEXT NOT NULL,source TEXT NOT NULL,amount INTEGER NOT NULL,minutes INTEGER DEFAULT 0,notes TEXT);
            CREATE TABLE IF NOT EXISTS growth_areas(id INTEGER PRIMARY KEY,zip TEXT NOT NULL,address TEXT NOT NULL,existing_options TEXT,eligibility TEXT,test_notes TEXT,checked_on TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS growth_rate_limits(key TEXT PRIMARY KEY,window INTEGER,count INTEGER);
            CREATE INDEX IF NOT EXISTS growth_lead_stage ON growth_leads(stage,zip);
            CREATE INDEX IF NOT EXISTS growth_task_due ON growth_tasks(status,due_date);
            ''')
    migrate()

    def sync():
        """Observe recorded payments. Never contact prospects or activate carrier service."""
        with m.conn() as c:
            c.execute('BEGIN IMMEDIATE')
            rows=c.execute("SELECT l.id,l.stage,l.paid_at,l.customer_id,l.activated_at,l.cancelled_at,i.status,i.subtotal,i.amount_paid,c.status customer_status FROM growth_leads l JOIN invoices i ON i.id=l.invoice_id JOIN customers c ON c.id=l.customer_id").fetchall()
            for r in rows:
                paid=r['status']!='Void' and r['subtotal']>0 and r['amount_paid']>=r['subtotal']-.005
                if paid and not r['paid_at']:
                    c.execute("UPDATE growth_leads SET paid_at=?,stage=CASE WHEN stage IN ('Lost','Unavailable') THEN stage ELSE 'Paid' END WHERE id=?",(today(),r['id']))
                    log(c,None,r['id'],'Initial invoice paid','Payment verified from linked CRM invoice.')
                    task(c,'Schedule activation and verify equipment',today(),r['id'],key=f"paid:{r['id']}")
                    c.execute("UPDATE growth_tasks SET status='Cancelled' WHERE lead_id=? AND status='Open' AND (unique_key LIKE 'quote:%' OR unique_key LIKE 'collect:%')",(r['id'],))
                    c.execute("UPDATE growth_leads SET next_action='Schedule activation and verify equipment',next_date=? WHERE id=?",(today(),r['id']))
                if not paid and r['paid_at'] and not r['activated_at']:
                    c.execute("UPDATE growth_leads SET paid_at=NULL,stage='Decision pending',next_action='Review initial invoice balance',next_date=? WHERE id=?",(today(),r['id']))
                    task(c,'Review initial invoice balance',today(),r['id'],key=f"balance:{r['id']}")
                if r['activated_at'] and r['customer_status']=='Inactive' and not r['cancelled_at']:
                    c.execute('UPDATE growth_leads SET cancelled_at=? WHERE id=?',(today(),r['id']))
                    task(c,'Review cancellation reason and wholesale charges',today(),r['id'],key=f"cancel:{r['id']}")
                elif r['activated_at'] and r['customer_status']=='Active' and r['cancelled_at']:
                    c.execute('UPDATE growth_leads SET cancelled_at=NULL WHERE id=?',(r['id'],))
    namespace['sync_growth']=sync

    @app.get('/growth',response_class=HTMLResponse)
    def overview(request:Request):
        m.require_staff(request); sync(); cfg=settings()
        with m.conn() as c:
            count=c.execute('SELECT COUNT(*) FROM growth_leads').fetchone()[0]
            active=c.execute("SELECT COUNT(*) FROM growth_leads WHERE activated_at IS NOT NULL AND cancelled_at IS NULL").fetchone()[0]
            due=c.execute("SELECT t.*,l.first_name,l.last_name FROM growth_tasks t LEFT JOIN growth_leads l ON l.id=t.lead_id WHERE t.status='Open' AND t.due_date<=? ORDER BY due_date LIMIT 25",(today(),)).fetchall()
            spend=c.execute('SELECT COALESCE(SUM(amount),0) FROM growth_expenses').fetchone()[0]
            missing=c.execute("SELECT COUNT(*) FROM growth_leads WHERE stage NOT IN ('Lost','Unavailable','Activated') AND do_not_contact=0 AND (next_action='' OR next_date='')").fetchone()[0]
        margin=cfg['service']+cfg['lease']-cfg['wholesale_service']-cfg['wholesale_modem']-cfg['other_monthly']
        cards=''.join(f'<div class="card"><div>{esc(label)}</div><div class="metric">{esc(value)}</div></div>' for label,value in [('Inquiries',count),('Activated / goal',f'{active} / {cfg["goal"]}'),('Default monthly remainder',dollars(margin)),('Launch spending',dollars(spend))])
        rows=[[esc(r['due_date']),esc(r['title']),f'<a href="/growth/leads/{r["lead_id"]}">{esc(r["first_name"])} {esc(r["last_name"])}</a>' if r['lead_id'] else 'Launch / partner',form(request,f'/growth/tasks/{r["id"]}/complete','','Complete')] for r in due]
        return shell(request,'Sales & Growth',f'<div class="grid">{cards}</div><p>Target rural ZIP codes: {", ".join(ZIPS)}. Remainder excludes unentered expenses and overhead; it is not net profit.</p><p>{missing} open leads need a next action or date. '+('Launch budget exceeded.' if spend>cfg['launch_budget'] else '')+'</p><div class="actions"><a class="btn" href="/growth/leads/new">Add lead</a><a class="btn" href="/availability">Preview inquiry page</a></div><h2>Due and overdue work</h2>'+table(['Due','Task','Lead','Action'],rows)+'<p>Follow-ups appear here and in Tasks. No marketing emails or texts are sent automatically.</p>')

    def lead_fields(r, public=False):
        s=field('first_name',r.get('first_name',''),required=True)+field('last_name',r.get('last_name',''),required=True)+field('service_address',r.get('service_address',''),required=True)+field('city',r.get('city',''))+field('zip',r.get('zip',''),required=True)+field('email',r.get('email',''),'email')+field('phone',r.get('phone',''))+select('preferred_contact',[(x,x) for x in ['Phone','Email','Text']],r.get('preferred_contact','Phone'))+field('source',r.get('source','Direct'),label='How did you hear about us?')+area('problem',r.get('problem',''),label='What internet problem do you want to solve?')
        if public: return s
        s+=select('rural',[(x,x) for x in ['Unknown','Yes','No']],r.get('rural','Unknown'))+field('current_provider',r.get('current_provider',''))+field('current_price',str(r.get('current_price',0)/100),'number')+area('needs',r.get('needs',''))+field('timing',r.get('timing',''))+area('notes',r.get('notes',''))
        with m.conn() as c:
            partners=c.execute('SELECT id,name FROM growth_partners ORDER BY name').fetchall(); users=c.execute('SELECT id,name FROM users WHERE active=1').fetchall()
        return s+select('partner_id',[('', 'None')]+[(p['id'],p['name']) for p in partners],r.get('partner_id',''))+select('owner_id',[('','Unassigned')]+[(u['id'],u['name']) for u in users],r.get('owner_id',''))
    def parse_lead(f,public=False):
        d={k:text(f,k,limit,req) for k,limit,req in [('first_name',100,True),('last_name',100,True),('service_address',300,True),('city',100,False),('zip',10,True),('email',254,False),('phone',40,False),('source',100,False),('problem',2000,False)]}
        if not re.fullmatch(r'\d{5}(?:-\d{4})?',d['zip']): raise HTTPException(400,'Enter a five-digit ZIP or ZIP+4.')
        if not d['email'] and not d['phone']: raise HTTPException(400,'Provide a phone number or email.')
        if d['email'] and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',d['email']): raise HTTPException(400,'Check the email address.')
        d['preferred_contact']=text(f,'preferred_contact',10) or 'Phone'
        if d['preferred_contact'] not in ('Phone','Email','Text'): raise HTTPException(400,'Choose a contact method.')
        if (d['preferred_contact']=='Email' and not d['email']) or (d['preferred_contact']!='Email' and not d['phone']): raise HTTPException(400,'Provide contact details for your preferred method.')
        d['source']=d['source'] or ('Website' if public else 'Direct')
        if not public:
            d.update({k:text(f,k,2000) for k in ['current_provider','needs','timing','notes']})
            d['current_price']=cents(f.get('current_price','0'))
            d['rural']=text(f,'rural',10) or 'Unknown'
            if d['rural'] not in ('Unknown','Yes','No'): raise HTTPException(400,'Invalid rural selection.')
            with m.conn() as c:
                for key,tbl in [('partner_id','growth_partners'),('owner_id','users')]:
                    v=text(f,key,20); d[key]=None
                    if v:
                        if not v.isdigit() or not c.execute(f'SELECT 1 FROM {tbl} WHERE id=?',(v,)).fetchone(): raise HTTPException(400,'Invalid partner or owner.')
                        d[key]=int(v)
        return d
    def add_lead(c,d,request):
        duplicate=c.execute("SELECT id FROM growth_leads WHERE lower(service_address)=lower(?) AND zip=? AND ((email!='' AND lower(email)=lower(?)) OR (phone!='' AND phone=?))",(d['service_address'],d['zip'],d['email'],d['phone'])).fetchone()
        if duplicate: return duplicate['id'],False
        d.update(next_action='Respond and check service address',next_date=today())
        cur=c.execute(f'INSERT INTO growth_leads({",".join(d)}) VALUES ({",".join("?" for _ in d)})',tuple(d.values())); lid=cur.lastrowid
        task(c,'Respond to inquiry and check address',today(),lid,key=f'new:{lid}'); log(c,request,lid,'Inquiry created',d['source'])
        return lid,True

    @app.get('/growth/leads',response_class=HTMLResponse)
    def leads(request:Request,q:str='',stage:str='',zip:str='',source:str=''):
        m.require_staff(request); sync()
        with m.conn() as c:
            rows=c.execute("SELECT * FROM growth_leads WHERE (?='' OR stage=?) AND (?='' OR substr(zip,1,5)=?) AND (?='' OR source=?) AND (first_name||' '||last_name||' '||service_address||' '||email LIKE ?) ORDER BY id DESC LIMIT 500",(stage,stage,zip,zip,source,source,'%'+q+'%')).fetchall()
        filters='<form method="get">'+field('q',q,label='Search name, address or email')+select('stage',[('','All stages')]+[(x,x) for x in STAGES],stage)+select('zip',[('','All ZIP codes')]+[(z,f'{z} — {n}') for z,n in ZIPS.items()],zip)+field('source',source)+'<button class="btn">Filter</button></form>'
        body=table(['Name','Address','Stage / eligibility','Source','Next action'],[[f'<a href="/growth/leads/{r["id"]}">{esc(r["first_name"])} {esc(r["last_name"])}</a>',esc(r['service_address'])+'<br>'+esc(r['zip']),esc(r['stage'])+' / '+esc(r['eligibility']),esc(r['source']),esc(r['next_date'])+' '+esc(r['next_action'])] for r in rows])
        return shell(request,'Lead pipeline','<a class="btn" href="/growth/leads/new">Add lead</a> <a href="/growth/export.csv">Export all leads</a>'+filters+body+'<p>Showing up to 500 matching leads. CSV includes all leads.</p>')

    @app.get('/growth/leads/new',response_class=HTMLResponse)
    def new_lead(request:Request):
        m.require_staff(request)
        return shell(request,'Add lead',form(request,'/growth/leads/new',lead_fields({})+select('contact_consent',[('0','Not recorded'),('1','Prospect agreed to contact about this inquiry')],'0'),'Create lead'))
    @app.post('/growth/leads/new')
    async def save_lead(request:Request):
        f=await checked(request); d=parse_lead(f); d['contact_consent']=int(f.get('contact_consent')=='1')
        with m.conn() as c:
            c.execute('BEGIN IMMEDIATE'); lid,_=add_lead(c,d,request)
        return RedirectResponse(f'/growth/leads/{lid}',303)

    @app.get('/growth/leads/{lid}',response_class=HTMLResponse)
    def detail(request:Request,lid:int):
        m.require_staff(request); sync()
        with m.conn() as c:
            r=record(c,lid); quotes=c.execute('SELECT * FROM growth_quotes WHERE lead_id=? ORDER BY id DESC',(lid,)).fetchall(); events=c.execute('SELECT * FROM growth_events WHERE lead_id=? ORDER BY id DESC LIMIT 100',(lid,)).fetchall()
        cfg=settings()
        body=f'<p><b>{esc(r["first_name"])} {esc(r["last_name"])}</b> · {esc(r["stage"])} · '+('Target ZIP' if r['zip'][:5] in ZIPS else 'Outside target ZIPs')+'</p>'
        if r['do_not_contact']: body+='<div class="notice">Do not contact. Automated follow-up tasks are cancelled.</div>'
        if r['customer_id']: body+=f'<p><a href="/customers/{r["customer_id"]}">Customer record</a> · <a href="/invoices/{r["invoice_id"]}">Initial invoice / Stripe payment</a></p>'
        body+='<details><summary>Edit contact details and assignment</summary>'+form(request,f'/growth/leads/{lid}/edit',lead_fields(r))+'</details>'
        states=[x for x in STAGES if x not in ('Paid','Activated')]
        body+='<h2>Qualification and next action</h2>'+form(request,f'/growth/leads/{lid}/status',select('stage',[(x,x) for x in states]+([(r['stage'],r['stage'])] if r['stage'] in ('Paid','Activated') else []),r['stage'])+select('eligibility',[(x,x) for x in ['Unchecked','Eligible','Unavailable']],r['eligibility'])+area('eligibility_notes',r['eligibility_notes'],label='Platform check evidence / date / reference')+field('next_action',r['next_action'])+field('next_date',r['next_date'],'date')+area('lost_reason',r['lost_reason'])+select('contact_consent',[('0','Not recorded'),('1','Agreed to inquiry follow-up')],r['contact_consent'])+select('do_not_contact',[('0','May contact with permission'),('1','Do not contact')],r['do_not_contact']))
        body+='<h2>Activity note</h2>'+form(request,f'/growth/leads/{lid}/note',area('note'),'Record note')
        body+='<h2>Quote</h2><p>Save a quote, open its printable view, and share it yourself. Record when you actually send it to schedule day-2 and day-7 follow-ups.</p>'
        if not r['customer_id']:
            qfields=''.join(field(k,str(cfg[k]/100),'number') for k in ['service','lease','activation','wholesale_service','wholesale_modem','other_monthly'])+field('contract_months','36','number')+area('terms','',label='Required: performance qualifications, setup timing, agreement/cancellation terms, and any additional charges')
            body+=form(request,f'/growth/leads/{lid}/quote',qfields,'Save quote')
        for q in quotes:
            body+=f'<div class="card section"><a href="/growth/quotes/{q["id"]}">Quote #{q["id"]} — {dollars(q["service"]+q["lease"])} / month</a>'
            if not r['customer_id']: body+=form(request,f'/growth/quotes/{q["id"]}/sent','','Record sent & schedule follow-ups')
            body+='</div>'
        if not r['customer_id']:
            body+='<h2>Convert accepted quote</h2><p>Creates one customer and initial invoice. No service plan is enabled until payment and activation are verified. Existing customers can be linked using their numeric CRM ID; they must have no subscription.</p>'+form(request,f'/growth/leads/{lid}/convert',select('quote_id',[(q['id'],f'Quote #{q["id"]}') for q in quotes])+field('existing_customer_id','',label='Existing CRM customer ID (optional)')+area('agreement_evidence',label='Agreement acceptance evidence / document reference'),'Create customer and initial invoice')
        elif not r['activated_at']:
            body+='<h2>Confirm physical activation</h2><p>Requires a fully paid initial invoice, an eligible address, agreement evidence, assigned modem and SIM, and your actual service test. This does not send a carrier activation command.</p>'+form(request,f'/growth/leads/{lid}/activate',area('test_results',label='Record actual modem placement, service test and customer outcome'),'Confirm activation & start recurring billing')
        body+='<h2>History</h2>'+table(['When','Staff','Action','Details'],[[esc(e[k]) for k in ['created_at','actor','action','details']] for e in events])
        return shell(request,f'Lead #{lid}',body)

    @app.post('/growth/leads/{lid}/edit')
    async def edit_lead(request:Request,lid:int):
        f=await checked(request); d=parse_lead(f)
        with m.conn() as c:
            record(c,lid); c.execute(f'UPDATE growth_leads SET {",".join(k+"=?" for k in d)},updated_at=CURRENT_TIMESTAMP WHERE id=?',(*d.values(),lid)); log(c,request,lid,'Contact updated','Customer billing contact, if linked, is edited separately.')
        return RedirectResponse(f'/growth/leads/{lid}',303)
    @app.post('/growth/leads/{lid}/status')
    async def status(request:Request,lid:int):
        f=await checked(request)
        with m.conn() as c:
            r=record(c,lid); stage=text(f,'stage',30); eligible=text(f,'eligibility',20); due=day(text(f,'next_date',10)); action=text(f,'next_action',300); lost=text(f,'lost_reason',2000); evidence=text(f,'eligibility_notes',2000)
            dnc=int(f.get('do_not_contact')=='1'); consent=int(f.get('contact_consent')=='1')
            if stage not in STAGES or eligible not in ['Unchecked','Eligible','Unavailable']: raise HTTPException(400,'Invalid stage or eligibility.')
            if stage in ['Paid','Activated'] and stage!=r['stage']: raise HTTPException(400,'Payment and activation are verified through their dedicated workflows.')
            if r['activated_at'] and stage!='Activated': raise HTTPException(400,'Manage cancellation on the linked customer record.')
            if r['customer_id'] and stage!=r['stage']: raise HTTPException(400,'Converted leads use verified payment and activation stages; manage customer cancellation on the customer record.')
            if stage in ('Address checked','Quote sent','Decision pending') and eligible=='Unchecked': raise HTTPException(400,'Record the address check before advancing this lead.')
            if stage=='Quote sent' and r['stage']!='Quote sent': raise HTTPException(400,'Use Record sent on a saved quote to schedule follow-ups.')
            if stage in CLOSED and not lost: raise HTTPException(400,'Record the reason for closing the lead.')
            if eligible!='Unchecked' and not evidence: raise HTTPException(400,'Record address-check evidence.')
            if stage not in (*CLOSED,'Activated') and not dnc and (not action or not due): raise HTTPException(400,'Open leads need a next action and date.')
            c.execute('UPDATE growth_leads SET stage=?,eligibility=?,eligibility_notes=?,next_action=?,next_date=?,lost_reason=?,do_not_contact=?,contact_consent=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(stage,eligible,evidence,action,due,lost,dnc,consent,lid))
            if eligible!='Unchecked': c.execute("UPDATE growth_tasks SET status='Done',completed_at=CURRENT_TIMESTAMP WHERE unique_key=? AND status='Open'",(f'new:{lid}',))
            if dnc or stage in CLOSED:
                c.execute("UPDATE growth_tasks SET status='Cancelled' WHERE lead_id=? AND status='Open'",(lid,))
            elif due and action:
                c.execute("UPDATE growth_tasks SET status='Cancelled' WHERE lead_id=? AND unique_key=? AND status='Open'",(lid,f'next:{lid}'))
                c.execute("INSERT INTO growth_tasks(title,due_date,lead_id,unique_key) VALUES (?,?,?,?) ON CONFLICT(unique_key) DO UPDATE SET title=excluded.title,due_date=excluded.due_date,status='Open',completed_at=NULL",(action,due,lid,f'next:{lid}'))
            log(c,request,lid,'Qualification updated',f'{stage}; {eligible}; next={due}; do_not_contact={dnc}')
        return RedirectResponse(f'/growth/leads/{lid}',303)
    @app.post('/growth/leads/{lid}/note')
    async def note(request:Request,lid:int):
        f=await checked(request); val=text(f,'note',10000,True)
        with m.conn() as c: record(c,lid); log(c,request,lid,'Note',val)
        return RedirectResponse(f'/growth/leads/{lid}',303)

    @app.post('/growth/leads/{lid}/quote')
    async def quote(request:Request,lid:int):
        f=await checked(request); amounts={k:cents(f.get(k,'')) for k in ['service','lease','activation','wholesale_service','wholesale_modem','other_monthly']}; terms=text(f,'terms',10000,True)
        try: months=int(f.get('contract_months',''))
        except ValueError: raise HTTPException(400,'Contract months must be a whole number.')
        if not 1<=months<=120 or amounts['service']+amounts['lease']<=0: raise HTTPException(400,'Check contract length and monthly price.')
        with m.conn() as c:
            r=record(c,lid)
            if r['customer_id']: raise HTTPException(409,'Converted quotes are immutable. Use customer billing for changes.')
            if r['eligibility']!='Eligible': raise HTTPException(400,'Verify address eligibility before quoting.')
            d=dict(lead_id=lid,**amounts,contract_months=months,terms=terms)
            qid=c.execute(f'INSERT INTO growth_quotes({",".join(d)}) VALUES ({",".join("?" for _ in d)})',tuple(d.values())).lastrowid
            log(c,request,lid,'Quote saved',f'Quote #{qid}')
        return RedirectResponse(f'/growth/quotes/{qid}',303)
    @app.get('/growth/quotes/{qid}',response_class=HTMLResponse)
    def quote_view(request:Request,qid:int):
        m.require_staff(request)
        with m.conn() as c:
            q=c.execute('SELECT * FROM growth_quotes WHERE id=?',(qid,)).fetchone()
            if not q: raise HTTPException(404)
            r=record(c,q['lead_id'])
        monthly=q['service']+q['lease']
        body=f'<img src="/assets/entire-wireless-logo.png" alt="Entire Wireless" style="max-width:180px"><h1>Entire Wireless — Service Quote #{qid}</h1><p>{esc(r["first_name"])} {esc(r["last_name"])}<br>{esc(r["service_address"])}<br>{esc(r["city"])} IL {esc(r["zip"])}</p>'+table(['Charge','Amount'],[['Monthly service',dollars(q['service'])],['Monthly modem lease',dollars(q['lease'])],['Total monthly',dollars(monthly)],['One-time activation',dollars(q['activation'])],['First full month + activation',dollars(monthly+q['activation'])]])+f'<p>Agreement: {q["contract_months"]} months. Other charges or applicable taxes, if any, are described in the terms below.</p><div style="white-space:pre-wrap">{esc(q["terms"])}</div><p>{esc(m.COMPANY_PHONE)} · {esc(m.SUPPORT_EMAIL)} · {esc(m.COMPANY_SITE)}</p><p class="no-print">Use your browser’s Print / Save as PDF to share this quote. <a href="/growth/leads/{r["id"]}">Return to lead</a></p>'
        return HTMLResponse('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Service quote</title><style>'+m.CSS+'body{padding:30px;background:white;max-width:900px;margin:auto}@media print{.no-print{display:none}}</style></head><body>'+body+'</body></html>')
    @app.post('/growth/quotes/{qid}/sent')
    async def quote_sent(request:Request,qid:int):
        await checked(request)
        with m.conn() as c:
            q=c.execute('SELECT * FROM growth_quotes WHERE id=?',(qid,)).fetchone()
            if not q: raise HTTPException(404)
            r=record(c,q['lead_id'])
            if r['customer_id'] or r['do_not_contact'] or not r['contact_consent'] or r['stage'] in CLOSED: raise HTTPException(409,'Check contact permission and lead status first.')
            if c.execute('SELECT 1 FROM growth_tasks WHERE unique_key=?',(f'quote:{qid}:2',)).fetchone(): return RedirectResponse(f'/growth/leads/{r["id"]}',303)
            sent=m.business_now().date()
            for days in [2,7]: task(c,f'Follow up on quote #{qid}',(sent+timedelta(days=days)).isoformat(),r['id'],key=f'quote:{qid}:{days}')
            c.execute("UPDATE growth_leads SET stage='Quote sent',quote_id=?,next_action='Follow up on quote',next_date=? WHERE id=?",(qid,(sent+timedelta(days=2)).isoformat(),r['id']))
            log(c,request,r['id'],'Quote recorded as sent',f'Quote #{qid}; shared by staff, not emailed by CRM.')
        return RedirectResponse(f'/growth/leads/{r["id"]}',303)

    @app.post('/growth/leads/{lid}/convert')
    async def convert(request:Request,lid:int):
        f=await checked(request); agreement=text(f,'agreement_evidence',10000,True); qid=text(f,'quote_id',20,True); existing=text(f,'existing_customer_id',20)
        with m.conn() as c:
            c.execute('BEGIN IMMEDIATE'); r=record(c,lid)
            if r['customer_id']: return RedirectResponse(f'/growth/leads/{lid}',303)
            if r['eligibility']!='Eligible' or r['do_not_contact'] or not r['contact_consent'] or r['stage'] in CLOSED: raise HTTPException(409,'Confirm eligibility, contact permission and active lead status.')
            q=c.execute('SELECT * FROM growth_quotes WHERE id=? AND lead_id=?',(qid,lid)).fetchone()
            if not q: raise HTTPException(400,'Select a quote belonging to this lead.')
            if existing:
                cust=c.execute('SELECT * FROM customers WHERE id=?',(existing,)).fetchone()
                if not cust: raise HTTPException(400,'Existing customer not found.')
                if c.execute('SELECT 1 FROM subscriptions WHERE customer_id=?',(existing,)).fetchone() or c.execute('SELECT 1 FROM growth_leads WHERE customer_id=?',(existing,)).fetchone(): raise HTTPException(409,'Customer already has a subscription or linked lead.')
                if cust['service_address'].strip().lower()!=r['service_address'].strip().lower() or cust['zip']!=r['zip']: raise HTTPException(409,'Customer address must match the lead before linking.')
                cid=cust['id']
            else:
                if c.execute("SELECT 1 FROM customers WHERE lower(service_address)=lower(?) AND zip=? AND (lower(email)=lower(?) OR phone=?)",(r['service_address'],r['zip'],r['email'] or '__none__',r['phone'] or '__none__')).fetchone(): raise HTTPException(409,'Possible existing customer. Review Customers and enter its CRM ID to link.')
                cid=c.execute("INSERT INTO customers(account_no,first_name,last_name,email,phone,service_address,city,state,zip,status,service_status,billing_hold_until_first_payment,contract_months,notes) VALUES (?,?,?,?,?,?,?,'IL',?,'Active','Pending activation',1,?,?)",(m.generate_account_number(c),r['first_name'],r['last_name'],r['email'],r['phone'],r['service_address'],r['city'],r['zip'],q['contract_months'],f'Converted from Sales lead #{lid}.')).lastrowid
            now=m.business_now().date(); seq=c.execute('SELECT COALESCE(MAX(id),0)+1 FROM invoices').fetchone()[0]
            iid=c.execute('INSERT INTO invoices(invoice_no,customer_id,issue_date,due_date,subtotal) VALUES (?,?,?,?,?)',(f'GROW-{now:%Y%m}-{seq:05d}',cid,now.isoformat(),now.isoformat(),(q['service']+q['lease']+q['activation'])/100)).lastrowid
            for label,k in [('First month Internet service','service'),('First month modem lease','lease'),('One-time activation','activation')]:
                c.execute('INSERT INTO invoice_items(invoice_id,description,qty,unit_price,amount) VALUES (?,?,1,?,?)',(iid,label,q[k]/100,q[k]/100))
            c.execute("UPDATE customers SET initial_invoice_id=?,billing_hold_until_first_payment=1,service_status='Pending activation' WHERE id=?",(iid,cid))
            c.execute("UPDATE growth_leads SET customer_id=?,invoice_id=?,quote_id=?,agreement_evidence=?,stage='Decision pending',next_action='Collect initial invoice payment',next_date=? WHERE id=?",(cid,iid,q['id'],agreement,today(),lid))
            c.execute("UPDATE growth_tasks SET status='Cancelled' WHERE lead_id=? AND status='Open'",(lid,))
            task(c,'Collect initial invoice payment',today(),lid,key=f'collect:{lid}'); log(c,request,lid,'Converted',f'Customer #{cid}, invoice #{iid}; no recurring subscription yet.')
        m.audit(request,'CREATE','growth_conversion',lid,f'customer={cid}; invoice={iid}')
        return RedirectResponse(f'/growth/leads/{lid}',303)

    @app.post('/growth/leads/{lid}/activate')
    async def activate(request:Request,lid:int):
        f=await checked(request); tests=text(f,'test_results',10000,True); sync()
        with m.conn() as c:
            c.execute('BEGIN IMMEDIATE'); r=record(c,lid)
            if r['activated_at']: return RedirectResponse(f'/growth/leads/{lid}',303)
            inv=c.execute('SELECT * FROM invoices WHERE id=?',(r['invoice_id'],)).fetchone()
            cust=c.execute('SELECT * FROM customers WHERE id=?',(r['customer_id'],)).fetchone()
            if not cust or cust['status']!='Active' or not inv or inv['status']=='Void' or inv['amount_paid']<inv['subtotal']-.005 or r['eligibility']!='Eligible' or not r['agreement_evidence']: raise HTTPException(409,'A fully paid initial invoice, active customer, eligible address and agreement evidence are required.')
            for tbl in ('modems','sims'):
                if not c.execute(f'SELECT 1 FROM {tbl} WHERE customer_id=?',(r['customer_id'],)).fetchone(): raise HTTPException(409,'Assign a modem and SIM on the customer page first.')
            if c.execute('SELECT 1 FROM subscriptions WHERE customer_id=?',(r['customer_id'],)).fetchone(): raise HTTPException(409,'Customer already has a subscription. Review billing before activation to avoid duplicate billing.')
            q=c.execute('SELECT * FROM growth_quotes WHERE id=?',(r['quote_id'],)).fetchone()
            plan=c.execute('SELECT id FROM plans WHERE active=1 AND abs(monthly_price-?)<0.001 AND abs(modem_lease-?)<0.001',(q['service']/100,q['lease']/100)).fetchone()
            if not plan: raise HTTPException(409,'Create an active Service Plan matching the accepted quote before activation.')
            now=m.business_now().date()
            c.execute("INSERT INTO subscriptions(customer_id,plan_id,start_date,status) VALUES (?,?,?,'Active')",(r['customer_id'],plan['id'],now.isoformat()))
            c.execute("UPDATE customers SET service_status='Active',billing_hold_until_first_payment=0,billing_started_at=?,contract_start=?,contract_months=?,billing_day=? WHERE id=?",(now.isoformat(),now.isoformat(),q['contract_months'],min(now.day,28),r['customer_id']))
            c.execute("UPDATE growth_leads SET stage='Activated',activated_at=?,test_results=?,next_action='48-hour service check',next_date=? WHERE id=?",(today(),tests,(now+timedelta(days=2)).isoformat(),lid))
            c.execute("UPDATE growth_tasks SET status='Cancelled' WHERE lead_id=? AND status='Open'",(lid,))
            if not r['do_not_contact']:
                for days,title in [(2,'48-hour service check'),(7,'One-week service check; ask for honest review and introduction if satisfied')]: task(c,title,(now+timedelta(days=days)).isoformat(),lid,key=f'activation:{lid}:{days}')
            log(c,request,lid,'Activated',tests)
        return RedirectResponse(f'/growth/leads/{lid}',303)

    @app.get('/growth/tasks',response_class=HTMLResponse)
    def tasks(request:Request,status:str='Open',owner_id:str=''):
        m.require_staff(request); sync()
        with m.conn() as c:
            rows=c.execute("SELECT t.*,u.name owner FROM growth_tasks t LEFT JOIN users u ON u.id=t.owner_id WHERE (?='' OR t.status=?) AND (?='' OR CAST(t.owner_id AS TEXT)=?) ORDER BY t.due_date,t.id LIMIT 500",(status,status,owner_id,owner_id)).fetchall()
            users=c.execute('SELECT id,name FROM users WHERE active=1').fetchall()
        options=[('','Unassigned')]+[(u['id'],u['name']) for u in users]
        body='<form method="get">'+select('status',[(x,x or 'All') for x in ['Open','Done','Cancelled','']],status)+select('owner_id',[('','All owners')]+options[1:],owner_id)+'<button class="btn">Filter</button></form>'
        body+=table(['Due','Task / linked record','Owner','Status','Action'],[[esc(r['due_date']),esc(r['title'])+(f' · <a href="/growth/leads/{r["lead_id"]}">Lead #{r["lead_id"]}</a>' if r['lead_id'] else '')+(f' · Partner #{r["partner_id"]}' if r['partner_id'] else ''),esc(r['owner']),esc(r['status']),form(request,f'/growth/tasks/{r["id"]}/complete',area('notes',label='Outcome'),'Complete')+form(request,f'/growth/tasks/{r["id"]}/reschedule',field('due_date',r['due_date'],'date',True)+select('owner_id',options,r['owner_id']),'Reschedule / assign') if r['status']=='Open' else esc(r['notes'])] for r in rows])
        body+='<h2>Add task</h2>'+form(request,'/growth/tasks',field('title',required=True)+field('due_date',today(),'date',True)+field('lead_id','',label='Lead ID (optional)')+select('owner_id',options),'Add task')
        return shell(request,'Tasks & follow-ups',body)
    @app.post('/growth/tasks')
    async def task_add(request:Request):
        f=await checked(request); title=text(f,'title',300,True); due=day(text(f,'due_date',10),True); lid=text(f,'lead_id',20); owner=text(f,'owner_id',20)
        with m.conn() as c:
            if lid:
                r=record(c,lid)
                if r['do_not_contact'] or r['stage'] in CLOSED: raise HTTPException(409,'This lead is closed or marked do not contact.')
            if owner and not c.execute('SELECT 1 FROM users WHERE id=? AND active=1',(owner,)).fetchone(): raise HTTPException(400,'Invalid owner.')
            c.execute('INSERT INTO growth_tasks(title,due_date,lead_id,owner_id) VALUES (?,?,?,?)',(title,due,lid or None,owner or None))
        return RedirectResponse('/growth/tasks',303)
    @app.post('/growth/tasks/{tid}/complete')
    async def complete(request:Request,tid:int):
        f=await checked(request); notes=text(f,'notes',2000)
        with m.conn() as c:
            t=c.execute('SELECT * FROM growth_tasks WHERE id=?',(tid,)).fetchone()
            if not t: raise HTTPException(404)
            c.execute("UPDATE growth_tasks SET status='Done',completed_at=CURRENT_TIMESTAMP,notes=? WHERE id=? AND status='Open'",(notes,tid))
            if t['lead_id']:
                log(c,request,t['lead_id'],'Task completed',t['title']+' '+notes)
                nxt=c.execute("SELECT title,due_date FROM growth_tasks WHERE lead_id=? AND status='Open' ORDER BY due_date,id LIMIT 1",(t['lead_id'],)).fetchone()
                c.execute('UPDATE growth_leads SET next_action=?,next_date=? WHERE id=?',(nxt['title'] if nxt else '',nxt['due_date'] if nxt else '',t['lead_id']))
        return RedirectResponse('/growth/tasks',303)
    @app.post('/growth/tasks/{tid}/reschedule')
    async def reschedule(request:Request,tid:int):
        f=await checked(request); due=day(text(f,'due_date',10),True); owner=text(f,'owner_id',20)
        with m.conn() as c:
            if owner and not c.execute('SELECT 1 FROM users WHERE id=? AND active=1',(owner,)).fetchone(): raise HTTPException(400,'Invalid owner.')
            r=c.execute('SELECT * FROM growth_tasks WHERE id=?',(tid,)).fetchone()
            if not r: raise HTTPException(404)
            c.execute('UPDATE growth_tasks SET due_date=?,owner_id=? WHERE id=?',(due,owner or None,tid))
            if r['lead_id']:
                nxt=c.execute("SELECT title,due_date FROM growth_tasks WHERE lead_id=? AND status='Open' ORDER BY due_date,id LIMIT 1",(r['lead_id'],)).fetchone()
                if nxt: c.execute('UPDATE growth_leads SET next_action=?,next_date=? WHERE id=?',(nxt['title'],nxt['due_date'],r['lead_id']))
                log(c,request,r['lead_id'],'Task rescheduled',f'{r["title"]}; due={due}')
        return RedirectResponse('/growth/tasks',303)

    @app.get('/growth/partners',response_class=HTMLResponse)
    def partners(request:Request):
        m.require_staff(request)
        with m.conn() as c: rows=c.execute('SELECT p.*,COUNT(l.id) leads FROM growth_partners p LEFT JOIN growth_leads l ON l.partner_id=p.id GROUP BY p.id ORDER BY p.name').fetchall()
        body=table(['Partner','Contact','Permission','Leads','Update'],[[f'#{r["id"]} '+esc(r['name'])+'<br>'+esc(r['kind']),esc(r['contact'])+'<br>'+esc(r['email'])+'<br>'+esc(r['phone']),esc(r['permission']),r['leads'],form(request,f'/growth/partners/{r["id"]}',select('permission',[(x,x) for x in ['Not asked','Cards allowed','Introductions agreed','Declined']],r['permission'])+field('next_date',r['next_date'],'date')+area('notes',r['notes']))] for r in rows])
        body+='<h2>Add prospective partner</h2>'+form(request,'/growth/partners',field('name',required=True)+select('kind',[(x,x) for x in ['Farm store','Computer repair','Real estate','Electrician / installer','Community organization','Other']])+field('contact')+field('email',kind='email')+field('phone')+field('zip')+field('next_date',today(),'date')+area('notes'),'Add partner')
        return shell(request,'Local partners',body)
    @app.post('/growth/partners')
    async def partner_add(request:Request):
        f=await checked(request); d={k:text(f,k,300,k=='name') for k in ['name','kind','contact','email','phone','zip']}; d.update(notes=text(f,'notes',2000),next_date=day(text(f,'next_date',10)))
        with m.conn() as c:
            pid=c.execute(f'INSERT INTO growth_partners({",".join(d)}) VALUES ({",".join("?" for _ in d)})',tuple(d.values())).lastrowid
            if d['next_date']: task(c,'Contact prospective partner: '+d['name'],d['next_date'],partner=pid,key=f'partner:{pid}')
        return RedirectResponse('/growth/partners',303)
    @app.post('/growth/partners/{pid}')
    async def partner_update(request:Request,pid:int):
        f=await checked(request); permission=text(f,'permission',30); due=day(text(f,'next_date',10)); notes=text(f,'notes',2000)
        if permission not in ['Not asked','Cards allowed','Introductions agreed','Declined']: raise HTTPException(400,'Invalid permission.')
        with m.conn() as c:
            r=c.execute('SELECT * FROM growth_partners WHERE id=?',(pid,)).fetchone()
            if not r: raise HTTPException(404)
            c.execute('UPDATE growth_partners SET permission=?,next_date=?,notes=? WHERE id=?',(permission,due,notes,pid))
            c.execute("UPDATE growth_tasks SET status='Cancelled' WHERE partner_id=? AND status='Open'",(pid,))
            if due and permission!='Declined':
                c.execute("INSERT INTO growth_tasks(title,due_date,partner_id,unique_key) VALUES (?,?,?,?) ON CONFLICT(unique_key) DO UPDATE SET title=excluded.title,due_date=excluded.due_date,status='Open',completed_at=NULL",('Follow up with '+r['name'],due,pid,f'partner:{pid}'))
        return RedirectResponse('/growth/partners',303)

    @app.get('/growth/areas',response_class=HTMLResponse)
    def areas(request:Request):
        m.require_staff(request)
        with m.conn() as c: rows=c.execute('SELECT * FROM growth_areas ORDER BY id DESC LIMIT 300').fetchall()
        body='<p>Use <a href="https://broadbandmap.fcc.gov/" target="_blank" rel="noopener">FCC availability information</a> and your wholesale platform to research addresses. These records do not create leads or assert coverage automatically.</p>'+table(['ZIP','Address','Existing options','Platform result','Evidence / test','Checked'],[[esc(r[k]) for k in ['zip','address','existing_options','eligibility','test_notes','checked_on']] for r in rows])
        body+='<h2>Record an address check</h2>'+form(request,'/growth/areas',select('zip',[(z,f'{z} — {n}') for z,n in ZIPS.items()])+field('address',required=True)+area('existing_options')+select('eligibility',[(x,x) for x in ['Unchecked','Eligible','Unavailable']])+area('test_notes',label='Evidence, reference and any actual test results')+field('checked_on',today(),'date',True))
        return shell(request,'Rural coverage research',body)
    @app.post('/growth/areas')
    async def area_add(request:Request):
        f=await checked(request); z=text(f,'zip',5); eligibility=text(f,'eligibility',20)
        if z not in ZIPS or eligibility not in ['Unchecked','Eligible','Unavailable']: raise HTTPException(400,'Check ZIP and eligibility.')
        with m.conn() as c: c.execute('INSERT INTO growth_areas(zip,address,existing_options,eligibility,test_notes,checked_on) VALUES (?,?,?,?,?,?)',(z,text(f,'address',300,True),text(f,'existing_options',2000),eligibility,text(f,'test_notes',2000),day(text(f,'checked_on',10),True)))
        return RedirectResponse('/growth/areas',303)

    @app.get('/growth/reports',response_class=HTMLResponse)
    def reports(request:Request,start:str='',end:str=''):
        m.require_staff(request); sync(); start=day(start) or '0001-01-01'; end=day(end) or today()
        if start>end: raise HTTPException(400,'Start must precede end.')
        cfg=settings()
        with m.conn() as c:
            leads=[dict(r) for r in c.execute('SELECT * FROM growth_leads')]
            quotes={r['id']:dict(r) for r in c.execute('SELECT * FROM growth_quotes')}
            expenses=c.execute('SELECT * FROM growth_expenses WHERE spent_on BETWEEN ? AND ? ORDER BY spent_on DESC',(start,end)).fetchall()
            lost=c.execute("SELECT lost_reason,COUNT(*) n FROM growth_leads WHERE stage IN ('Lost','Unavailable') AND substr(created_at,1,10) BETWEEN ? AND ? GROUP BY lost_reason",(start,end)).fetchall()
        channels=sorted({l['source'] for l in leads}|{e['source'] for e in expenses}); rows=[]
        for source in channels:
            ls=[l for l in leads if l['source']==source]; spend=sum(e['amount'] for e in expenses if e['source']==source)
            inquiries=sum(start<=l['created_at'][:10]<=end for l in ls); activations=sum(bool(l['activated_at']) and start<=l['activated_at']<=end for l in ls)
            eligible=sum(start<=l['created_at'][:10]<=end and l['eligibility']=='Eligible' for l in ls)
            rows.append([esc(source),inquiries,eligible,activations,dollars(spend),dollars(round(spend/activations)) if activations else '—'])
        active=[l for l in leads if l['activated_at'] and not l['cancelled_at']]
        revenue=sum(quotes[l['quote_id']]['service']+quotes[l['quote_id']]['lease'] for l in active)
        costs=sum(quotes[l['quote_id']]['wholesale_service']+quotes[l['quote_id']]['wholesale_modem']+quotes[l['quote_id']]['other_monthly'] for l in active)
        cash=sum(e['amount'] for e in expenses); minutes=sum(e['minutes'] for e in expenses)
        cancelled=sum(bool(l['cancelled_at']) and start<=l['cancelled_at']<=end for l in leads)
        body='<form method="get">'+field('start',start if start!='0001-01-01' else '','date')+field('end',end,'date')+'<button class="btn">Apply dates</button></form>'
        body+=f'<div class="notice">Current Sales-linked active accounts: {len(active)}. Quoted monthly revenue: {dollars(revenue)}. Estimated monthly remainder: {dollars(revenue-costs)}; after configured overhead: {dollars(revenue-costs-cfg["overhead"])}. This is a planning estimate using accepted quote costs, not accounting profit, cash collections or a whole-CRM billing report.</div>'
        body+=f'<p>Selected dates: outreach spending {dollars(cash)}, logged time {minutes} minutes, cancellations {cancelled}. Blank acquisition costs mean no activations.</p>'+table(['Source','Inquiries created','Currently eligible from those inquiries','Activations in period','Spending in period','Period spending / activation'],rows)+'<p>Period spending per activation is a directional measure, not cohort payback: spending and activations may concern different leads. Lifetime reporting uses all recorded dates. Consistent source names are required.</p>'
        body+='<h2>Target ZIP performance</h2>'+table(['ZIP','Total inquiries','Activated ever','Currently active'],[[esc(z),sum(l['zip'][:5]==z for l in leads),sum(l['zip'][:5]==z and bool(l['activated_at']) for l in leads),sum(l['zip'][:5]==z for l in active)] for z in ZIPS])
        body+='<h2>Reasons lost / unavailable</h2>'+table(['Reason','Count'],[[esc(r['lost_reason']),r['n']] for r in lost])
        body+='<h2>Spending log</h2>'+table(['Date','Source','Amount','Minutes','Notes'],[[esc(e['spent_on']),esc(e['source']),dollars(e['amount']),e['minutes'],esc(e['notes'])] for e in expenses])
        body+=form(request,'/growth/expenses',field('spent_on',today(),'date',True)+field('source',required=True)+field('amount','0','number',True)+field('minutes','0','number')+area('notes'),'Log expense / time')
        body+='<p><a href="/growth/export.csv">Export leads CSV</a> · <a href="/growth/expenses.csv">Export expenses CSV</a></p>'
        return shell(request,'Acquisition reports & costs',body)
    @app.post('/growth/expenses')
    async def expense(request:Request):
        f=await checked(request)
        try: minutes=int(f.get('minutes','0'))
        except ValueError: raise HTTPException(400,'Minutes must be a whole number.')
        if not 0<=minutes<=100000: raise HTTPException(400,'Check minutes.')
        with m.conn() as c: c.execute('INSERT INTO growth_expenses(spent_on,source,amount,minutes,notes) VALUES (?,?,?,?,?)',(day(text(f,'spent_on',10),True),text(f,'source',100,True),cents(f.get('amount','')),minutes,text(f,'notes',2000)))
        m.audit(request,'CREATE','growth_expense',None,'Outreach cost/time recorded')
        return RedirectResponse('/growth/reports',303)
    def export(request,tbl,filename):
        m.require_staff(request)
        with m.conn() as c:
            cur=c.execute(f'SELECT * FROM {tbl} ORDER BY id'); rows=cur.fetchall(); headers=[x[0] for x in cur.description]
        def safe(v):
            s=str(v if v is not None else '')
            return "'"+s if s.lstrip().startswith(('=','+','-','@','\t','\r','\n')) else s
        out=io.StringIO(); writer=csv.writer(out); writer.writerow(headers)
        for r in rows: writer.writerow([safe(v) for v in r])
        return Response('\ufeff'+out.getvalue(),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="{filename}"'})
    @app.get('/growth/export.csv')
    def export_leads(request:Request): return export(request,'growth_leads','sales-leads.csv')
    @app.get('/growth/expenses.csv')
    def export_expenses(request:Request): return export(request,'growth_expenses','sales-expenses.csv')

    @app.get('/growth/setup',response_class=HTMLResponse)
    def setup(request:Request):
        m.require_staff(request); cfg=settings()
        body='<p>Launch territory: rural Milford 60953, Rossville 60963, Watseka 60970 and Hoopeston 60942. Availability checks remain manual until a supported carrier eligibility integration is configured.</p>'
        body+=form(request,'/growth/launch',field('start_date',today(),'date',True),'Create 30-day launch checklist (once)')
        if m.role(request)=='admin':
            body+='<h2>Default quote economics and public inquiries</h2><p>Defaults apply to new quotes only. Existing plans, invoices and signed quote snapshots are preserved. Enter processing/support estimates under Other Monthly. A zero means not yet budgeted.</p>'
            fields=''.join(field(k,str(cfg[k]/100),'number') for k in ['service','lease','activation','wholesale_service','wholesale_modem','other_monthly','overhead','launch_budget'])+field('goal',cfg['goal'],'number')+select('public_enabled',[('0','Public inquiry submission disabled'),('1','Enable public inquiry submission')],int(cfg['public_enabled']))
            body+=form(request,'/growth/setup',fields,'Save settings')
        body+=f'<h2>Website connection</h2><p>After enabling inquiries, point your website’s Check Availability button to <code>{esc(m.PUBLIC_URL)}/availability</code>. No separate website plugin is needed. Test this URL in a signed-out browser. Inquiries create leads and internal tasks; the CRM does not send unsolicited messages.</p>'
        body+='<h2>Wholesale questions to confirm</h2><ul><li>Residential address eligibility and performance/data policies.</li><li>Service and modem billing start dates; inactive equipment costs.</li><li>Failed-installation returns, shipping and cancellation charges.</li><li>Compatible owned equipment and volume pricing at 10, 25 and 50 lines.</li></ul><p>Record the written answers in a launch task’s outcome notes.</p>'
        return shell(request,'Launch setup',body)
    @app.post('/growth/setup')
    async def setup_save(request:Request):
        f=await checked(request,True); cfg=settings()
        for k in ['service','lease','activation','wholesale_service','wholesale_modem','other_monthly','overhead','launch_budget']: cfg[k]=cents(f.get(k,''))
        try: cfg['goal']=int(f.get('goal',''))
        except ValueError: raise HTTPException(400,'Goal must be a whole number.')
        if not 1<=cfg['goal']<=100000: raise HTTPException(400,'Check goal.')
        cfg['public_enabled']=f.get('public_enabled')=='1'
        with m.conn() as c: c.execute("INSERT INTO settings(key,value) VALUES ('growth_config',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(json.dumps(cfg),))
        m.audit(request,'UPDATE','growth_config',None,'Sales defaults / public inquiry setting')
        return RedirectResponse('/growth/setup',303)
    @app.post('/growth/launch')
    async def launch(request:Request):
        f=await checked(request); start=date.fromisoformat(day(text(f,'start_date',10),True))
        jobs=[(0,'Confirm wholesale costs, eligibility, equipment and return terms'),(1,'Research five rural addresses in each target ZIP'),(2,'Choose one starting rural cluster'),(2,'Check website pricing, branding and contact details; test inquiry form'),(3,'Request five personal introductions'),(4,'Request five more personal introductions'),(5,'Request five more personal introductions'),(6,'Request final five personal introductions'),(7,'Approach five local referral partners and record permission'),(8,'Publish local availability post with inquiry link'),(10,'Publish real equipment demonstration'),(12,'Publish owner introduction and support hours'),(14,'Review qualified leads, quotes and next actions'),(20,'Check first activations and resolve service problems'),(27,'Review first-month results and plan next territory')]
        with m.conn() as c:
            for n,(offset,title) in enumerate(jobs): task(c,title,(start+timedelta(days=offset)).isoformat(),key=f'launch:{n}')
            for week in range(4): task(c,'Weekly sales review: sources, quotes, activations, spending and lost reasons',(start+timedelta(days=6+7*week)).isoformat(),key=f'weekly:{week}')
        return RedirectResponse('/growth/tasks',303)

    def public_page(request,body):
        return HTMLResponse('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Entire Wireless — Check Availability</title><style>'+m.CSS+'</style></head><body><main class="portal"><img src="/assets/entire-wireless-logo.png" alt="Entire Wireless" style="max-width:200px"><h1>Check rural internet availability</h1>'+body+'</main></body></html>',headers={'Cache-Control':'no-store'})
    @app.get('/availability',response_class=HTMLResponse)
    def availability(request:Request):
        cfg=settings()
        if not cfg['public_enabled'] and not m.staff(request): return public_page(request,f'<p>Please contact Entire Wireless at {esc(m.COMPANY_PHONE)} or {esc(m.SUPPORT_EMAIL)} for an address check.</p>')
        request.session['inquiry_started']=int(datetime.now().timestamp())
        body=f'<p>Rural Milford, Rossville, Watseka and Hoopeston. Submit your address for review; coverage is not guaranteed.</p><p><b>{dollars(cfg["service"]+cfg["lease"])} / month</b> ({dollars(cfg["service"])} service + {dollars(cfg["lease"])} modem lease). One-time activation: {dollars(cfg["activation"])}. Full service terms and any other applicable charges are provided in your quote before purchase.</p>'
        if not cfg['public_enabled']: body+='<p>Staff preview: submissions are disabled until enabled in Launch setup.</p>'
        body+=form(request,'/availability',lead_fields({'source':request.query_params.get('source','Website')},True)+'<div style="display:none" aria-hidden="true"><input name="website" tabindex="-1" autocomplete="off"></div><label><input style="width:auto" type="checkbox" name="consent" value="1" required> I agree that Entire Wireless may contact me by my selected method about this request. This does not subscribe me to a newsletter.</label>','Request address check')
        return public_page(request,body)
    # v10.7 — Authenticated server-to-server website lead intake.
    # The WordPress site uses this endpoint instead of scraping the public form/CSRF session.
    @app.post('/api/website-leads')
    async def website_lead_api(request:Request):
        if not settings()['public_enabled']:
            raise HTTPException(403,'Online inquiries are not enabled yet.')
        expected=os.getenv('WEBSITE_LEAD_API_KEY','Fthk9qMwSq8jQNHPiRdMI3mE3PlnY9TJsjO3lSeSB7N_htx7KuUIhnTr7vPGHEw1')
        supplied=request.headers.get('x-entire-wireless-key','')
        if not expected or not secrets.compare_digest(supplied,expected):
            raise HTTPException(401,'Unauthorized website lead request.')
        if int(request.headers.get('content-length','0') or 0)>20000:
            raise HTTPException(413,'Payload too large.')
        try:
            f=await request.json()
        except Exception:
            raise HTTPException(400,'Invalid JSON payload.')
        if not isinstance(f,dict): raise HTTPException(400,'Invalid lead payload.')
        if str(f.get('consent',''))!='1': raise HTTPException(400,'Inquiry follow-up consent is required.')
        f['source']='Website - WordPress'
        d=parse_lead(f,True); d['contact_consent']=1
        with m.conn() as c:
            c.execute('BEGIN IMMEDIATE'); lid,created=add_lead(c,d,None)
        return {'ok':True,'lead_id':lid,'created':created}

    @app.post('/availability')
    async def inquiry(request:Request):
        cfg=settings()
        if not cfg['public_enabled']: raise HTTPException(403,'Online inquiries are not enabled yet.')
        if int(request.headers.get('content-length','0') or 0)>20000: raise HTTPException(413,'Form too large.')
        f=await request.form()
        if not secrets.compare_digest(str(f.get('csrf','')),request.session.get('growth_csrf','missing')): raise HTTPException(403,'Reload the inquiry form and try again.')
        if f.get('website'): return public_page(request,'<p>Thank you. Your request has been received.</p>')
        if f.get('consent')!='1': raise HTTPException(400,'Please agree to inquiry follow-up.')
        import time
        now=int(time.time()); started=request.session.get('inquiry_started',0)
        if not started or now-started<2 or now-started>7200: raise HTTPException(400,'Reload the form, complete your details, and submit again.')
        # SQLite-backed limiter works across workers. Uses direct client IP, never untrusted forwarded headers.
        ip=request.client.host if request.client else 'unknown'; key=hashlib.sha256((m.SECRET_KEY+ip).encode()).hexdigest(); window=now//3600
        with m.conn() as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('DELETE FROM growth_rate_limits WHERE window<?',(window-24,))
            r=c.execute('SELECT * FROM growth_rate_limits WHERE key=?',(key,)).fetchone()
            if r and r['window']==window and r['count']>=20: raise HTTPException(429,'Too many inquiries. Please contact us directly or try later.')
            c.execute('INSERT INTO growth_rate_limits(key,window,count) VALUES (?,?,1) ON CONFLICT(key) DO UPDATE SET count=CASE WHEN window=excluded.window THEN count+1 ELSE 1 END,window=excluded.window',(key,window))
        d=parse_lead(f,True); d['contact_consent']=1
        with m.conn() as c:
            c.execute('BEGIN IMMEDIATE'); add_lead(c,d,None)
        request.session.pop('inquiry_started',None)
        return public_page(request,'<h2>Thank you.</h2><p>Your address-check request has been received. Entire Wireless will review it and contact you using your selected method. No service has been ordered and no payment has been collected.</p>')
