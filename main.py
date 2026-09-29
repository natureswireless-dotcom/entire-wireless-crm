import os, sqlite3, secrets, smtplib, hashlib, hmac, base64, json, time, asyncio, urllib.parse, urllib.request, urllib.error, html, csv, io, shutil
from pathlib import Path
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from email.message import EmailMessage
from docx import Document

from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse, Response
from starlette.middleware.sessions import SessionMiddleware
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

APP_NAME = "Entire Wireless ISP CRM v10.17"
BASE = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB = DATA_DIR / "isp_crm_v2.db"
STATEMENTS = DATA_DIR / "statements"
STATEMENTS.mkdir(exist_ok=True)
COLLECTIONS = DATA_DIR / "collections"
COLLECTIONS.mkdir(exist_ok=True)
DOCUMENTS = DATA_DIR / "customer_documents"
DOCUMENTS.mkdir(exist_ok=True)
MAX_DOCUMENT_BYTES = int(os.getenv("MAX_DOCUMENT_BYTES", str(20*1024*1024)))
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"}
SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-this-secret")
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://127.0.0.1:8000").rstrip('/')
COMPANY_NAME = os.getenv("COMPANY_NAME", "Entire Wireless")
COMPANY_LEGAL = os.getenv("COMPANY_LEGAL", "Natures Wireless LLC")
COMPANY_DBA = os.getenv("COMPANY_DBA", "Entire Wireless")
COMPANY_DISPLAY_LEGAL = os.getenv("COMPANY_DISPLAY_LEGAL", f"{COMPANY_LEGAL} d/b/a {COMPANY_DBA}")
COMPANY_SITE = os.getenv("COMPANY_SITE", "https://natureswireless.org")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@natureswireless.org")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
RECONNECT_FEE = float(os.getenv("RECONNECT_FEE", "25.00"))
SUSPEND_AFTER_DAYS = int(os.getenv("SUSPEND_AFTER_DAYS", "3"))
VERIZON_ENABLED = os.getenv("VERIZON_ENABLED", "0") == "1"
VERIZON_DRY_RUN = os.getenv("VERIZON_DRY_RUN", "1") == "1"
VERIZON_ACCOUNT_NAME = os.getenv("VERIZON_ACCOUNT_NAME", "")
VERIZON_APP_KEY = os.getenv("VERIZON_APP_KEY", "")
VERIZON_APP_SECRET = os.getenv("VERIZON_APP_SECRET", "")
VERIZON_UWS_USERNAME = os.getenv("VERIZON_UWS_USERNAME", "")
VERIZON_UWS_PASSWORD = os.getenv("VERIZON_UWS_PASSWORD", "")
VERIZON_CALLBACK_TOKEN = os.getenv("VERIZON_CALLBACK_TOKEN", "")
VERIZON_BASE_URL = os.getenv("VERIZON_BASE_URL", "https://thingspace.verizon.com/api/m2m/v1").rstrip('/')
VERIZON_OAUTH_URL = os.getenv("VERIZON_OAUTH_URL", "https://thingspace.verizon.com/api/ts/v1/oauth2/token")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "(815) 694-WIRE")
COMPANY_ADDRESS = os.getenv("COMPANY_ADDRESS", "35412 N 770 East Rd, Rossville, IL 60963")
BUSINESS_TIMEZONE = os.getenv("BUSINESS_TIMEZONE", "America/Chicago")
BUSINESS_CLOSE_HOUR = int(os.getenv("BUSINESS_CLOSE_HOUR", "17"))
PAST_DUE_REMINDER_DAYS = int(os.getenv("PAST_DUE_REMINDER_DAYS", "7"))
VERIZON_ACCOUNT_DISPLAY_NAME = os.getenv("VERIZON_ACCOUNT_DISPLAY_NAME", COMPANY_DISPLAY_LEGAL)
UNRETURNED_EQUIPMENT_FEE = float(os.getenv("UNRETURNED_EQUIPMENT_FEE", "700.00"))
EARLY_TERMINATION_MONTHLY_FEE = float(os.getenv("EARLY_TERMINATION_MONTHLY_FEE", "20.00"))
SIM_REPLACEMENT_FEE = float(os.getenv("SIM_REPLACEMENT_FEE", "5.00"))
PASSWORD_MAX_AGE_DAYS = int(os.getenv("PASSWORD_MAX_AGE_DAYS", "90"))
PASSWORD_HISTORY_COUNT = int(os.getenv("PASSWORD_HISTORY_COUNT", "3"))
QUICKBOOKS_ENABLED = os.getenv("QUICKBOOKS_ENABLED", "0") == "1"
QUICKBOOKS_ENVIRONMENT = os.getenv("QUICKBOOKS_ENVIRONMENT", "sandbox").lower()
QUICKBOOKS_CLIENT_ID = os.getenv("QUICKBOOKS_CLIENT_ID", "")
QUICKBOOKS_CLIENT_SECRET = os.getenv("QUICKBOOKS_CLIENT_SECRET", "")
QUICKBOOKS_REDIRECT_URI = os.getenv("QUICKBOOKS_REDIRECT_URI", f"{PUBLIC_URL}/quickbooks/callback")
QB_AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
QB_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
QB_API_BASE = "https://sandbox-quickbooks.api.intuit.com" if QUICKBOOKS_ENVIRONMENT == "sandbox" else "https://quickbooks.api.intuit.com"
QB_API_TIMEOUT = int(os.getenv("QUICKBOOKS_API_TIMEOUT", "90"))
QB_API_RETRIES = max(1, int(os.getenv("QUICKBOOKS_API_RETRIES", "2")))

# Zoho Books integration (V9)
ZOHO_ENABLED = os.getenv("ZOHO_ENABLED", "0") == "1"
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID", "")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET", "")
ZOHO_REDIRECT_URI = os.getenv("ZOHO_REDIRECT_URI", f"{PUBLIC_URL}/zoho/callback")
ZOHO_ACCOUNTS_BASE = os.getenv("ZOHO_ACCOUNTS_BASE", "https://accounts.zoho.com").rstrip('/')
ZOHO_API_DOMAIN = os.getenv("ZOHO_API_DOMAIN", "https://www.zohoapis.com").rstrip('/')
ZOHO_API_TIMEOUT = int(os.getenv("ZOHO_API_TIMEOUT", "60"))
ZOHO_API_RETRIES = max(1, int(os.getenv("ZOHO_API_RETRIES", "2")))
ZOHO_SCOPES = os.getenv("ZOHO_SCOPES", "ZohoBooks.settings.ALL,ZohoBooks.contacts.ALL,ZohoBooks.invoices.ALL,ZohoBooks.customerpayments.ALL")
ACCOUNTING_PROVIDER = os.getenv("ACCOUNTING_PROVIDER", "").strip().lower()
if not ACCOUNTING_PROVIDER:
    ACCOUNTING_PROVIDER = "zoho" if ZOHO_ENABLED else ("quickbooks" if QUICKBOOKS_ENABLED else "none")
ACCOUNTING_SHOW_INACTIVE = os.getenv("ACCOUNTING_SHOW_INACTIVE", "0") == "1"

# WooCommerce storefront integration (v10.2)
WOOCOMMERCE_ENABLED = os.getenv("WOOCOMMERCE_ENABLED", "0") == "1"
WOOCOMMERCE_STORE_URL = os.getenv("WOOCOMMERCE_STORE_URL", "https://natureswireless.org").rstrip('/')
WOOCOMMERCE_CONSUMER_KEY = os.getenv("WOOCOMMERCE_CONSUMER_KEY", "")
WOOCOMMERCE_CONSUMER_SECRET = os.getenv("WOOCOMMERCE_CONSUMER_SECRET", "")
WOOCOMMERCE_WEBHOOK_SECRET = os.getenv("WOOCOMMERCE_WEBHOOK_SECRET", "")
WOOCOMMERCE_ACTIVATION_FEE = float(os.getenv("WOOCOMMERCE_ACTIVATION_FEE", "25.00"))
SERVICE_AGREEMENT_TEMPLATE = BASE / "Entire_Wireless_36_Month_ISP_Service_Agreement_Illinois.docx"

app = FastAPI(title=APP_NAME, docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, https_only=COOKIE_SECURE, same_site="lax")

CSS = '''
:root{--blue:#2596be;--nav:#102f3d;--bg:#f4f8fa;--card:#fff;--text:#18323d;--muted:#687b84;--danger:#b83b32;--ok:#1f7a62;--warn:#a66a18}
*{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif;background:var(--bg);color:var(--text)}a{color:#167ca1}.top{background:var(--nav);color:#fff;padding:15px 22px;display:flex;justify-content:space-between;gap:16px;align-items:center}.brand{font-size:21px;font-weight:800;display:flex;align-items:center;gap:10px}.brand-logo{height:42px;width:auto;max-width:125px;object-fit:contain}.brand span{color:#6fd3f2}.wrap{display:flex;min-height:calc(100vh - 58px)}nav{width:230px;background:#173e50;padding:17px 12px}nav a{display:block;color:#eef9fc;text-decoration:none;padding:11px 12px;border-radius:8px;margin:3px 0}nav a:hover{background:#22586e}.content{flex:1;padding:24px;max-width:1450px}h1{margin-top:0}.grid{display:grid;grid-template-columns:repeat(4,minmax(170px,1fr));gap:14px}.card{background:#fff;border-radius:12px;padding:18px;box-shadow:0 2px 12px #0000000d}.metric{font-size:27px;font-weight:800;color:var(--blue)}.muted{color:var(--muted);font-size:13px}.section{margin-top:18px}.row{display:grid;grid-template-columns:1fr 1fr;gap:16px}.three{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}table{width:100%;border-collapse:collapse;background:#fff}th,td{text-align:left;padding:10px;border-bottom:1px solid #e6edf0;vertical-align:top}th{background:#eaf5f9}input,select,textarea{width:100%;padding:10px;border:1px solid #c7d5db;border-radius:7px;margin:5px 0 12px;background:white}.btn{display:inline-block;background:var(--blue);color:#fff;border:none;border-radius:7px;padding:10px 14px;text-decoration:none;cursor:pointer}.btn.secondary{background:#59717b}.btn.danger{background:var(--danger)}.btn.ok{background:var(--ok)}.actions{display:flex;gap:8px;flex-wrap:wrap}.right{justify-content:flex-end}.pill{display:inline-block;padding:4px 9px;border-radius:999px;background:#e7f5ef;color:#176b55;font-size:12px}.pill.warn{background:#fff2df;color:#95601d}.pill.bad{background:#fde8e5;color:#9a3024}.notice{padding:12px;background:#eaf7fb;border-left:4px solid var(--blue);border-radius:6px;margin-bottom:15px}.login{max-width:430px;margin:8vh auto}.login .card{padding:28px}.kicker{font-size:12px;text-transform:uppercase;letter-spacing:.09em;color:var(--muted)}.portal-top{background:#102f3d;color:white;padding:18px}.portal{max-width:1100px;margin:24px auto;padding:0 18px}.danger-text{color:var(--danger)}@media(max-width:950px){nav{width:165px}.grid{grid-template-columns:1fr 1fr}.row,.three{grid-template-columns:1fr}}@media(max-width:650px){.wrap{display:block}nav{width:auto}.grid{grid-template-columns:1fr}.content{padding:14px}}
'''


EW_SALES_TAX_OTHER_FEES=8.00
EW_SALES_TAX_OTHER_FEES_LABEL="Sales Tax & Other Fees"

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def money(v): return f"${float(v or 0):,.2f}"

def add_months(d: date, months: int) -> date:
    import calendar
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    day = min(d.day, calendar.monthrange(y, m)[1])
    return date(y, m, day)

def whole_months_remaining(contract_start: str, contract_months: int, as_of: date) -> int:
    if not contract_start or not contract_months:
        return 0
    try:
        start = date.fromisoformat(contract_start[:10])
    except Exception:
        return 0
    end = add_months(start, int(contract_months))
    if as_of >= end:
        return 0
    months = (end.year - as_of.year) * 12 + (end.month - as_of.month)
    if as_of.day > end.day:
        months -= 1
    return max(0, months)

def phash(p):
    salt=os.urandom(16)
    dk=hashlib.pbkdf2_hmac('sha256',p.encode(),salt,210000)
    return 'pbkdf2_sha256$210000$'+base64.urlsafe_b64encode(salt).decode()+'$'+base64.urlsafe_b64encode(dk).decode()
def pcheck(p,h):
    try:
        alg,iters,salt_b64,dk_b64=h.split('$',3)
        salt=base64.urlsafe_b64decode(salt_b64.encode()); expected=base64.urlsafe_b64decode(dk_b64.encode())
        actual=hashlib.pbkdf2_hmac('sha256',p.encode(),salt,int(iters))
        return hmac.compare_digest(actual,expected)
    except Exception: return False

def password_is_reused(c, user_id, new_password, current_hash=None):
    hashes=[]
    if current_hash:
        hashes.append(current_hash)
    for r in c.execute("SELECT password_hash FROM password_history WHERE user_id=? ORDER BY id DESC LIMIT ?",(user_id,max(PASSWORD_HISTORY_COUNT,1))).fetchall():
        if r['password_hash'] not in hashes:
            hashes.append(r['password_hash'])
    return any(pcheck(new_password,h) for h in hashes[:PASSWORD_HISTORY_COUNT])

def password_expired(user):
    if user['role']=='admin':
        return False
    raw=user['password_changed_at']
    if not raw:
        return True
    try:
        changed=datetime.fromisoformat(str(raw).replace('Z','+00:00')).replace(tzinfo=None)
    except Exception:
        return True
    return datetime.now()-changed >= timedelta(days=PASSWORD_MAX_AGE_DAYS)

def init_db():
    with conn() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'staff',active INTEGER DEFAULT 1,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY AUTOINCREMENT,account_no TEXT UNIQUE NOT NULL,first_name TEXT NOT NULL,last_name TEXT NOT NULL,company TEXT,email TEXT,phone TEXT,service_address TEXT,city TEXT,state TEXT,zip TEXT,billing_address TEXT,status TEXT DEFAULT 'Active',billing_day INTEGER DEFAULT 1,autopay INTEGER DEFAULT 0,contract_start TEXT,contract_months INTEGER DEFAULT 36,portal_password_hash TEXT,portal_enabled INTEGER DEFAULT 1,notes TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS plans(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,monthly_price REAL NOT NULL,modem_lease REAL DEFAULT 0,description TEXT,active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS subscriptions(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_id INTEGER NOT NULL UNIQUE,plan_id INTEGER NOT NULL,start_date TEXT NOT NULL,status TEXT DEFAULT 'Active',FOREIGN KEY(customer_id) REFERENCES customers(id),FOREIGN KEY(plan_id) REFERENCES plans(id));
        CREATE TABLE IF NOT EXISTS modems(id INTEGER PRIMARY KEY AUTOINCREMENT,imei TEXT UNIQUE NOT NULL,serial_no TEXT,manufacturer TEXT,model TEXT,status TEXT DEFAULT 'Available',customer_id INTEGER,acquired_date TEXT,notes TEXT,FOREIGN KEY(customer_id) REFERENCES customers(id));
        CREATE TABLE IF NOT EXISTS sims(id INTEGER PRIMARY KEY AUTOINCREMENT,iccid TEXT UNIQUE NOT NULL,carrier TEXT,mdn TEXT,status TEXT DEFAULT 'Available',customer_id INTEGER,activation_date TEXT,notes TEXT,FOREIGN KEY(customer_id) REFERENCES customers(id));
        CREATE TABLE IF NOT EXISTS equipment_history(id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,equipment_id INTEGER NOT NULL,customer_id INTEGER,action TEXT NOT NULL,details TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS tablet_services(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            woo_order_id INTEGER UNIQUE,
            imei TEXT NOT NULL,
            sim_type TEXT NOT NULL,
            monthly_price REAL NOT NULL DEFAULT 45.00,
            activation_fee REAL NOT NULL DEFAULT 15.00,
            physical_sim_fee REAL NOT NULL DEFAULT 0.00,
            start_date TEXT NOT NULL,
            contract_months INTEGER NOT NULL DEFAULT 36,
            status TEXT NOT NULL DEFAULT 'Active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(plan_id) REFERENCES plans(id)
        );
        CREATE INDEX IF NOT EXISTS idx_tablet_services_customer ON tablet_services(customer_id);

        CREATE TABLE IF NOT EXISTS invoices(id INTEGER PRIMARY KEY AUTOINCREMENT,invoice_no TEXT UNIQUE NOT NULL,customer_id INTEGER NOT NULL,issue_date TEXT NOT NULL,due_date TEXT NOT NULL,subtotal REAL NOT NULL,amount_paid REAL DEFAULT 0,status TEXT DEFAULT 'Due',pdf_path TEXT,emailed_at TEXT,last_reminder_at TEXT,stripe_session_id TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(customer_id) REFERENCES customers(id));
        CREATE TABLE IF NOT EXISTS invoice_items(id INTEGER PRIMARY KEY AUTOINCREMENT,invoice_id INTEGER NOT NULL,description TEXT NOT NULL,qty REAL DEFAULT 1,unit_price REAL NOT NULL,amount REAL NOT NULL,FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS payments(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_id INTEGER NOT NULL,invoice_id INTEGER,amount REAL NOT NULL,payment_date TEXT NOT NULL,method TEXT,reference TEXT,notes TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(customer_id) REFERENCES customers(id),FOREIGN KEY(invoice_id) REFERENCES invoices(id));
        CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,user_email TEXT,action TEXT,entity TEXT,entity_id INTEGER,details TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
        CREATE TABLE IF NOT EXISTS customer_documents(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_id INTEGER NOT NULL,original_name TEXT NOT NULL,stored_name TEXT NOT NULL,document_type TEXT DEFAULT 'Customer Agreement / Contract',notes TEXT,content_type TEXT,size_bytes INTEGER DEFAULT 0,uploaded_by TEXT,uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(customer_id) REFERENCES customers(id));
        CREATE TABLE IF NOT EXISTS customer_notes(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_id INTEGER NOT NULL,category TEXT NOT NULL,note TEXT NOT NULL,user_id INTEGER,user_name TEXT,user_email TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(customer_id) REFERENCES customers(id));
        CREATE TABLE IF NOT EXISTS customer_message_threads(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        );
        CREATE TABLE IF NOT EXISTS customer_messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            sender_type TEXT NOT NULL,
            sender_user_id INTEGER,
            sender_name TEXT,
            body TEXT NOT NULL,
            read_by_staff INTEGER DEFAULT 0,
            read_by_customer INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(thread_id) REFERENCES customer_message_threads(id),
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        );
        CREATE INDEX IF NOT EXISTS idx_customer_message_threads_customer ON customer_message_threads(customer_id);
        CREATE INDEX IF NOT EXISTS idx_customer_messages_thread ON customer_messages(thread_id);
        CREATE INDEX IF NOT EXISTS idx_customer_messages_unread_staff ON customer_messages(read_by_staff,sender_type);
        CREATE TABLE IF NOT EXISTS woocommerce_orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            woo_order_id INTEGER UNIQUE NOT NULL,
            customer_id INTEGER,
            invoice_id INTEGER,
            payment_id INTEGER,
            customer_type TEXT,
            plan_name TEXT,
            order_status TEXT,
            payment_method TEXT,
            order_total REAL DEFAULT 0,
            transaction_id TEXT,
            sync_status TEXT DEFAULT 'Received',
            sync_error TEXT,
            payload_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_woocommerce_orders_customer ON woocommerce_orders(customer_id);
        CREATE INDEX IF NOT EXISTS idx_woocommerce_orders_status ON woocommerce_orders(sync_status);
        CREATE TABLE IF NOT EXISTS customer_onboarding(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL UNIQUE,
            woo_order_id INTEGER,
            stage TEXT NOT NULL DEFAULT 'Order Received',
            order_received_at TEXT,
            payment_confirmed_at TEXT,
            agreement_signed_at TEXT,
            equipment_assigned_at TEXT,
            provisioning_started_at TEXT,
            ready_for_service_at TEXT,
            activated_at TEXT,
            staff_notes TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        );
        CREATE INDEX IF NOT EXISTS idx_customer_onboarding_stage ON customer_onboarding(stage);
        ''')
        for col,sql in [
            ('deactivated_at', "ALTER TABLE customers ADD COLUMN deactivated_at TEXT"),
            ('deactivation_reason', "ALTER TABLE customers ADD COLUMN deactivation_reason TEXT")]:
            try: c.execute(sql)
            except sqlite3.OperationalError: pass
        # v9.6 subscriber classification
        try: c.execute("ALTER TABLE customers ADD COLUMN customer_type TEXT DEFAULT 'Residential'")
        except sqlite3.OperationalError: pass
        c.execute("UPDATE customers SET customer_type='Residential' WHERE customer_type IS NULL OR trim(customer_type)=''")
        # Employee password-security migrations (v5.5)
        for col, ddl in [
            ('must_change_password', "ALTER TABLE users ADD COLUMN must_change_password INTEGER DEFAULT 0"),
            ('password_changed_at', "ALTER TABLE users ADD COLUMN password_changed_at TEXT"),
            ('password_reset_at', "ALTER TABLE users ADD COLUMN password_reset_at TEXT"),
            ('password_reset_by', "ALTER TABLE users ADD COLUMN password_reset_by TEXT")]:
            try: c.execute(ddl)
            except sqlite3.OperationalError: pass
        # Employee credential deactivation tracking (v5.6)
        for col, ddl in [
            ('deactivated_at', "ALTER TABLE users ADD COLUMN deactivated_at TEXT"),
            ('deactivated_by', "ALTER TABLE users ADD COLUMN deactivated_by TEXT"),
            ('deactivation_reason', "ALTER TABLE users ADD COLUMN deactivation_reason TEXT")]:
            try: c.execute(ddl)
            except sqlite3.OperationalError: pass
        c.execute("CREATE TABLE IF NOT EXISTS password_history(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,password_hash TEXT NOT NULL,used_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)")
        c.execute("CREATE TABLE IF NOT EXISTS api_tokens(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,token_hash TEXT UNIQUE NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,last_used_at TEXT,expires_at TEXT NOT NULL,revoked_at TEXT,device_name TEXT,FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)")
        c.execute("UPDATE users SET must_change_password=1 WHERE role!='admin' AND password_changed_at IS NULL")
        c.execute("UPDATE users SET password_changed_at=COALESCE(password_changed_at, created_at, CURRENT_TIMESTAMP) WHERE role='admin'")
        for u in c.execute("SELECT id,password_hash FROM users").fetchall():
            if not c.execute("SELECT 1 FROM password_history WHERE user_id=? LIMIT 1",(u['id'],)).fetchone():
                c.execute("INSERT INTO password_history(user_id,password_hash) VALUES (?,?)",(u['id'],u['password_hash']))
        # QuickBooks Online integration migrations (v8.0)
        for ddl in [
            "ALTER TABLE customers ADD COLUMN quickbooks_customer_id TEXT",
            "ALTER TABLE customers ADD COLUMN quickbooks_sync_status TEXT",
            "ALTER TABLE customers ADD COLUMN quickbooks_sync_error TEXT",
            "ALTER TABLE customers ADD COLUMN quickbooks_synced_at TEXT",
            "ALTER TABLE invoices ADD COLUMN quickbooks_invoice_id TEXT",
            "ALTER TABLE invoices ADD COLUMN quickbooks_sync_status TEXT",
            "ALTER TABLE invoices ADD COLUMN quickbooks_sync_error TEXT",
            "ALTER TABLE invoices ADD COLUMN quickbooks_synced_at TEXT",
            "ALTER TABLE payments ADD COLUMN quickbooks_payment_id TEXT",
            "ALTER TABLE payments ADD COLUMN quickbooks_sync_status TEXT",
            "ALTER TABLE payments ADD COLUMN quickbooks_sync_error TEXT",
            "ALTER TABLE payments ADD COLUMN quickbooks_synced_at TEXT"]:
            try: c.execute(ddl)
            except sqlite3.OperationalError: pass
        c.execute("CREATE TABLE IF NOT EXISTS quickbooks_sync_log(id INTEGER PRIMARY KEY AUTOINCREMENT,entity_type TEXT NOT NULL,entity_id INTEGER,action TEXT,status TEXT,quickbooks_id TEXT,error TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS quickbooks_oauth(id INTEGER PRIMARY KEY CHECK(id=1),realm_id TEXT,access_token TEXT,refresh_token TEXT,access_expires_at TEXT,refresh_expires_at TEXT,company_name TEXT,connected_at TEXT,updated_at TEXT)")
        # Zoho Books V9 migrations are additive and preserve all existing CRM/QuickBooks data.
        for sql in [
            "ALTER TABLE customers ADD COLUMN zoho_contact_id TEXT",
            "ALTER TABLE customers ADD COLUMN zoho_sync_status TEXT",
            "ALTER TABLE customers ADD COLUMN zoho_sync_error TEXT",
            "ALTER TABLE customers ADD COLUMN zoho_synced_at TEXT",
            "ALTER TABLE invoices ADD COLUMN zoho_invoice_id TEXT",
            "ALTER TABLE invoices ADD COLUMN zoho_sync_status TEXT",
            "ALTER TABLE invoices ADD COLUMN zoho_sync_error TEXT",
            "ALTER TABLE invoices ADD COLUMN zoho_synced_at TEXT",
            "ALTER TABLE payments ADD COLUMN zoho_payment_id TEXT",
            "ALTER TABLE payments ADD COLUMN zoho_sync_status TEXT",
            "ALTER TABLE payments ADD COLUMN zoho_sync_error TEXT",
            "ALTER TABLE payments ADD COLUMN zoho_synced_at TEXT"]:
            try: c.execute(sql)
            except sqlite3.OperationalError: pass
        # Modem lease promotion migrations (v9.5 promotion update)
        for ddl in [
            "ALTER TABLE customers ADD COLUMN modem_promo_free_months INTEGER DEFAULT 0",
            "ALTER TABLE customers ADD COLUMN modem_promo_cycles_used INTEGER DEFAULT 0",
            "ALTER TABLE customers ADD COLUMN modem_promo_start TEXT",
            "ALTER TABLE customers ADD COLUMN modem_promo_name TEXT"]:
            try: c.execute(ddl)
            except sqlite3.OperationalError: pass
        # Stripe onboarding / contract billing migrations (v9.5 online-payment update)
        for ddl in [
            "ALTER TABLE customers ADD COLUMN billing_hold_until_first_payment INTEGER DEFAULT 0",
            "ALTER TABLE customers ADD COLUMN billing_started_at TEXT",
            "ALTER TABLE customers ADD COLUMN initial_invoice_id INTEGER",
            "ALTER TABLE customers ADD COLUMN first_stripe_payment_at TEXT"]:
            try: c.execute(ddl)
            except sqlite3.OperationalError: pass
        c.execute("CREATE TABLE IF NOT EXISTS zoho_sync_log(id INTEGER PRIMARY KEY AUTOINCREMENT,entity_type TEXT NOT NULL,entity_id INTEGER,action TEXT,status TEXT,zoho_id TEXT,error TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS zoho_oauth(id INTEGER PRIMARY KEY CHECK(id=1),organization_id TEXT,organization_name TEXT,access_token TEXT,refresh_token TEXT,access_expires_at TEXT,api_domain TEXT,connected_at TEXT,updated_at TEXT)")
        try:
            c.execute("ALTER TABLE customers ADD COLUMN referral_code TEXT")
        except Exception:
            pass
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_referral_code ON customers(referral_code) WHERE referral_code IS NOT NULL")
        # Give every existing customer a stable, human-readable referral code.
        missing=c.execute("SELECT id,account_no FROM customers WHERE referral_code IS NULL OR TRIM(referral_code)='' ORDER BY id").fetchall()
        for rr in missing:
            base='EWREF-'+''.join(ch for ch in str(rr['account_no'] or rr['id']) if ch.isdigit())[-6:]
            code=base; n=1
            while c.execute("SELECT 1 FROM customers WHERE referral_code=? AND id<>?",(code,rr['id'])).fetchone():
                n+=1; code=f"{base}-{n}"
            c.execute("UPDATE customers SET referral_code=? WHERE id=?",(code,rr['id']))

        c.execute("CREATE TABLE IF NOT EXISTS zoho_history_runs(id INTEGER PRIMARY KEY AUTOINCREMENT,filter_mode TEXT,start_date TEXT,end_date TEXT,customer_id INTEGER,batch_size INTEGER,customers_attempted INTEGER DEFAULT 0,invoices_attempted INTEGER DEFAULT 0,payments_attempted INTEGER DEFAULT 0,customers_synced INTEGER DEFAULT 0,invoices_synced INTEGER DEFAULT 0,payments_synced INTEGER DEFAULT 0,failures INTEGER DEFAULT 0,started_at TEXT DEFAULT CURRENT_TIMESTAMP,completed_at TEXT,run_by TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS pending_charges(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_id INTEGER NOT NULL,description TEXT NOT NULL,amount REAL NOT NULL,source TEXT,source_id INTEGER,applied_invoice_id INTEGER,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(customer_id) REFERENCES customers(id))")
        c.execute("CREATE TABLE IF NOT EXISTS charge_reversals(id INTEGER PRIMARY KEY AUTOINCREMENT,invoice_id INTEGER NOT NULL,original_item_id INTEGER NOT NULL,reversal_item_id INTEGER,amount REAL NOT NULL,reason TEXT NOT NULL,reversed_by TEXT,reversed_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(invoice_id) REFERENCES invoices(id),FOREIGN KEY(original_item_id) REFERENCES invoice_items(id),FOREIGN KEY(reversal_item_id) REFERENCES invoice_items(id))")
        c.execute("CREATE TABLE IF NOT EXISTS carrier_actions(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_id INTEGER NOT NULL,sim_id INTEGER,action TEXT NOT NULL,provider TEXT DEFAULT 'Verizon',status TEXT NOT NULL,request_id TEXT,response TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,completed_at TEXT,FOREIGN KEY(customer_id) REFERENCES customers(id),FOREIGN KEY(sim_id) REFERENCES sims(id))")
        c.execute("""CREATE TABLE IF NOT EXISTS collection_letters(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_id INTEGER NOT NULL,stage TEXT NOT NULL,balance REAL NOT NULL,pdf_path TEXT,generated_at TEXT DEFAULT CURRENT_TIMESTAMP,generated_by TEXT,emailed_at TEXT,email_to TEXT,notes TEXT,FOREIGN KEY(customer_id) REFERENCES customers(id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS customer_referrals(id INTEGER PRIMARY KEY AUTOINCREMENT,referrer_customer_id INTEGER NOT NULL,referred_customer_id INTEGER NOT NULL UNIQUE,status TEXT NOT NULL DEFAULT 'Pending',reward_months INTEGER NOT NULL DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP,qualified_at TEXT,qualified_by TEXT,notes TEXT,FOREIGN KEY(referrer_customer_id) REFERENCES customers(id),FOREIGN KEY(referred_customer_id) REFERENCES customers(id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS referral_reward_ledger(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_id INTEGER NOT NULL,referral_id INTEGER,months INTEGER NOT NULL,entry_type TEXT NOT NULL,invoice_id INTEGER,notes TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,created_by TEXT,FOREIGN KEY(customer_id) REFERENCES customers(id),FOREIGN KEY(referral_id) REFERENCES customer_referrals(id),FOREIGN KEY(invoice_id) REFERENCES invoices(id))""")
        for col, ddl in [
            ('service_status', "ALTER TABLE customers ADD COLUMN service_status TEXT DEFAULT 'Active'"),
            ('suspension_exempt', "ALTER TABLE customers ADD COLUMN suspension_exempt INTEGER DEFAULT 0"),
            ('payment_arrangement', "ALTER TABLE customers ADD COLUMN payment_arrangement INTEGER DEFAULT 0"),
            ('last_suspend_at', "ALTER TABLE customers ADD COLUMN last_suspend_at TEXT"),
            ('last_restore_at', "ALTER TABLE customers ADD COLUMN last_restore_at TEXT")]:
            try: c.execute(ddl)
            except sqlite3.OperationalError: pass
        for col, ddl in [
            ('eod_notice_at', "ALTER TABLE invoices ADD COLUMN eod_notice_at TEXT"),
            ('eod_notice_pdf', "ALTER TABLE invoices ADD COLUMN eod_notice_pdf TEXT"),
            ('voided_at', "ALTER TABLE invoices ADD COLUMN voided_at TEXT"),
            ('voided_by', "ALTER TABLE invoices ADD COLUMN voided_by TEXT"),
            ('void_reason', "ALTER TABLE invoices ADD COLUMN void_reason TEXT"),
            ('edited_at', "ALTER TABLE invoices ADD COLUMN edited_at TEXT"),
            ('edited_by', "ALTER TABLE invoices ADD COLUMN edited_by TEXT")]:
            try: c.execute(ddl)
            except sqlite3.OperationalError: pass
        if not c.execute("SELECT 1 FROM plans LIMIT 1").fetchone():
            c.execute("INSERT INTO plans(name,monthly_price,modem_lease,description) VALUES (?,?,?,?)",("Unlimited Internet",85,10,"Residential unlimited high-speed Internet service"))
        # v10.11: current service catalog is synchronized below after schema initialization.
        admin_email = os.getenv("ADMIN_EMAIL", "admin@natureswireless.org").lower()
        admin_password = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")
        if not c.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            c.execute("INSERT INTO users(email,name,password_hash,role,must_change_password,password_changed_at) VALUES (?,?,?,?,0,CURRENT_TIMESTAMP)",(admin_email,"Administrator",phash(admin_password),"admin"))
init_db()

def ew_v1010_sync_service_catalog():
    """Synchronize the visible Service Plans catalog to the four current 5G plans."""
    current = [
      ("5G Internet 100 Mbps - Residential",85.00,0.00,"Residential 5G Internet 100 Mbps with unlimited data — Plan 59142. Availability depends on service address, approved router and network capacity. Eligible 5G C-Band addresses and compatible 5G C-Band routers only."),
      ("5G Internet 200 Mbps - Residential",105.00,0.00,"Residential 5G Internet 200 Mbps with unlimited data — Plan 59145. Availability depends on service address, approved router and network capacity. Eligible 5G C-Band addresses and compatible 5G C-Band routers only."),
      ("5G Internet 100 Mbps - Business",95.00,0.00,"Business 5G Internet 100 Mbps with unlimited data — Plan 59143. Availability depends on service address, approved router and network capacity. Eligible 5G C-Band addresses and compatible 5G C-Band routers only."),
      ("5G Internet 200 Mbps - Business",115.00,0.00,"Business 5G Internet 200 Mbps with unlimited data — Plan 59146. Availability depends on service address, approved router and network capacity. Eligible 5G C-Band addresses and compatible 5G C-Band routers only.")
    ]
    obsolete=("Unlimited Internet","Business Internet","Tablet / iPad Unlimited Data","Tablet / iPad Unlimited Data (Obsolete)","__RETIRED_TABLET_PLAN__")
    with conn() as c:
        # Do not delete rows that historical subscriptions may reference; make them inactive instead.
        c.executemany("UPDATE plans SET active=0 WHERE name=?",[(x,) for x in obsolete])
        for name,price,modem,description in current:
            row=c.execute("SELECT id FROM plans WHERE name=?",(name,)).fetchone()
            if row:
                c.execute("UPDATE plans SET monthly_price=?,modem_lease=?,description=?,active=1 WHERE id=?",
                          (price,modem,description,row["id"]))
            else:
                c.execute("INSERT INTO plans(name,monthly_price,modem_lease,description,active) VALUES(?,?,?,?,1)",
                          (name,price,modem,description))
        c.commit()

ew_v1010_sync_service_catalog()


def generate_account_number(c, customer_type='Residential'):
    """Return the next unique 9-digit customer account number with a type-specific suffix.
    Residential/consumer accounts end in -0001; Business accounts end in -0002.
    """
    customer_type=(customer_type or 'Residential').strip().title()
    suffix='0002' if customer_type=='Business' else '0001'
    rows=c.execute("SELECT account_no FROM customers WHERE account_no LIKE ?",(f'%-{suffix}',)).fetchall()
    highest=100000000
    for row in rows:
        value=str(row['account_no'] or '')
        try:
            base,existing_suffix=value.rsplit('-',1)
            if len(base)==9 and base.isdigit() and existing_suffix==suffix:
                highest=max(highest,int(base))
        except Exception:
            pass
    candidate=highest+1
    while candidate <= 999999999:
        account_no=f"{candidate:09d}-{suffix}"
        if not c.execute("SELECT 1 FROM customers WHERE account_no=?",(account_no,)).fetchone():
            return account_no
        candidate += 1
    raise RuntimeError("No available 9-digit customer account numbers remain")

def audit(request, action, entity, entity_id=None, details=""):
    email = request.session.get("user_email") if request else "system"
    with conn() as c: c.execute("INSERT INTO audit_log(user_email,action,entity,entity_id,details) VALUES (?,?,?,?,?)",(email,action,entity,entity_id,details))

def staff(request): return bool(request.session.get("user_id"))
def role(request): return request.session.get("role", "")
def require_staff(request):
    if not staff(request): raise HTTPException(401)
    uid=request.session.get('user_id')
    with conn() as c:
        u=c.execute("SELECT * FROM users WHERE id=? AND active=1",(uid,)).fetchone()
        if not u:
            request.session.clear()
            raise HTTPException(401)
        required=bool(u['must_change_password']) or password_expired(u)
        if required and not u['must_change_password']:
            c.execute("UPDATE users SET must_change_password=1 WHERE id=?",(uid,))
    request.session['password_change_required']=required
    if required and request.url.path not in ('/change-password','/logout'):
        raise HTTPException(428)
def require_admin(request):
    require_staff(request)
    if role(request) != "admin": raise HTTPException(403)

def nav(request):
    admin_links=''
    if role(request)=='admin':
        provider_link = '<a href="/integrations/accounting">Accounting</a>'
        if ACCOUNTING_PROVIDER=='zoho':
            provider_link += '<a href="/integrations/zoho">Zoho Books</a>'
            if ACCOUNTING_SHOW_INACTIVE: provider_link += '<a href="/integrations/quickbooks">QuickBooks</a>'
        elif ACCOUNTING_PROVIDER=='quickbooks':
            provider_link += '<a href="/integrations/quickbooks">QuickBooks</a>'
            if ACCOUNTING_SHOW_INACTIVE: provider_link += '<a href="/integrations/zoho">Zoho Books</a>'
        else:
            provider_link += '<a href="/integrations/zoho">Zoho Books</a><a href="/integrations/quickbooks">QuickBooks</a>'
        admin_links = provider_link + '<a href="/integrations/woocommerce">WooCommerce</a><a href="/users">Employees</a><a href="/audit">Audit Log</a>'
    return f'''<div class="top"><div class="brand"><img class="brand-logo" src="/assets/entire-wireless-logo.png" alt="Entire Wireless logo"><div>Entire <span>Wireless</span> ISP CRM <small>v10.16.2</small></div></div><div>{request.session.get('user_name','')} · <a style="color:white" href="/change-password">Change Password</a> · <a style="color:white" href="/logout">Sign out</a></div></div><div class="wrap"><nav>
<a href="/">Dashboard</a><a href="/growth">Sales &amp; Growth</a><a href="/messages">Customer Messages</a><a href="/customers">Customers</a><a href="/plans">Service Plans</a><a href="/modems">Modems / IMEI</a><a href="/sims">SIM Cards / ICCID</a><a href="/invoices">Invoices</a><a href="/payments">Payments</a><a href="/billing">Billing Center</a><a href="/collections">Internal Collections</a><a href="/carrier">Carrier Control</a><a href="/reports">Reports</a>{admin_links}
</nav><main class="content">'''

def page(request, title, body):
    return HTMLResponse(f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body>{nav(request)}{body}</main></div></body></html>''')

def portal_page(title, body):
    return HTMLResponse(f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body><div class="portal-top"><b>{COMPANY_NAME}</b> Customer Portal <span style="float:right"><a style="color:white" href="/portal/home">Home</a> · <a style="color:white" href="/portal/messages">Messages</a> · <a style="color:white" href="/portal/logout">Sign out</a></span></div><div class="portal">{body}</div></body></html>''')

def business_now():
    try: return datetime.now(ZoneInfo(BUSINESS_TIMEZONE))
    except Exception: return datetime.now()

def update_invoice_status(c, iid):
    inv = c.execute("SELECT subtotal,amount_paid,due_date,status FROM invoices WHERE id=?",(iid,)).fetchone()
    if not inv or inv['status'] == 'Void': return
    now=business_now(); due=date.fromisoformat(inv['due_date'])
    if inv['amount_paid'] >= inv['subtotal'] - .005: s='Paid'
    elif due < now.date() or (due == now.date() and now.hour >= BUSINESS_CLOSE_HOUR): s='Past Due'
    elif inv['amount_paid'] > 0: s='Partial'
    else: s='Due'
    c.execute("UPDATE invoices SET status=? WHERE id=?",(s,iid))

def generate_statement(iid):
    """Generate a two-page Entire Wireless invoice/statement using live CRM data.

    v10.11 redesign: utility-style account statement inspired by the user's supplied
    reference, with Entire Wireless branding, billing summary, aging, transaction
    detail, service information, and a detachable remittance section.
    """
    with conn() as c:
        inv = c.execute("""SELECT i.*,c.account_no,c.first_name,c.last_name,c.customer_type,c.company,c.email,c.phone,
            c.service_address,c.billing_address,c.city,c.state,c.zip,c.contract_start,c.contract_months,
            p.name AS plan_name,p.monthly_price AS plan_monthly_price,p.modem_lease AS plan_modem_lease
            FROM invoices i
            JOIN customers c ON c.id=i.customer_id
            LEFT JOIN subscriptions s ON s.customer_id=c.id AND s.status='Active'
            LEFT JOIN plans p ON p.id=s.plan_id
            WHERE i.id=?""",(iid,)).fetchone()
        if not inv: raise ValueError("Invoice not found")
        items = c.execute("SELECT * FROM invoice_items WHERE invoice_id=? ORDER BY id",(iid,)).fetchall()
        payments = c.execute("SELECT * FROM payments WHERE invoice_id=? ORDER BY payment_date,id",(iid,)).fetchall()
        prior_rows = c.execute("SELECT id,subtotal,amount_paid,due_date,status FROM invoices WHERE customer_id=? AND id<? AND status!='Void'",(inv['customer_id'],iid)).fetchall()

        prior_open = sum(max(0,float(r['subtotal'] or 0)-float(r['amount_paid'] or 0)) for r in prior_rows)
        current_paid = float(inv['amount_paid'] or 0)
        current_charges = 0 if inv['status']=='Void' else float(inv['subtotal'] or 0)
        current_balance = max(0,current_charges-current_paid)
        total_account_due = max(0,prior_open+current_balance)
        credit_balance = max(0,current_paid-current_charges-prior_open)
        today = business_now().date()
        aging={'current':0.0,'1-30':0.0,'31-60':0.0,'over60':0.0}
        for r in prior_rows:
            bal=max(0,float(r['subtotal'] or 0)-float(r['amount_paid'] or 0))
            if bal <= .005: continue
            try: days=max(0,(today-date.fromisoformat(r['due_date'])).days)
            except Exception: days=0
            if days == 0: aging['current'] += bal
            elif days <= 30: aging['1-30'] += bal
            elif days <= 60: aging['31-60'] += bal
            else: aging['over60'] += bal
        if current_balance > .005:
            try: days=max(0,(today-date.fromisoformat(inv['due_date'])).days)
            except Exception: days=0
            if days == 0: aging['current'] += current_balance
            elif days <= 30: aging['1-30'] += current_balance
            elif days <= 60: aging['31-60'] += current_balance
            else: aging['over60'] += current_balance

        path = STATEMENTS / f"{inv['invoice_no']}.pdf"
        p=canvas.Canvas(str(path),pagesize=letter); w,h=letter
        logo=BASE/'entire_wireless_logo.png'
        EW=(37/255,150/255,190/255); DARK=(.12,.17,.22); GRAY=(.42,.45,.48); LIGHT=(.94,.96,.97)
        customer_name=(inv['company'] or f"{inv['first_name']} {inv['last_name']}").strip()
        contact_name=f"{inv['first_name']} {inv['last_name']}".strip()
        bill_address=(inv['billing_address'] or inv['service_address'] or '').strip()
        service_address=(inv['service_address'] or '').strip()
        city_state_zip=' '.join(x for x in [f"{inv['city'] or ''}," if inv['city'] else '',inv['state'] or '',inv['zip'] or ''] if x).strip()
        plan_name=(inv['plan_name'] or 'No Service Plan').strip()

        def line(x1,y1,x2,y2,width=.6,color=(.65,.68,.70)):
            p.setStrokeColorRGB(*color); p.setLineWidth(width); p.line(x1,y1,x2,y2)
        def box(x,y,bw,bh,fill=None,stroke=(.68,.71,.73),radius=0):
            if fill: p.setFillColorRGB(*fill)
            p.setStrokeColorRGB(*stroke); p.setLineWidth(.6)
            if radius: p.roundRect(x,y,bw,bh,radius,fill=1 if fill else 0,stroke=1)
            else: p.rect(x,y,bw,bh,fill=1 if fill else 0,stroke=1)
            p.setFillColorRGB(0,0,0)
        def draw_logo(x,y,width=1.70*inch,height=.64*inch):
            if logo.exists(): p.drawImage(str(logo),x,y,width=width,height=height,preserveAspectRatio=True,mask='auto')
        def header(page_no):
            draw_logo(.48*inch,h-.92*inch)
            p.setFillColorRGB(*DARK); p.setFont('Helvetica-Bold',8.2); p.drawRightString(w-.48*inch,h-.35*inch,COMPANY_DISPLAY_LEGAL)
            p.setFont('Helvetica',7.5); p.drawRightString(w-.48*inch,h-.51*inch,COMPANY_ADDRESS)
            p.drawRightString(w-.48*inch,h-.67*inch,f'{COMPANY_PHONE}  |  {SUPPORT_EMAIL}')
            p.drawRightString(w-.48*inch,h-.83*inch,COMPANY_SITE.replace('https://','').replace('http://',''))
            line(.45*inch,h-1.04*inch,w-.45*inch,h-1.04*inch,1.1,EW)
            p.setFillColorRGB(*GRAY); p.setFont('Helvetica',7); p.drawRightString(w-.48*inch,.34*inch,f'Page {page_no} of 2  |  Account {inv["account_no"]}  |  Invoice {inv["invoice_no"]}')
            p.setFillColorRGB(0,0,0)
            if inv['status']=='Void':
                p.saveState(); p.setFillColorRGB(.75,.15,.12); p.setFont('Helvetica-Bold',38); p.translate(w/2,h/2); p.rotate(35); p.drawCentredString(0,0,'VOID'); p.restoreState()
        def label_value(x,y,label,value,right=None,bold_value=False):
            p.setFillColorRGB(*GRAY); p.setFont('Helvetica',7.4); p.drawString(x,y,label.upper())
            p.setFillColorRGB(*DARK); p.setFont('Helvetica-Bold' if bold_value else 'Helvetica',9.1)
            if right is None: p.drawString(x,y-.17*inch,str(value))
            else: p.drawRightString(right,y-.17*inch,str(value))
            p.setFillColorRGB(0,0,0)
        def amount_status():
            if inv['status']=='Void': return 'VOID', money(0)
            if credit_balance > .005: return 'CREDIT BALANCE', money(-credit_balance)
            if total_account_due <= .005: return 'NO PAYMENT DUE', money(0)
            if aging['1-30']+aging['31-60']+aging['over60'] > .005: return 'PAST DUE AMOUNT', money(total_account_due)
            return 'AMOUNT NOW DUE', money(total_account_due)

        status_label,status_amount=amount_status()

        # PAGE 1 — statement summary, account activity and remittance stub.
        header(1)
        p.setFont('Helvetica-Bold',17); p.setFillColorRGB(*DARK); p.drawString(.55*inch,h-1.38*inch,'BILLING STATEMENT')
        p.setFillColorRGB(*EW); p.setFont('Helvetica-Bold',8.5); p.drawRightString(w-.55*inch,h-1.35*inch,status_label)
        p.setFont('Helvetica-Bold',17); p.drawRightString(w-.55*inch,h-1.61*inch,status_amount); p.setFillColorRGB(0,0,0)

        # Customer/address and statement metadata.
        p.setFont('Helvetica-Bold',8); p.setFillColorRGB(*GRAY); p.drawString(.58*inch,h-1.72*inch,'BILL TO')
        p.setFillColorRGB(*DARK); p.setFont('Helvetica-Bold',9.3); yy=h-1.94*inch
        address_lines=[customer_name]+([contact_name] if inv['company'] and contact_name else [])+([bill_address] if bill_address else [])+([city_state_zip] if city_state_zip else [])
        for idx,t in enumerate(address_lines):
            p.setFont('Helvetica-Bold' if idx==0 else 'Helvetica',9.1); p.drawString(.58*inch,yy,t[:56]); yy-=.17*inch
        mx=4.22*inch
        label_value(mx,h-1.72*inch,'Account Number',inv['account_no'],w-.55*inch)
        label_value(mx,h-2.12*inch,'Statement Date',inv['issue_date'],w-.55*inch)
        label_value(mx,h-2.52*inch,'Invoice Number',inv['invoice_no'],w-.55*inch)
        label_value(mx,h-2.92*inch,'Due Date',inv['due_date'],w-.55*inch,True)

        # Billing summary bar/table.
        y0=h-3.43*inch
        p.setFillColorRGB(*EW); p.rect(.48*inch,y0,.0+7.54*inch,.32*inch,fill=1,stroke=0)
        p.setFillColorRGB(1,1,1); p.setFont('Helvetica-Bold',10); p.drawString(.62*inch,y0+.10*inch,'BILLING SUMMARY'); p.setFillColorRGB(0,0,0)
        summary=[('Previous Account Balance',prior_open),('Payments / Credits',-current_paid),('New Charges',current_charges),('Current Account Balance',total_account_due)]
        sy=y0-.28*inch
        for i,(lab,val) in enumerate(summary):
            p.setFont('Helvetica-Bold' if i==3 else 'Helvetica',8.8); p.drawString(.68*inch,sy,lab); p.drawRightString(3.75*inch,sy,money(val)); sy-=.22*inch
        p.setFillColorRGB(*LIGHT); p.rect(4.08*inch,y0-.94*inch,3.63*inch,.82*inch,fill=1,stroke=0)
        p.setFillColorRGB(*GRAY); p.setFont('Helvetica-Bold',7.5); p.drawString(4.24*inch,y0-.36*inch,status_label)
        p.setFillColorRGB(*EW); p.setFont('Helvetica-Bold',18); p.drawRightString(7.55*inch,y0-.70*inch,status_amount); p.setFillColorRGB(0,0,0)

        # Aging / account status.
        ay=y0-1.33*inch
        p.setFont('Helvetica-Bold',8.2); p.setFillColorRGB(*DARK); p.drawString(.58*inch,ay,'ACCOUNT STATUS'); p.setFillColorRGB(0,0,0)
        cols=[('CURRENT',aging['current']),('1–30 DAYS',aging['1-30']),('31–60 DAYS',aging['31-60']),('OVER 60 DAYS',aging['over60'])]
        cw=1.78*inch; ax=.58*inch
        for lab,val in cols:
            box(ax,ay-.58*inch,cw,.46*inch,fill=LIGHT)
            p.setFillColorRGB(*GRAY); p.setFont('Helvetica-Bold',6.8); p.drawCentredString(ax+cw/2,ay-.28*inch,lab)
            p.setFillColorRGB(*DARK); p.setFont('Helvetica-Bold',9); p.drawCentredString(ax+cw/2,ay-.48*inch,money(val)); ax+=cw+.07*inch
        p.setFillColorRGB(0,0,0)

        # Detail section.
        dy=ay-.94*inch
        p.setFillColorRGB(*DARK); p.setFont('Helvetica-Bold',8.5); p.drawString(.58*inch,dy,'DETAIL')
        dy-=.18*inch; line(.58*inch,dy,7.72*inch,dy,.7,DARK); dy-=.16*inch
        p.setFillColorRGB(*GRAY); p.setFont('Helvetica-Bold',6.7)
        p.drawString(.60*inch,dy,'DATE'); p.drawString(1.35*inch,dy,'DESCRIPTION'); p.drawString(5.05*inch,dy,'REFERENCE'); p.drawRightString(7.65*inch,dy,'AMOUNT')
        dy-=.12*inch; line(.58*inch,dy,7.72*inch,dy,.45); dy-=.17*inch
        p.setFillColorRGB(*DARK); p.setFont('Helvetica',7.5)
        p.drawString(.60*inch,dy,inv['issue_date']); p.drawString(1.35*inch,dy,'Beginning account balance'); p.drawRightString(7.65*inch,dy,money(prior_open)); dy-=.18*inch
        for pay in payments[-4:]:
            p.drawString(.60*inch,dy,str(pay['payment_date'])[:10]); p.drawString(1.35*inch,dy,(f"{pay['method'] or 'Payment'} - Thank you")[:48]); p.drawString(5.05*inch,dy,(pay['reference'] or '')[:20]); p.drawRightString(7.65*inch,dy,money(-float(pay['amount'] or 0))); dy-=.18*inch
        for it in items[:7]:
            p.drawString(.60*inch,dy,inv['issue_date']); p.drawString(1.35*inch,dy,(it['description'] or 'Service charge')[:52]); p.drawString(5.05*inch,dy,inv['invoice_no'][:20]); p.drawRightString(7.65*inch,dy,money(float(it['amount'] or 0))); dy-=.18*inch
        p.setFont('Helvetica-Bold',7.8); p.drawString(1.35*inch,dy,'CURRENT ACCOUNT BALANCE'); p.drawRightString(7.65*inch,dy,money(total_account_due)); dy-=.20*inch
        p.setFont('Helvetica',6.9); p.setFillColorRGB(*GRAY); p.drawString(.60*inch,dy,f'Service: {plan_name}  |  Service address: {(service_address or bill_address)} {city_state_zip}'[:118]); p.setFillColorRGB(0,0,0)

        # Important message above stub.
        my=2.23*inch
        p.setFont('Helvetica-Bold',7.8); p.setFillColorRGB(*DARK); p.drawString(.58*inch,my,'IMPORTANT MESSAGE')
        p.setFont('Helvetica',6.9); p.setFillColorRGB(*GRAY)
        msg=(f'Questions about your bill? Contact {SUPPORT_EMAIL} or {COMPANY_PHONE}. '
             f'View statements and make payments through the customer portal at {PUBLIC_URL}/portal.')
        for i,t in enumerate(_wrap_pdf_text(msg,112)[:2]): p.drawString(.58*inch,my-.17*inch-(i*.13*inch),t)
        p.setFillColorRGB(0,0,0)

        # Remittance stub.
        line(.32*inch,1.72*inch,w-.32*inch,1.72*inch,.8,(.25,.25,.25))
        p.setFont('Helvetica',6.2); p.setFillColorRGB(*GRAY); p.drawString(.45*inch,1.77*inch,'DETACH AND RETURN THIS PORTION WITH PAYMENT IF PAYING BY MAIL'); p.setFillColorRGB(0,0,0)
        draw_logo(.48*inch,.88*inch,width=1.45*inch,height=.55*inch)
        p.setFont('Helvetica',6.8); p.drawString(.50*inch,.73*inch,COMPANY_DISPLAY_LEGAL[:55]); p.drawString(.50*inch,.59*inch,COMPANY_ADDRESS[:70])
        p.setFont('Helvetica-Bold',7.2); p.drawString(3.75*inch,1.49*inch,'REMITTANCE SECTION')
        p.setFont('Helvetica',7.2); ry=1.30*inch
        rem=[('Account Number',inv['account_no']),('Statement Date',inv['issue_date']),('Due Date',inv['due_date']),('Amount Now Due',status_amount)]
        for lab,val in rem:
            p.drawString(3.75*inch,ry,lab+':'); p.drawRightString(7.72*inch,ry,str(val)); ry-=.17*inch
        p.setFont('Helvetica-Bold',7.2); p.drawString(3.75*inch,.53*inch,'Amount Enclosed:  $________________________')
        p.showPage()

        # PAGE 2 — charge detail and Entire Wireless billing information.
        header(2)
        p.setFont('Helvetica-Bold',14); p.setFillColorRGB(*DARK); p.drawString(.55*inch,h-1.40*inch,'SERVICE & CHARGE DETAIL')
        p.setFont('Helvetica',7.6); p.setFillColorRGB(*GRAY); p.drawRightString(w-.55*inch,h-1.38*inch,f'{customer_name}  |  {inv["account_no"]}')
        p.setFillColorRGB(0,0,0)

        ty=h-1.82*inch
        p.setFillColorRGB(*EW); p.rect(.55*inch,ty,7.40*inch,.28*inch,fill=1,stroke=0)
        p.setFillColorRGB(1,1,1); p.setFont('Helvetica-Bold',8.4); p.drawString(.68*inch,ty+.09*inch,'CURRENT INVOICE CHARGES'); p.setFillColorRGB(0,0,0)
        ty-=.28*inch
        p.setFont('Helvetica-Bold',6.8); p.setFillColorRGB(*GRAY); p.drawString(.68*inch,ty,'DESCRIPTION'); p.drawRightString(6.35*inch,ty,'QTY'); p.drawRightString(7.02*inch,ty,'RATE'); p.drawRightString(7.78*inch,ty,'AMOUNT'); p.setFillColorRGB(0,0,0)
        ty-=.12*inch; line(.65*inch,ty,7.80*inch,ty,.45); ty-=.18*inch
        p.setFont('Helvetica',7.8)
        if items:
            for it in items:
                if ty < 4.75*inch: break
                p.drawString(.68*inch,ty,(it['description'] or 'Service charge')[:70]); p.drawRightString(6.35*inch,ty,f"{float(it['qty'] or 0):g}"); p.drawRightString(7.02*inch,ty,money(it['unit_price'])); p.drawRightString(7.78*inch,ty,money(it['amount'])); ty-=.20*inch
        else:
            p.drawString(.68*inch,ty,'No line-item charges on this invoice.'); ty-=.20*inch
        ty-=.04*inch; line(5.55*inch,ty,7.80*inch,ty,.6,DARK); ty-=.18*inch
        p.setFont('Helvetica-Bold',8.3); p.drawString(5.58*inch,ty,'New Charges'); p.drawRightString(7.78*inch,ty,money(current_charges)); ty-=.20*inch
        p.drawString(5.58*inch,ty,'Payments/Credits'); p.drawRightString(7.78*inch,ty,money(-current_paid)); ty-=.20*inch
        p.setFillColorRGB(*EW); p.drawString(5.58*inch,ty,'Invoice Balance'); p.drawRightString(7.78*inch,ty,money(current_balance)); p.setFillColorRGB(0,0,0)

        # Service/account information.
        iy=4.30*inch
        p.setFillColorRGB(*DARK); p.setFont('Helvetica-Bold',8.7); p.drawString(.60*inch,iy,'ACCOUNT & SERVICE INFORMATION'); iy-=.16*inch; line(.60*inch,iy,7.80*inch,iy,.55,DARK); iy-=.20*inch
        info=[('Customer',customer_name),('Account Number',inv['account_no']),('Customer Type',inv['customer_type'] or 'Residential'),('Service Plan',plan_name),('Service Address',f'{service_address or bill_address} {city_state_zip}'.strip()),('Phone',inv['phone'] or ''),('Email',inv['email'] or '')]
        for lab,val in info:
            p.setFont('Helvetica-Bold',7.1); p.drawString(.68*inch,iy,lab+':'); p.setFont('Helvetica',7.3); p.drawString(1.65*inch,iy,str(val)[:88]); iy-=.18*inch

        # Billing information / rights, replacing the reference's industry-specific back page.
        by=2.66*inch
        p.setFillColorRGB(*EW); p.rect(.55*inch,by,7.40*inch,.28*inch,fill=1,stroke=0)
        p.setFillColorRGB(1,1,1); p.setFont('Helvetica-Bold',8.4); p.drawString(.68*inch,by+.09*inch,'IMPORTANT BILLING INFORMATION'); p.setFillColorRGB(0,0,0)
        by-=.25*inch
        notices=[
            f'PAYMENTS. Pay online through {PUBLIC_URL}/portal. Keep your account number available when contacting support about a payment.',
            f'PAST-DUE ACCOUNTS. Accounts that remain unpaid {SUSPEND_AFTER_DAYS} days after the due date may be subject to service suspension in accordance with the service agreement and applicable law.',
            f'RECONNECTION. When service is restored following a nonpayment suspension, a {money(RECONNECT_FEE)} reconnect fee may be added to a subsequent invoice.',
            f'BILLING QUESTIONS. If you believe a charge is incorrect or need more information, contact {SUPPORT_EMAIL} or {COMPANY_PHONE} and include your account and invoice numbers.',
            f'CUSTOMER PORTAL. Statements, account information, and available payment options can be viewed at {PUBLIC_URL}/portal.',
            f'{COMPANY_DBA} is operated by {COMPANY_DISPLAY_LEGAL}.'
        ]
        p.setFont('Helvetica',6.9); p.setFillColorRGB(*DARK)
        for notice in notices:
            lines=_wrap_pdf_text(notice,116)
            for t in lines: p.drawString(.68*inch,by,t); by-=.13*inch
            by-=.07*inch
        p.setFillColorRGB(0,0,0)
        p.save()
        c.execute("UPDATE invoices SET pdf_path=? WHERE id=?",(str(path),iid))
        return path

def _wrap_pdf_text(text, width=60):
    words=text.split(); lines=[]; cur=[]; n=0
    for word in words:
        if n+len(word)+1>width and cur: lines.append(' '.join(cur)); cur=[word]; n=len(word)
        else: cur.append(word); n+=len(word)+1
    if cur: lines.append(' '.join(cur))
    return lines

def generate_past_due_notice(iid):
    with conn() as c:
        inv=c.execute("""SELECT i.*,c.account_no,c.first_name,c.last_name,c.company,c.email,c.service_address,c.billing_address,c.city,c.state,c.zip FROM invoices i JOIN customers c ON c.id=i.customer_id WHERE i.id=?""",(iid,)).fetchone()
        if not inv: raise ValueError("Invoice not found")
        balance=max(0,float(inv['subtotal'])-float(inv['amount_paid'] or 0))
        path=STATEMENTS / f"{inv['invoice_no']}-PAST-DUE-NOTICE.pdf"
        p=canvas.Canvas(str(path),pagesize=letter); w,h=letter
        logo=BASE/'entire_wireless_logo.png'
        if logo.exists(): p.drawImage(str(logo),.6*inch,h-1.05*inch,width=1.8*inch,height=.68*inch,preserveAspectRatio=True,mask='auto')
        p.setFont('Helvetica-Bold',9); p.drawRightString(w-.6*inch,h-.48*inch,COMPANY_DISPLAY_LEGAL)
        p.setFont('Helvetica',8); p.drawRightString(w-.6*inch,h-.68*inch,COMPANY_ADDRESS); p.drawRightString(w-.6*inch,h-.86*inch,f'{COMPANY_PHONE} · {SUPPORT_EMAIL}')
        p.setFillColorRGB(184/255,59/255,50/255); p.setFont('Helvetica-Bold',20); p.drawString(.7*inch,h-1.65*inch,'PAST DUE NOTICE'); p.setFillColorRGB(0,0,0)
        name=inv['company'] or f"{inv['first_name']} {inv['last_name']}"
        y=h-2.1*inch; p.setFont('Helvetica',10)
        for line in [name, inv['billing_address'] or inv['service_address'] or '', f"{inv['city'] or ''}, {inv['state'] or ''} {inv['zip'] or ''}"]:
            if line.strip(): p.drawString(.7*inch,y,line); y-=.2*inch
        y-=.2*inch; p.setFont('Helvetica-Bold',10); p.drawString(.7*inch,y,'Account Number'); p.drawString(2.35*inch,y,inv['account_no']); y-=.25*inch
        p.drawString(.7*inch,y,'Invoice Number'); p.drawString(2.35*inch,y,inv['invoice_no']); y-=.25*inch
        p.drawString(.7*inch,y,'Original Due Date'); p.drawString(2.35*inch,y,inv['due_date']); y-=.25*inch
        p.setFillColorRGB(184/255,59/255,50/255); p.drawString(.7*inch,y,'PAST DUE BALANCE'); p.drawRightString(w-.7*inch,y,money(balance)); p.setFillColorRGB(0,0,0); y-=.5*inch
        p.setFont('Helvetica',10); text=p.beginText(.7*inch,y); text.setLeading(14)
        body=(f'Our records show that payment for the invoice above was not received by the close of business on its due date. '
              f'Please pay the past-due balance promptly through the customer portal at {PUBLIC_URL}/portal or contact us at {COMPANY_PHONE}. '
              f'Accounts that remain unpaid may be subject to collection activity and, after the configured grace period, service suspension in accordance with your service agreement and applicable law.')
        for line in _wrap_pdf_text(body,88): text.textLine(line)
        text.textLine(''); text.textLine(f'This notice is from {COMPANY_DISPLAY_LEGAL}.')
        p.drawText(text)
        p.setFont('Helvetica',7.5); p.drawString(.7*inch,.65*inch,f'{COMPANY_DISPLAY_LEGAL} · {COMPANY_SITE} · {SUPPORT_EMAIL}')
        p.save(); c.execute('UPDATE invoices SET eod_notice_pdf=? WHERE id=?',(str(path),iid)); return path

def send_eod_past_due_notice(iid):
    with conn() as c:
        inv=c.execute("""SELECT i.*,c.email,c.first_name,c.account_no FROM invoices i JOIN customers c ON c.id=i.customer_id WHERE i.id=?""",(iid,)).fetchone()
        if not inv or not inv['email'] or inv['eod_notice_at']: return False
        if float(inv['subtotal'])-float(inv['amount_paid'] or 0) <= .005: return False
    path=generate_past_due_notice(iid); balance=float(inv['subtotal'])-float(inv['amount_paid'] or 0)
    subject=f"Past Due Notice — {inv['invoice_no']}"
    body=f"Hello {inv['first_name']},\n\nOur records show payment was not received by the close of business on the due date for invoice {inv['invoice_no']}.\nAccount: {inv['account_no']}\nPast-due balance: {money(balance)}\nOriginal due date: {inv['due_date']}\n\nYour formal past-due notice is attached. You may review your account and payment options at {PUBLIC_URL}/portal.\n\n{COMPANY_DISPLAY_LEGAL}\n{SUPPORT_EMAIL}\n{COMPANY_PHONE}"
    ok=smtp_send(inv['email'],subject,body,path)
    if ok:
        with conn() as c: c.execute('UPDATE invoices SET eod_notice_at=?,last_reminder_at=? WHERE id=?',(business_now().isoformat(timespec='seconds'),business_now().isoformat(timespec='seconds'),iid))
    return ok

def run_eod_due_notices(force=False):
    now=business_now()
    if not force and now.hour < BUSINESS_CLOSE_HOUR: return 0
    with conn() as c:
        rows=c.execute("SELECT id FROM invoices WHERE due_date<=? AND status NOT IN ('Paid','Void') AND (subtotal-amount_paid)>.005 AND eod_notice_at IS NULL",(now.date().isoformat(),)).fetchall()
        ids=[r['id'] for r in rows]
        for iid in ids: update_invoice_status(c,iid)
    sent=0
    for iid in ids:
        try:
            if send_eod_past_due_notice(iid): sent+=1
        except Exception as e: print('EOD past due notice error:',e)
    return sent

def smtp_send(to_email, subject, body, attachment=None):
    host=os.getenv('SMTP_HOST'); port=int(os.getenv('SMTP_PORT','587')); user=os.getenv('SMTP_USER'); password=os.getenv('SMTP_PASSWORD'); sender=os.getenv('SMTP_FROM',SUPPORT_EMAIL)
    if not all([host,user,password,to_email]): return False
    msg=EmailMessage(); msg['From']=sender; msg['To']=to_email; msg['Subject']=subject; msg.set_content(body)
    if attachment and Path(attachment).exists(): msg.add_attachment(Path(attachment).read_bytes(),maintype='application',subtype='pdf',filename=Path(attachment).name)
    with smtplib.SMTP(host,port,timeout=25) as s:
        s.starttls(); s.login(user,password); s.send_message(msg)
    return True

def email_statement(iid, reminder=False):
    with conn() as c:
        inv=c.execute('''SELECT i.*,c.email,c.first_name,c.account_no FROM invoices i JOIN customers c ON c.id=i.customer_id WHERE i.id=?''',(iid,)).fetchone()
        if not inv or not inv['email']: return False
    path=generate_statement(iid); balance=inv['subtotal']-inv['amount_paid']
    subj=("Past Due Reminder" if reminder else "Billing Statement")+f" — {inv['invoice_no']}"
    body=f"Hello {inv['first_name']},\n\nYour {COMPANY_NAME} {'past-due reminder' if reminder else 'billing statement'} is attached.\nAccount: {inv['account_no']}\nInvoice: {inv['invoice_no']}\nBalance due: {money(balance)}\nDue date: {inv['due_date']}\n\nCustomer portal: {PUBLIC_URL}/portal\n\n{COMPANY_DISPLAY_LEGAL}\n{SUPPORT_EMAIL}"
    ok=smtp_send(inv['email'],subj,body,path)
    if ok:
        with conn() as c:
            c.execute("UPDATE invoices SET emailed_at=COALESCE(emailed_at,?),last_reminder_at=? WHERE id=?",(datetime.now().isoformat(timespec='seconds'),datetime.now().isoformat(timespec='seconds') if reminder else inv['last_reminder_at'],iid))
    return ok

def _qb_log(entity_type, entity_id, action, status, quickbooks_id='', error=''):
    with conn() as c:
        c.execute("INSERT INTO quickbooks_sync_log(entity_type,entity_id,action,status,quickbooks_id,error) VALUES (?,?,?,?,?,?)",(entity_type,entity_id,action,status,quickbooks_id,error[:2000] if error else ''))

def _qb_oauth():
    with conn() as c: return c.execute("SELECT * FROM quickbooks_oauth WHERE id=1").fetchone()

def _qb_token_request(data):
    raw=urllib.parse.urlencode(data).encode()
    auth=base64.b64encode(f"{QUICKBOOKS_CLIENT_ID}:{QUICKBOOKS_CLIENT_SECRET}".encode()).decode()
    req=urllib.request.Request(QB_TOKEN_URL,data=raw,headers={'Authorization':f'Basic {auth}','Accept':'application/json','Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req,timeout=30) as r: return json.loads(r.read().decode())

def _qb_store_tokens(tok, realm_id=None):
    now=datetime.utcnow(); access_exp=now+timedelta(seconds=int(tok.get('expires_in',3600))-60); refresh_exp=now+timedelta(seconds=int(tok.get('x_refresh_token_expires_in',8726400))-300)
    old=_qb_oauth(); realm_id=realm_id or (old['realm_id'] if old else '')
    refresh=tok.get('refresh_token') or (old['refresh_token'] if old else '')
    with conn() as c:
        c.execute("INSERT INTO quickbooks_oauth(id,realm_id,access_token,refresh_token,access_expires_at,refresh_expires_at,connected_at,updated_at) VALUES (1,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET realm_id=excluded.realm_id,access_token=excluded.access_token,refresh_token=excluded.refresh_token,access_expires_at=excluded.access_expires_at,refresh_expires_at=excluded.refresh_expires_at,updated_at=excluded.updated_at",(realm_id,tok.get('access_token',''),refresh,access_exp.isoformat(),refresh_exp.isoformat(),now.isoformat(),now.isoformat()))

def _qb_access_token():
    row=_qb_oauth()
    if not row or not row['refresh_token']: raise RuntimeError('QuickBooks is not connected.')
    try: exp=datetime.fromisoformat(row['access_expires_at'])
    except Exception: exp=datetime.min
    if row['access_token'] and exp > datetime.utcnow()+timedelta(seconds=30): return row['access_token'],row['realm_id']
    tok=_qb_token_request({'grant_type':'refresh_token','refresh_token':row['refresh_token']}); _qb_store_tokens(tok,row['realm_id']); return tok['access_token'],row['realm_id']

def _qb_request_id(kind, entity_id):
    # Stable per CRM entity/environment. Intuit uses requestid to make create retries idempotent.
    raw=f"entire-wireless:{QUICKBOOKS_ENVIRONMENT}:{kind}:{entity_id}".encode()
    return hashlib.sha256(raw).hexdigest()[:40]

def _qb_api(method, path, payload=None, request_id=None):
    token,realm=_qb_access_token()
    if request_id:
        sep='&' if '?' in path else '?'
        path=f"{path}{sep}requestid={urllib.parse.quote(str(request_id), safe='')}"
    url=f"{QB_API_BASE}/v3/company/{realm}/{path}"
    data=json.dumps(payload).encode() if payload is not None else None
    last=None
    attempts=QB_API_RETRIES if (method.upper()=='GET' or request_id) else 1
    for attempt in range(attempts):
        req=urllib.request.Request(url,data=data,method=method,headers={'Authorization':f'Bearer {token}','Accept':'application/json','Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=QB_API_TIMEOUT) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body=e.read().decode(errors='replace')
            # Authentication can expire between token lookup and the API call. Refresh once.
            if e.code==401 and attempt+1 < attempts:
                row=_qb_oauth()
                if row and row['refresh_token']:
                    tok=_qb_token_request({'grant_type':'refresh_token','refresh_token':row['refresh_token']})
                    _qb_store_tokens(tok,row['realm_id'])
                    token=tok['access_token']
                    continue
            raise RuntimeError(f'QuickBooks API {e.code}: {body[:1500]}')
        except (TimeoutError, OSError) as e:
            last=e
            if attempt+1 >= attempts:
                raise RuntimeError(f'QuickBooks API timed out after {QB_API_TIMEOUT}s ({attempts} attempt(s)): {e}')
            time.sleep(2)
    raise RuntimeError(f'QuickBooks API request failed: {last}')

def _qb_query(q): return _qb_api('GET','query?query='+urllib.parse.quote(q,safe=''))
def _qb_escape(v): return str(v or '').replace("'","\\'")

def qb_sync_customer(cid):
    if not QUICKBOOKS_ENABLED: return None
    with conn() as c: cust=c.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone()
    if not cust: raise RuntimeError('Customer not found')
    if cust['quickbooks_customer_id']: return cust['quickbooks_customer_id']
    display=(cust['company'] or f"{cust['first_name']} {cust['last_name']}").strip()
    q=_qb_query(f"select * from Customer where DisplayName = '{_qb_escape(display)}' maxresults 10")
    found=(q.get('QueryResponse',{}).get('Customer') or [])
    if found: qid=str(found[0]['Id'])
    else:
        payload={'DisplayName':display,'GivenName':cust['first_name'],'FamilyName':cust['last_name']}
        if cust['company']: payload['CompanyName']=cust['company']
        if cust['email']: payload['PrimaryEmailAddr']={'Address':cust['email']}
        if cust['phone']: payload['PrimaryPhone']={'FreeFormNumber':cust['phone']}
        if cust['service_address']:
            payload['BillAddr']={'Line1':cust['service_address'],'City':cust['city'] or '','CountrySubDivisionCode':cust['state'] or '','PostalCode':cust['zip'] or ''}
        qid=str(_qb_api('POST','customer',payload,request_id=_qb_request_id('customer',cid))['Customer']['Id'])
    with conn() as c: c.execute("UPDATE customers SET quickbooks_customer_id=?,quickbooks_sync_status='Synced',quickbooks_sync_error=NULL,quickbooks_synced_at=? WHERE id=?",(qid,datetime.utcnow().isoformat(),cid))
    _qb_log('customer',cid,'sync','Synced',qid); return qid

def _qb_service_item():
    name='Entire Wireless Services'; q=_qb_query(f"select * from Item where Name = '{name}' maxresults 1"); rows=q.get('QueryResponse',{}).get('Item') or []
    if rows: return str(rows[0]['Id'])
    aq=_qb_query("select * from Account where AccountType = 'Income' maxresults 1"); accts=aq.get('QueryResponse',{}).get('Account') or []
    if not accts: raise RuntimeError('QuickBooks has no Income account available for the service item.')
    payload={'Name':name,'Type':'Service','IncomeAccountRef':{'value':str(accts[0]['Id'])}}
    return str(_qb_api('POST','item',payload,request_id=_qb_request_id('service-item',1))['Item']['Id'])

def qb_sync_invoice(iid):
    if not QUICKBOOKS_ENABLED: return None
    with conn() as c:
        inv=c.execute("SELECT * FROM invoices WHERE id=?",(iid,)).fetchone(); items=c.execute("SELECT * FROM invoice_items WHERE invoice_id=? ORDER BY id",(iid,)).fetchall()
    if not inv: raise RuntimeError('Invoice not found')
    if inv['quickbooks_invoice_id']: return inv['quickbooks_invoice_id']
    qcid=qb_sync_customer(inv['customer_id'])
    # Recover safely if QuickBooks accepted an earlier create but the CRM timed out before receiving it.
    existing=_qb_query(f"select * from Invoice where DocNumber = '{_qb_escape(inv['invoice_no'])}' maxresults 10")
    found=(existing.get('QueryResponse',{}).get('Invoice') or [])
    if found:
        qid=str(found[0]['Id'])
    else:
        item_id=_qb_service_item(); lines=[]
        for x in items:
            lines.append({'Amount':round(float(x['amount']),2),'DetailType':'SalesItemLineDetail','Description':x['description'],'SalesItemLineDetail':{'ItemRef':{'value':item_id},'Qty':float(x['qty'] or 1),'UnitPrice':float(x['unit_price'])}})
        payload={'CustomerRef':{'value':qcid},'TxnDate':inv['issue_date'],'DueDate':inv['due_date'],'DocNumber':inv['invoice_no'],'PrivateNote':f"Entire Wireless CRM invoice #{iid}",'Line':lines}
        qid=str(_qb_api('POST','invoice',payload,request_id=_qb_request_id('invoice',iid))['Invoice']['Id'])
    with conn() as c: c.execute("UPDATE invoices SET quickbooks_invoice_id=?,quickbooks_sync_status='Synced',quickbooks_sync_error=NULL,quickbooks_synced_at=? WHERE id=?",(qid,datetime.utcnow().isoformat(),iid))
    _qb_log('invoice',iid,'sync','Synced',qid); return qid

def qb_sync_payment(pid):
    if not QUICKBOOKS_ENABLED: return None
    with conn() as c: pay=c.execute("SELECT * FROM payments WHERE id=?",(pid,)).fetchone()
    if not pay: raise RuntimeError('Payment not found')
    if pay['quickbooks_payment_id']: return pay['quickbooks_payment_id']
    qcid=qb_sync_customer(pay['customer_id']); qinv=qb_sync_invoice(pay['invoice_id']) if pay['invoice_id'] else None
    payload={'CustomerRef':{'value':qcid},'TotalAmt':round(float(pay['amount']),2),'TxnDate':pay['payment_date'],'PrivateNote':f"Entire Wireless CRM payment #{pid}"}
    if qinv: payload['Line']=[{'Amount':round(float(pay['amount']),2),'LinkedTxn':[{'TxnId':qinv,'TxnType':'Invoice'}]}]
    qid=str(_qb_api('POST','payment',payload,request_id=_qb_request_id('payment',pid))['Payment']['Id'])
    with conn() as c: c.execute("UPDATE payments SET quickbooks_payment_id=?,quickbooks_sync_status='Synced',quickbooks_sync_error=NULL,quickbooks_synced_at=? WHERE id=?",(qid,datetime.utcnow().isoformat(),pid))
    _qb_log('payment',pid,'sync','Synced',qid); return qid

def qb_try(entity, entity_id):
    if not QUICKBOOKS_ENABLED: return
    try:
        {'customer':qb_sync_customer,'invoice':qb_sync_invoice,'payment':qb_sync_payment}[entity](entity_id)
    except Exception as e:
        table={'customer':'customers','invoice':'invoices','payment':'payments'}[entity]
        with conn() as c: c.execute(f"UPDATE {table} SET quickbooks_sync_status='Failed',quickbooks_sync_error=? WHERE id=?",(str(e)[:2000],entity_id))
        _qb_log(entity,entity_id,'sync','Failed','',str(e))

# ---------------- Zoho Books integration (V9) ----------------
def _zoho_log(entity_type, entity_id, action, status, zoho_id='', error=''):
    with conn() as c:
        c.execute("INSERT INTO zoho_sync_log(entity_type,entity_id,action,status,zoho_id,error) VALUES (?,?,?,?,?,?)",(entity_type,entity_id,action,status,zoho_id,error[:2000] if error else ''))

def _zoho_oauth():
    with conn() as c: return c.execute("SELECT * FROM zoho_oauth WHERE id=1").fetchone()

def _zoho_token_request(data):
    payload=dict(data)
    payload['client_id']=ZOHO_CLIENT_ID
    payload['client_secret']=ZOHO_CLIENT_SECRET
    req=urllib.request.Request(ZOHO_ACCOUNTS_BASE+'/oauth/v2/token',data=urllib.parse.urlencode(payload).encode(),method='POST')
    try:
        with urllib.request.urlopen(req,timeout=ZOHO_API_TIMEOUT) as r: out=json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body=e.read().decode(errors='replace')
        raise RuntimeError(f"Zoho token error HTTP {e.code}: {body[:1000]}")
    if out.get('error'): raise RuntimeError('Zoho token error: '+str(out.get('error')))
    return out

def _zoho_store_tokens(tok, organization_id=None, organization_name=None):
    old=_zoho_oauth(); now=datetime.utcnow(); expires=int(tok.get('expires_in') or 3600)
    refresh=tok.get('refresh_token') or (old['refresh_token'] if old else '')
    api_domain=(tok.get('api_domain') or (old['api_domain'] if old else '') or ZOHO_API_DOMAIN).rstrip('/')
    oid=organization_id if organization_id is not None else (old['organization_id'] if old else '')
    oname=organization_name if organization_name is not None else (old['organization_name'] if old else '')
    connected=(old['connected_at'] if old and old['connected_at'] else now.isoformat())
    with conn() as c:
        c.execute("INSERT INTO zoho_oauth(id,organization_id,organization_name,access_token,refresh_token,access_expires_at,api_domain,connected_at,updated_at) VALUES (1,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET organization_id=excluded.organization_id,organization_name=excluded.organization_name,access_token=excluded.access_token,refresh_token=excluded.refresh_token,access_expires_at=excluded.access_expires_at,api_domain=excluded.api_domain,updated_at=excluded.updated_at",(oid,oname,tok.get('access_token',''),refresh,(now+timedelta(seconds=max(60,expires-60))).isoformat(),api_domain,connected,now.isoformat()))

def _zoho_access_token():
    row=_zoho_oauth()
    if not row or not row['access_token']: raise RuntimeError('Zoho Books is not connected.')
    try: exp=datetime.fromisoformat(row['access_expires_at'])
    except Exception: exp=datetime.utcnow()-timedelta(seconds=1)
    if datetime.utcnow() < exp: return row['access_token'],row['organization_id'],(row['api_domain'] or ZOHO_API_DOMAIN).rstrip('/')
    if not row['refresh_token']: raise RuntimeError('Zoho refresh token is missing. Reconnect Zoho Books.')
    tok=_zoho_token_request({'grant_type':'refresh_token','refresh_token':row['refresh_token']})
    _zoho_store_tokens(tok,row['organization_id'],row['organization_name'])
    row=_zoho_oauth(); return row['access_token'],row['organization_id'],(row['api_domain'] or ZOHO_API_DOMAIN).rstrip('/')

def _zoho_api(method, path, payload=None, params=None, require_org=True):
    token,org,domain=_zoho_access_token()
    params=dict(params or {})
    if require_org:
        if not org: raise RuntimeError('Zoho Books organization is not selected.')
        params['organization_id']=org
    url=domain+'/books/v3/'+path.lstrip('/')
    if params: url += ('&' if '?' in url else '?')+urllib.parse.urlencode(params)
    data=None if payload is None else json.dumps(payload).encode()
    headers={'Authorization':'Zoho-oauthtoken '+token,'Accept':'application/json'}
    if data is not None: headers['Content-Type']='application/json'
    last=None
    for attempt in range(ZOHO_API_RETRIES):
        req=urllib.request.Request(url,data=data,headers=headers,method=method.upper())
        try:
            with urllib.request.urlopen(req,timeout=ZOHO_API_TIMEOUT) as r:
                body=r.read().decode()
                out=json.loads(body) if body else {}
                if isinstance(out,dict) and out.get('code') not in (None,0): raise RuntimeError(f"Zoho API error {out.get('code')}: {out.get('message','Unknown error')}")
                return out
        except urllib.error.HTTPError as e:
            body=e.read().decode(errors='replace')
            if e.code==401 and attempt==0:
                row=_zoho_oauth()
                if row and row['refresh_token']:
                    tok=_zoho_token_request({'grant_type':'refresh_token','refresh_token':row['refresh_token']}); _zoho_store_tokens(tok,row['organization_id'],row['organization_name'])
                    token,org,domain=_zoho_access_token(); headers['Authorization']='Zoho-oauthtoken '+token
                    continue
            if e.code in (429,500,502,503,504) and attempt+1<ZOHO_API_RETRIES:
                time.sleep(1.5*(attempt+1)); last=RuntimeError(f"Zoho API HTTP {e.code}: {body[:1000]}"); continue
            raise RuntimeError(f"Zoho API HTTP {e.code}: {body[:1000]}")
        except Exception as e:
            last=e
            if attempt+1<ZOHO_API_RETRIES: time.sleep(1.5*(attempt+1)); continue
            raise
    raise last or RuntimeError('Zoho API request failed.')

def _zoho_find_contact(cust):
    # Prefer email when present, then exact contact-name match.
    if cust['email']:
        out=_zoho_api('GET','contacts',params={'email':cust['email'],'contact_type':'customer'})
        for x in out.get('contacts') or []:
            if str(x.get('email','')).lower()==str(cust['email']).lower(): return str(x['contact_id'])
    display=(cust['company'] or f"{cust['first_name']} {cust['last_name']}").strip()
    out=_zoho_api('GET','contacts',params={'contact_name':display,'contact_type':'customer'})
    for x in out.get('contacts') or []:
        if str(x.get('contact_name','')).strip().lower()==display.lower(): return str(x['contact_id'])
    return None

def zoho_sync_customer(cid):
    if not ZOHO_ENABLED: return None
    with conn() as c: cust=c.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone()
    if not cust: raise RuntimeError('CRM customer not found.')
    if cust['zoho_contact_id']: return cust['zoho_contact_id']
    zid=_zoho_find_contact(cust)
    if not zid:
        display=(cust['company'] or f"{cust['first_name']} {cust['last_name']}").strip()
        addr={'address':cust['service_address'] or cust['billing_address'] or '','city':cust['city'] or '','state':cust['state'] or '','zip':cust['zip'] or '','country':'USA','phone':cust['phone'] or ''}
        payload={'contact_name':display,'company_name':cust['company'] or '','contact_type':'customer','notes':f"Entire Wireless CRM account {cust['account_no']}",'billing_address':addr}
        if cust['email'] or cust['phone'] or cust['first_name'] or cust['last_name']:
            payload['contact_persons']=[{'first_name':cust['first_name'] or '','last_name':cust['last_name'] or '','email':cust['email'] or '','phone':cust['phone'] or '','is_primary_contact':True}]
        zid=str(_zoho_api('POST','contacts',payload).get('contact',{}).get('contact_id') or '')
        if not zid: raise RuntimeError('Zoho did not return a contact ID.')
    with conn() as c: c.execute("UPDATE customers SET zoho_contact_id=?,zoho_sync_status='Synced',zoho_sync_error=NULL,zoho_synced_at=? WHERE id=?",(zid,datetime.utcnow().isoformat(),cid))
    _zoho_log('customer',cid,'sync','Synced',zid); return zid

def zoho_update_customer(cid):
    if not ZOHO_ENABLED: return None
    with conn() as c: cust=c.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone()
    if not cust: raise RuntimeError('CRM customer not found.')
    if not cust['zoho_contact_id']:
        return zoho_sync_customer(cid)
    zid=str(cust['zoho_contact_id'])
    display=(cust['company'] or f"{cust['first_name']} {cust['last_name']}").strip()
    addr={'address':cust['billing_address'] or cust['service_address'] or '', 'city':cust['city'] or '', 'state':cust['state'] or '', 'zip':cust['zip'] or '', 'country':'USA', 'phone':cust['phone'] or ''}
    payload={'contact_name':display,'company_name':cust['company'] or '','contact_type':'customer','notes':f"Entire Wireless CRM account {cust['account_no']}",'billing_address':addr}
    if cust['email'] or cust['phone'] or cust['first_name'] or cust['last_name']:
        payload['contact_persons']=[{'first_name':cust['first_name'] or '','last_name':cust['last_name'] or '','email':cust['email'] or '','phone':cust['phone'] or '','is_primary_contact':True}]
    out=_zoho_api('PUT',f'contacts/{zid}',payload)
    returned=str((out.get('contact') or {}).get('contact_id') or zid)
    with conn() as c: c.execute("UPDATE customers SET zoho_sync_status='Synced',zoho_sync_error=NULL,zoho_synced_at=? WHERE id=?",(datetime.utcnow().isoformat(),cid))
    _zoho_log('customer',cid,'update','Synced',returned)
    return returned

def _zoho_service_item():
    name='Entire Wireless Services'
    out=_zoho_api('GET','items',params={'name':name})
    for x in out.get('items') or []:
        if str(x.get('name','')).strip().lower()==name.lower(): return str(x['item_id'])
    created=_zoho_api('POST','items',{'name':name,'rate':0.0,'description':'Entire Wireless internet and telecommunications services','product_type':'service'})
    zid=str(created.get('item',{}).get('item_id') or '')
    if not zid: raise RuntimeError('Zoho did not return an item ID.')
    return zid

def _zoho_find_invoice(invoice_no):
    out=_zoho_api('GET','invoices',params={'invoice_number':invoice_no})
    for x in out.get('invoices') or []:
        if str(x.get('invoice_number','')).strip().lower()==str(invoice_no).strip().lower(): return str(x['invoice_id'])
    return None

def zoho_sync_invoice(iid):
    if not ZOHO_ENABLED: return None
    with conn() as c:
        inv=c.execute("SELECT * FROM invoices WHERE id=?",(iid,)).fetchone(); lines=c.execute("SELECT * FROM invoice_items WHERE invoice_id=? ORDER BY id",(iid,)).fetchall()
    if not inv: raise RuntimeError('CRM invoice not found.')
    if inv['status']=='Void': return None
    if inv['zoho_invoice_id']: return inv['zoho_invoice_id']
    zcid=zoho_sync_customer(inv['customer_id'])
    zid=_zoho_find_invoice(inv['invoice_no'])
    if not zid:
        item_id=_zoho_service_item()
        zlines=[]
        promo_waiver=next((x for x in lines if float(x['unit_price'] or 0)<0 and 'Modem Rental Promotion' in str(x['description'] or '')),None)
        for x in lines:
            desc=str(x['description'] or 'Entire Wireless Services')
            rate=round(float(x['unit_price'] or 0),2)
            if promo_waiver and desc=='Monthly Modem Device Lease':
                promo_desc=str(promo_waiver['description'] or 'Modem Rental Promotion')
                zlines.append({'item_id':item_id,'name':'Monthly Modem Device Lease'[:100],'description':f"{promo_desc} — regular device lease waived this billing cycle"[:2000],'quantity':float(x['qty'] or 1),'rate':0.0})
                continue
            if promo_waiver and x['id']==promo_waiver['id']:
                continue
            zlines.append({'item_id':item_id,'name':desc[:100],'description':desc[:2000],'quantity':float(x['qty'] or 1),'rate':rate})
        if not zlines: zlines=[{'item_id':item_id,'description':'Entire Wireless Services','quantity':1,'rate':round(float(inv['subtotal'] or 0),2)}]
        payload={'customer_id':zcid,'invoice_number':inv['invoice_no'],'date':inv['issue_date'],'due_date':inv['due_date'],'reference_number':f"CRM invoice {iid}",'line_items':zlines,'notes':'Generated by Entire Wireless ISP CRM'}
        out=_zoho_api('POST','invoices',payload,params={'ignore_auto_number_generation':'true','send':'false'})
        zid=str(out.get('invoice',{}).get('invoice_id') or '')
        if not zid:
            # A timeout may happen after Zoho commits the invoice. Re-query before failing.
            zid=_zoho_find_invoice(inv['invoice_no']) or ''
        if not zid: raise RuntimeError('Zoho did not return an invoice ID.')
    with conn() as c: c.execute("UPDATE invoices SET zoho_invoice_id=?,zoho_sync_status='Synced',zoho_sync_error=NULL,zoho_synced_at=? WHERE id=?",(zid,datetime.utcnow().isoformat(),iid))
    _zoho_log('invoice',iid,'sync','Synced',zid); return zid

def _zoho_payment_mode(method):
    m=(method or '').strip().lower()
    if 'check' in m: return 'check'
    if 'cash' in m: return 'cash'
    if 'credit' in m or 'card' in m: return 'creditcard'
    if 'bank' in m or 'ach' in m: return 'banktransfer'
    if 'auto' in m: return 'autotransaction'
    return 'others'

def _zoho_find_payment(pay, invoice_id):
    # Use CRM payment ID as a stable reference number to prevent duplicates after ambiguous timeouts.
    ref=f"EWCRM-PAY-{pay['id']}"
    out=_zoho_api('GET','customerpayments',params={'reference_number':ref})
    for x in out.get('customerpayments') or []:
        if str(x.get('reference_number','')).strip()==ref: return str(x.get('payment_id') or '')
    return None

def zoho_sync_payment(pid):
    if not ZOHO_ENABLED: return None
    with conn() as c: pay=c.execute("SELECT * FROM payments WHERE id=?",(pid,)).fetchone()
    if not pay: raise RuntimeError('CRM payment not found.')
    if pay['zoho_payment_id']: return pay['zoho_payment_id']
    zcid=zoho_sync_customer(pay['customer_id']); zinv=zoho_sync_invoice(pay['invoice_id']) if pay['invoice_id'] else None
    if not zinv: raise RuntimeError('Zoho payment sync requires a synced invoice.')
    zid=_zoho_find_payment(pay,zinv)
    if not zid:
        ref=f"EWCRM-PAY-{pid}"
        payload={'customer_id':zcid,'payment_mode':_zoho_payment_mode(pay['method']),'amount':round(float(pay['amount']),2),'date':pay['payment_date'],'reference_number':ref,'description':f"Entire Wireless CRM payment {pid}. {pay['reference'] or ''}".strip(),'invoices':[{'invoice_id':zinv,'amount_applied':round(float(pay['amount']),2)}]}
        out=_zoho_api('POST','customerpayments',payload)
        zid=str(out.get('payment',{}).get('payment_id') or '')
        if not zid: zid=_zoho_find_payment(pay,zinv) or ''
        if not zid: raise RuntimeError('Zoho did not return a payment ID.')
    with conn() as c: c.execute("UPDATE payments SET zoho_payment_id=?,zoho_sync_status='Synced',zoho_sync_error=NULL,zoho_synced_at=? WHERE id=?",(zid,datetime.utcnow().isoformat(),pid))
    _zoho_log('payment',pid,'sync','Synced',zid); return zid

def zoho_try(entity, entity_id):
    if not ZOHO_ENABLED: return
    try:
        {'customer':zoho_sync_customer,'invoice':zoho_sync_invoice,'payment':zoho_sync_payment}[entity](entity_id)
    except Exception as e:
        table={'customer':'customers','invoice':'invoices','payment':'payments'}[entity]
        with conn() as c: c.execute(f"UPDATE {table} SET zoho_sync_status='Failed',zoho_sync_error=? WHERE id=?",(str(e)[:2000],entity_id))
        _zoho_log(entity,entity_id,'sync','Failed','',str(e))

def accounting_try(entity, entity_id):
    if ACCOUNTING_PROVIDER=='zoho': zoho_try(entity,entity_id)
    elif ACCOUNTING_PROVIDER=='quickbooks': qb_try(entity,entity_id)

def create_invoice(customer_id, items, issue=None, due=None, prefix='INV'):
    issue=issue or date.today(); due=due or issue+timedelta(days=15); subtotal=sum(q*p for _,q,p in items)
    with conn() as c:
        seq=c.execute("SELECT COALESCE(MAX(id),0)+1 n FROM invoices").fetchone()['n']; inv_no=f"{prefix}-{issue.strftime('%Y%m')}-{seq:05d}"
        cur=c.execute("INSERT INTO invoices(invoice_no,customer_id,issue_date,due_date,subtotal) VALUES (?,?,?,?,?)",(inv_no,customer_id,issue.isoformat(),due.isoformat(),subtotal)); iid=cur.lastrowid
        for d,q,p in items: c.execute("INSERT INTO invoice_items(invoice_id,description,qty,unit_price,amount) VALUES (?,?,?,?,?)",(iid,d,q,p,q*p))
    generate_statement(iid); return iid

def referral_reward_balance(customer_id):
    with conn() as c:
        r=c.execute("SELECT COALESCE(SUM(months),0) n FROM referral_reward_ledger WHERE customer_id=?",(customer_id,)).fetchone()
    return max(0,int(r['n'] or 0))

def _consume_referral_reward(customer_id, invoice_id):
    if referral_reward_balance(customer_id)<=0: return False
    with conn() as c:
        c.execute("INSERT INTO referral_reward_ledger(customer_id,months,entry_type,invoice_id,notes,created_by) VALUES (?,?,?,?,?,?)",(customer_id,-1,'Redeemed',invoice_id,'One free modem-rental month applied to recurring invoice','Automatic Billing'))
    return True

def _recurring_invoice_for_customer(customer_id, issue=None, prefix='AUTO'):
    """Create one plan-based recurring invoice and consume one modem-promo cycle when applicable."""
    issue=issue or date.today()
    with conn() as c:
        r=c.execute("""SELECT c.id,c.modem_promo_free_months,c.modem_promo_cycles_used,c.modem_promo_name,
            p.name,p.monthly_price,p.modem_lease
            FROM customers c JOIN subscriptions s ON s.customer_id=c.id JOIN plans p ON p.id=s.plan_id
            WHERE c.id=? AND c.status='Active' AND s.status='Active'""",(customer_id,)).fetchone()
        if not r: raise RuntimeError('Customer does not have an active service plan.')
        pending=c.execute("SELECT * FROM pending_charges WHERE customer_id=? AND applied_invoice_id IS NULL ORDER BY id",(customer_id,)).fetchall()
    items=[(r['name'],1,float(r['monthly_price']))]
    lease=float(r['modem_lease'] or 0); promo_applied=False
    if lease>0:
        items.append(("Monthly Modem Device Lease",1,lease))
        free_months=max(0,int(r['modem_promo_free_months'] or 0)); used=max(0,int(r['modem_promo_cycles_used'] or 0))
        if free_months>used:
            promo_name=(r['modem_promo_name'] or f"{free_months}-Month Free Modem Rental Promotion").strip()
            items.append((f"{promo_name} — Free Month {used+1} of {free_months}",1,-lease)); promo_applied=True
        elif referral_reward_balance(customer_id)>0:
            items.append(("Customer Referral Reward — Free Modem Rental Month",1,-lease))
    with conn() as c:
        tablets=c.execute("SELECT ts.*,p.name plan_name FROM tablet_services ts JOIN plans p ON p.id=ts.plan_id WHERE ts.customer_id=? AND ts.status='Active'",(customer_id,)).fetchall()
    for ts in tablets:
        # Avoid double billing if the tablet plan is also the customer's primary legacy subscription.
        if r['name'] != ts['plan_name']:
            items.append((ts['plan_name']+' — IMEI '+str(ts['imei'])[-4:],1,float(ts['monthly_price'])))
    items += [(x['description'],1,float(x['amount'])) for x in pending]
    iid=create_invoice(customer_id,items,issue,issue+timedelta(days=15),prefix)
    with conn() as c:
        if pending: c.executemany("UPDATE pending_charges SET applied_invoice_id=? WHERE id=?",[(iid,x['id']) for x in pending])
        if promo_applied: c.execute("UPDATE customers SET modem_promo_cycles_used=COALESCE(modem_promo_cycles_used,0)+1 WHERE id=?",(customer_id,))
    if any(d=="Customer Referral Reward — Free Modem Rental Month" for d,_,_ in items):
        _consume_referral_reward(customer_id,iid)
    accounting_try('invoice',iid)
    return iid

def _contract_allows_invoice(customer, issue_date):
    months=int(customer.get('contract_months') or 0)
    if months<=0: return True
    raw=customer.get('contract_start') or customer.get('billing_started_at')
    if not raw: return True
    try: start=date.fromisoformat(str(raw)[:10])
    except Exception: return True
    return issue_date < add_months(start,months)

def run_monthly_billing(send_email=True):
    today=date.today(); created=[]
    with conn() as c:
        customers=c.execute("""SELECT c.id,c.billing_day,c.contract_start,c.contract_months,c.billing_started_at,c.billing_hold_until_first_payment
            FROM customers c JOIN subscriptions s ON s.customer_id=c.id
            WHERE c.status='Active' AND s.status='Active' AND c.billing_day=?""",(min(today.day,28),)).fetchall()
        customer_rows=[dict(r) for r in customers]
    for r in customer_rows:
        if int(r.get('billing_hold_until_first_payment') or 0): continue
        if not _contract_allows_invoice(r,today): continue
        with conn() as c:
            exists=c.execute("SELECT 1 FROM invoices WHERE customer_id=? AND substr(issue_date,1,7)=? AND invoice_no LIKE 'AUTO-%' AND status!='Void'",(r['id'],today.strftime('%Y-%m'))).fetchone()
        if exists: continue
        try:
            iid=_recurring_invoice_for_customer(r['id'],today,'AUTO'); created.append(iid)
        except Exception as e:
            print('recurring invoice error:',r['id'],e); continue
    if send_email:
        for iid in created:
            try: email_statement(iid)
            except Exception as e: print('statement email error:',e)
    return created

def stripe_checkout_for_invoice(iid, success_url, cancel_url, context='invoice'):
    if not STRIPE_SECRET_KEY: raise HTTPException(503,'Stripe not configured')
    with conn() as c:
        inv=c.execute("""SELECT i.*,c.email,c.first_name,c.last_name,c.account_no FROM invoices i
            JOIN customers c ON c.id=i.customer_id WHERE i.id=?""",(iid,)).fetchone()
    if not inv: raise HTTPException(404,'Invoice not found')
    if inv['status']=='Void': raise HTTPException(409,'This invoice has been voided and cannot be paid.')
    bal=round(float(inv['subtotal'] or 0)-float(inv['amount_paid'] or 0),2)
    if bal<=0: return None
    form={
      'mode':'payment','success_url':success_url,'cancel_url':cancel_url,
      'line_items[0][price_data][currency]':'usd',
      'line_items[0][price_data][product_data][name]':f"{COMPANY_NAME} {inv['invoice_no']}",
      'line_items[0][price_data][unit_amount]':str(int(round(bal*100))),
      'line_items[0][quantity]':'1','metadata[invoice_id]':str(iid),
      'metadata[customer_id]':str(inv['customer_id']),'metadata[payment_context]':context
    }
    if inv['email']: form['customer_email']=inv['email']
    req=urllib.request.Request('https://api.stripe.com/v1/checkout/sessions',data=urllib.parse.urlencode(form).encode(),headers={'Authorization':f'Bearer {STRIPE_SECRET_KEY}','Content-Type':'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req,timeout=30) as resp: session=json.loads(resp.read().decode())
    except Exception as e: raise HTTPException(502,f'Payment processor error: {e}')
    with conn() as c: c.execute("UPDATE invoices SET stripe_session_id=? WHERE id=?",(session['id'],iid))
    return session

def email_payment_confirmation(pid):
    with conn() as c:
        p=c.execute("""SELECT p.*,i.invoice_no,i.subtotal,i.amount_paid,i.due_date,c.first_name,c.last_name,c.email,c.account_no
            FROM payments p JOIN customers c ON c.id=p.customer_id LEFT JOIN invoices i ON i.id=p.invoice_id WHERE p.id=?""",(pid,)).fetchone()
    if not p or not p['email']: return False
    remaining=max(0,float(p['subtotal'] or 0)-float(p['amount_paid'] or 0)) if p['invoice_id'] else 0
    subject=f"Payment Confirmation — {p['invoice_no'] or p['reference'] or 'Entire Wireless'}"
    body=f"Hello {p['first_name']},\n\nWe received your payment successfully.\n\nAccount: {p['account_no']}\nInvoice: {p['invoice_no'] or 'N/A'}\nPayment amount: {money(p['amount'])}\nPayment date: {p['payment_date']}\nPayment method: {p['method'] or 'Card'}\nConfirmation: {p['reference'] or ''}\nRemaining invoice balance: {money(remaining)}\n\nThank you for choosing {COMPANY_NAME}.\nCustomer portal: {PUBLIC_URL}/portal\n\n{COMPANY_DISPLAY_LEGAL}\n{SUPPORT_EMAIL}\n{COMPANY_PHONE}"
    attachment=None
    if p['invoice_id']:
        try: attachment=generate_statement(int(p['invoice_id']))
        except Exception: attachment=None
    return smtp_send(p['email'],subject,body,attachment)

_verizon_cache={'access_token':None,'access_expires':0,'session_token':None,'session_time':0}

def _urlopen_json(req, timeout=25):
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        raw=resp.read().decode() or '{}'; return json.loads(raw), resp.status

def _verizon_env(name, startup_value=''):
    # Read at request time as well as startup. This avoids stale/empty module-level
    # values after environment changes and strips accidental surrounding whitespace.
    value=os.getenv(name)
    if value is None:
        value=startup_value
    return str(value or '').strip()

def verizon_access_token():
    app_key=_verizon_env('VERIZON_APP_KEY', VERIZON_APP_KEY)
    app_secret=_verizon_env('VERIZON_APP_SECRET', VERIZON_APP_SECRET)
    missing=[]
    if not app_key: missing.append('VERIZON_APP_KEY')
    if not app_secret: missing.append('VERIZON_APP_SECRET')
    if missing: raise RuntimeError('Missing Render environment variable(s): '+', '.join(missing))
    if _verizon_cache['access_token'] and time.time() < _verizon_cache['access_expires']-60: return _verizon_cache['access_token']
    basic=base64.b64encode(f'{app_key}:{app_secret}'.encode()).decode()
    req=urllib.request.Request(VERIZON_OAUTH_URL,data=b'grant_type=client_credentials',headers={'Authorization':f'Basic {basic}','Content-Type':'application/x-www-form-urlencoded','Accept':'application/json'},method='POST')
    data,_=_urlopen_json(req); token=data.get('access_token')
    if not token: raise RuntimeError(f'No ThingSpace access_token returned: {data}')
    _verizon_cache['access_token']=token; _verizon_cache['access_expires']=time.time()+int(data.get('expires_in',3600)); return token

def verizon_session_token(force=False):
    uws_username=_verizon_env('VERIZON_UWS_USERNAME', VERIZON_UWS_USERNAME)
    uws_password=_verizon_env('VERIZON_UWS_PASSWORD', VERIZON_UWS_PASSWORD)
    missing=[]
    if not uws_username: missing.append('VERIZON_UWS_USERNAME')
    if not uws_password: missing.append('VERIZON_UWS_PASSWORD')
    if missing: raise RuntimeError('Missing Render environment variable(s): '+', '.join(missing))
    if not force and _verizon_cache['session_token'] and time.time()-_verizon_cache['session_time']<900: return _verizon_cache['session_token']
    token=verizon_access_token(); payload=json.dumps({'username':uws_username,'password':uws_password}).encode()
    req=urllib.request.Request(f'{VERIZON_BASE_URL}/session/login',data=payload,headers={'Authorization':f'Bearer {token}','Content-Type':'application/json','Accept':'application/json'},method='POST')
    data,_=_urlopen_json(req); st=data.get('sessionToken')
    if not st: raise RuntimeError(f'No VZ-M2M session token returned: {data}')
    _verizon_cache['session_token']=st; _verizon_cache['session_time']=time.time(); return st

def is_verizon_carrier(value):
    # CRM inventory historically uses both VZW and Verizon labels.
    carrier=str(value or '').strip().lower()
    return carrier in ('vzw','verizon','verizon wireless') or 'verizon' in carrier

def verizon_list_all_devices():
    """Read-only ThingSpace inventory retrieval with explicit diagnostics.

    For normal inventories, first request by accountName only (plus the response-size
    limit). If Verizon reports more than one page, restart using documented
    largestDeviceIdSeen pagination so DeviceId extended attributes are returned.
    """
    access=verizon_access_token(); sess=verizon_session_token()
    account_name=_verizon_env('VERIZON_ACCOUNT_NAME', VERIZON_ACCOUNT_NAME)
    if not account_name: raise RuntimeError('Missing Render environment variable: VERIZON_ACCOUNT_NAME')

    def fetch(payload):
        req=urllib.request.Request(
            f'{VERIZON_BASE_URL}/devices/actions/list',
            data=json.dumps(payload).encode(),
            headers={'Authorization':f'Bearer {access}','VZ-M2M-Token':sess,'Content-Type':'application/json','Accept':'application/json'},
            method='POST')
        try:
            with urllib.request.urlopen(req,timeout=60) as r:
                raw=r.read().decode() or '{}'; status=r.status
        except urllib.error.HTTPError as e:
            # Keep credentials/device identifiers out of the UI, but preserve Verizon's
            # HTTP status so an empty inventory is not confused with an API failure.
            raise RuntimeError(f'ThingSpace device-list request failed with Verizon HTTP {e.code}.')
        try: data=json.loads(raw)
        except Exception: raise RuntimeError(f'ThingSpace device-list returned HTTP {status} with a non-JSON response.')
        if not isinstance(data,(dict,list)):
            raise RuntimeError(f'ThingSpace device-list returned HTTP {status} with an unexpected response type.')
        return data,status

    # Simplest documented account inventory request. A 100-device account should fit
    # comfortably in this single response (maximum response size is 2,000 devices).
    first,status=fetch({'accountName':account_name,'maxNumberOfDevices':2000})
    if isinstance(first,list):
        devices=first
        more=False
    else:
        devices=first.get('devices')
        more=bool(first.get('hasMoreData'))
        if devices is None:
            keys=', '.join(sorted(str(k) for k in first.keys())) or 'none'
            raise RuntimeError(f'ThingSpace device-list returned HTTP {status}, but no devices collection was present (response fields: {keys}).')
        if not isinstance(devices,list):
            raise RuntimeError(f'ThingSpace device-list returned HTTP {status}, but the devices field was not a list.')
    if not more:
        return devices, {'http_status':status,'records':len(devices),'pages':1,'account_name':account_name}

    # If the account ever grows beyond one response, restart using Verizon's
    # recommended DeviceId pagination so every page can be retrieved without gaps.
    all_devices=[]; largest='0'; seen=set(); pages=0
    for _ in range(1000):
        data,status=fetch({'accountName':account_name,'largestDeviceIdSeen':largest,'maxNumberOfDevices':2000})
        page=data.get('devices',[]) if isinstance(data,dict) else data
        if not isinstance(page,list): raise RuntimeError('ThingSpace paginated device-list response did not contain a device list.')
        pages+=1
        if not page: break
        all_devices.extend(page)
        if not (isinstance(data,dict) and data.get('hasMoreData')): break
        ids=[]
        for d in page:
            for a in (d.get('extendedAttributes') or []) if isinstance(d,dict) else []:
                if str(a.get('key','')).lower()=='deviceid':
                    try: ids.append(int(str(a.get('value','')).strip()))
                    except Exception: pass
        if not ids: raise RuntimeError('ThingSpace reported additional inventory pages but did not return pagination DeviceId values.')
        nxt=str(max(ids))
        if nxt in seen or nxt==largest: raise RuntimeError('ThingSpace inventory pagination did not advance.')
        seen.add(nxt); largest=nxt
    return all_devices, {'http_status':status,'records':len(all_devices),'pages':pages,'account_name':account_name}

def verizon_inventory_diagnostic():
    """Compare UWS-visible inventory with the configured billing account.

    This is read-only. It deliberately returns aggregate counts/account names only;
    no device identifiers or credentials are exposed in the UI or audit log.
    """
    access=verizon_access_token(); sess=verizon_session_token(force=True)
    account_name=_verizon_env('VERIZON_ACCOUNT_NAME', VERIZON_ACCOUNT_NAME)
    if not account_name: raise RuntimeError('Missing Render environment variable: VERIZON_ACCOUNT_NAME')

    def fetch(payload):
        req=urllib.request.Request(
            f'{VERIZON_BASE_URL}/devices/actions/list',
            data=json.dumps(payload).encode(),
            headers={'Authorization':f'Bearer {access}','VZ-M2M-Token':sess,'Content-Type':'application/json','Accept':'application/json'},
            method='POST')
        try:
            with urllib.request.urlopen(req,timeout=60) as r:
                raw=r.read().decode() or '{}'; status=r.status
        except urllib.error.HTTPError as e:
            raise RuntimeError(f'ThingSpace diagnostic request failed with Verizon HTTP {e.code}.')
        try: data=json.loads(raw)
        except Exception: raise RuntimeError(f'ThingSpace diagnostic returned HTTP {status} with a non-JSON response.')
        if isinstance(data,list):
            return data,status,False
        if not isinstance(data,dict):
            raise RuntimeError(f'ThingSpace diagnostic returned HTTP {status} with an unexpected response type.')
        devices=data.get('devices')
        if devices is None:
            keys=', '.join(sorted(str(k) for k in data.keys())) or 'none'
            raise RuntimeError(f'ThingSpace diagnostic returned HTTP {status}, but no devices collection was present (response fields: {keys}).')
        if not isinstance(devices,list):
            raise RuntimeError('ThingSpace diagnostic devices field was not a list.')
        return devices,status,bool(data.get('hasMoreData'))

    # Verizon documents an empty request body as all devices visible to the UWS user.
    all_devices,all_status,all_more=fetch({})
    acct_devices,acct_status,acct_more=fetch({'accountName':account_name,'largestDeviceIdSeen':0,'maxNumberOfDevices':2000})

    def summarize(devices):
        accounts=set(); imeis=0; iccids=0
        for d in devices:
            if not isinstance(d,dict): continue
            a=str(d.get('accountName') or '').strip()
            if a: accounts.add(a)
            for x in (d.get('deviceIds') or []):
                if not isinstance(x,dict) or not x.get('id'): continue
                kind=str(x.get('kind') or '').strip().lower()
                if kind=='imei': imeis+=1
                elif kind=='iccid': iccids+=1
        return {'records':len(devices),'imeis':imeis,'iccids':iccids,'accounts':sorted(accounts)}

    a=summarize(all_devices); b=summarize(acct_devices)
    return {
        'uws_records':a['records'],'uws_imeis':a['imeis'],'uws_iccids':a['iccids'],
        'uws_accounts':a['accounts'],'uws_has_more':all_more,'uws_http':all_status,
        'configured_account':account_name,'account_records':b['records'],
        'account_imeis':b['imeis'],'account_iccids':b['iccids'],
        'account_accounts':b['accounts'],'account_has_more':acct_more,'account_http':acct_status,
    }

def verizon_import_inventory():
    devices,diagnostic=verizon_list_all_devices()
    result={'devices':len(devices),'new_modems':0,'existing_modems':0,'new_sims':0,'existing_sims':0,'skipped':0,'imei_found':0,'iccid_found':0,'pages':diagnostic.get('pages',1),'http_status':diagnostic.get('http_status',200)}
    with conn() as c:
        for d in devices:
            ids={str(x.get('kind','')).upper():str(x.get('id','')).strip() for x in (d.get('deviceIds') or []) if x.get('id')}
            imei=ids.get('IMEI',''); iccid=ids.get('ICCID',''); mdn=ids.get('MDN','') or ids.get('MSISDN','')
            ci=(d.get('carrierInformations') or [{}])[0] or {}
            carrier=ci.get('carrierName') or 'Verizon Wireless'; state=ci.get('state') or ''
            plan=ci.get('servicePlan') or ''; account=d.get('accountName') or ''
            note=f'ThingSpace sync; state={state or "unknown"}; plan={plan or "unknown"}; account={account or "unknown"}'
            if imei:
                result['imei_found']+=1
                m=c.execute('SELECT id,customer_id FROM modems WHERE imei=?',(imei,)).fetchone()
                if m: result['existing_modems']+=1
                else:
                    c.execute("INSERT INTO modems(imei,status,notes,acquired_date) VALUES (?,'Available',?,?)",(imei,note,date.today().isoformat())); result['new_modems']+=1
            if iccid:
                result['iccid_found']+=1
                sim=c.execute('SELECT id,customer_id FROM sims WHERE iccid=?',(iccid,)).fetchone()
                if sim:
                    result['existing_sims']+=1
                    c.execute("UPDATE sims SET carrier=CASE WHEN carrier IS NULL OR carrier='' THEN ? ELSE carrier END, mdn=CASE WHEN ?<>'' THEN ? ELSE mdn END WHERE id=?",(carrier,mdn,mdn,sim['id']))
                else:
                    c.execute("INSERT INTO sims(iccid,carrier,mdn,status,notes) VALUES (?,?,?,'Available',?)",(iccid,carrier,mdn,note)); result['new_sims']+=1
            if not imei and not iccid: result['skipped']+=1
    return result

def verizon_lookup_device(iccid):
    """Read-only ThingSpace lookup for one ICCID. No device state is modified."""
    iccid=str(iccid or '').strip()
    if not iccid: raise RuntimeError('ICCID is required')
    if not iccid.isdigit() or len(iccid)>20: raise RuntimeError('ICCID must be numeric and up to 20 digits')
    access=verizon_access_token(); session=verizon_session_token()
    payload={'deviceId':{'id':iccid,'kind':'ICCID'}}
    account_name=_verizon_env('VERIZON_ACCOUNT_NAME', VERIZON_ACCOUNT_NAME)
    if account_name: payload['accountName']=account_name
    body=json.dumps(payload).encode()
    def do_request(sess):
        req=urllib.request.Request(f'{VERIZON_BASE_URL}/devices/actions/list',data=body,headers={'Authorization':f'Bearer {access}','VZ-M2M-Token':sess,'Content-Type':'application/json','Accept':'application/json'},method='POST')
        return _urlopen_json(req)
    try: data,_=do_request(session)
    except urllib.error.HTTPError as e:
        if e.code in (401,403):
            _verizon_cache['session_token']=None
            session=verizon_session_token(True)
            data,_=do_request(session)
        else: raise
    devices=data.get('devices',[]) if isinstance(data,dict) else (data if isinstance(data,list) else [])
    if not devices: return {'found':False,'iccid':iccid}
    d=devices[0] or {}
    ids={str(x.get('kind','')).upper():str(x.get('id','')) for x in (d.get('deviceIds') or []) if isinstance(x,dict)}
    cis=d.get('carrierInformations') or []
    ci=cis[0] if cis and isinstance(cis[0],dict) else {}
    return {'found':True,'iccid':ids.get('ICCID',iccid),'imei':ids.get('IMEI',''),'mdn':ids.get('MDN',''),'state':ci.get('state',''),'service_plan':ci.get('servicePlan',''),'carrier':ci.get('carrierName',''),'connected':d.get('connected'),'account_name':d.get('accountName',''),'last_connection_date':d.get('lastConnectionDate','')}

def verizon_device_action(customer_id, action, reason='CRM automation'):
    if action not in ('suspend','restore'): raise ValueError('Unsupported carrier action')
    with conn() as c:
        sim=c.execute("SELECT * FROM sims WHERE customer_id=? AND (lower(trim(COALESCE(carrier,''))) IN ('vzw','verizon','verizon wireless') OR lower(COALESCE(carrier,'')) LIKE '%verizon%') ORDER BY id DESC LIMIT 1",(customer_id,)).fetchone()
        cust=c.execute("SELECT * FROM customers WHERE id=?",(customer_id,)).fetchone()
    if not cust: raise RuntimeError('Customer not found')
    if not sim or not sim['iccid']: raise RuntimeError('No Verizon SIM ICCID assigned to customer')
    device={'deviceIds':[{'id':sim['iccid'],'kind':'ICCID'}]}
    payload={'devices':[device]}
    if VERIZON_ACCOUNT_NAME: payload['accountName']=VERIZON_ACCOUNT_NAME
    if action=='suspend': payload['withBilling']=True
    if not VERIZON_ENABLED or VERIZON_DRY_RUN:
        data={'requestId':f'DRYRUN-{secrets.token_hex(8)}','mode':'dry-run','action':action,'iccid':sim['iccid']}
    else:
        access=verizon_access_token(); session=verizon_session_token(); body=json.dumps(payload).encode()
        req=urllib.request.Request(f'{VERIZON_BASE_URL}/devices/actions/{action}',data=body,headers={'Authorization':f'Bearer {access}','VZ-M2M-Token':session,'Content-Type':'application/json','Accept':'application/json'},method='POST')
        try: data,_=_urlopen_json(req)
        except urllib.error.HTTPError as e:
            if e.code in (401,403):
                _verizon_cache['session_token']=None; session=verizon_session_token(True); req.headers['VZ-M2M-Token']=session; data,_=_urlopen_json(req)
            else: raise
    reqid=data.get('requestId','')
    status='Dry Run' if (not VERIZON_ENABLED or VERIZON_DRY_RUN) else 'Accepted'
    with conn() as c:
        c.execute("INSERT INTO carrier_actions(customer_id,sim_id,action,status,request_id,response) VALUES (?,?,?,?,?,?)",(customer_id,sim['id'],action,status,reqid,json.dumps(data)[:8000]))
        if action=='suspend': c.execute("UPDATE customers SET service_status='Suspended - Nonpayment',last_suspend_at=? WHERE id=?",(datetime.now().isoformat(timespec='seconds'),customer_id))
        else: c.execute("UPDATE customers SET service_status='Active',last_restore_at=? WHERE id=?",(datetime.now().isoformat(timespec='seconds'),customer_id))
    return data

def customer_open_balance(customer_id):
    with conn() as c: return float(c.execute("SELECT COALESCE(SUM(subtotal-amount_paid),0) v FROM invoices WHERE customer_id=? AND status NOT IN ('Paid','Void')",(customer_id,)).fetchone()['v'] or 0)

def customer_suspension_balance(customer_id):
    cutoff=(date.today()-timedelta(days=SUSPEND_AFTER_DAYS)).isoformat()
    with conn() as c:
        return float(c.execute("SELECT COALESCE(SUM(subtotal-amount_paid),0) v FROM invoices WHERE customer_id=? AND status NOT IN ('Paid','Void') AND due_date<=?",(customer_id,cutoff)).fetchone()['v'] or 0)

def queue_reconnect_fee(customer_id, source_action_id=None):
    with conn() as c:
        existing=c.execute("SELECT 1 FROM pending_charges WHERE customer_id=? AND source='Reconnect' AND source_id IS ?",(customer_id,source_action_id)).fetchone()
        if not existing: c.execute("INSERT INTO pending_charges(customer_id,description,amount,source,source_id) VALUES (?,?,?,?,?)",(customer_id,'Reconnect Fee',RECONNECT_FEE,'Reconnect',source_action_id))

def maybe_restore_after_payment(customer_id):
    with conn() as c: cust=c.execute("SELECT * FROM customers WHERE id=?",(customer_id,)).fetchone()
    if not cust or not str(cust['service_status'] or '').startswith('Suspended'): return False
    if customer_suspension_balance(customer_id) > .005: return False
    data=verizon_device_action(customer_id,'restore','Payment confirmed')
    with conn() as c: aid=c.execute("SELECT id FROM carrier_actions WHERE customer_id=? AND action='restore' ORDER BY id DESC LIMIT 1",(customer_id,)).fetchone()['id']
    queue_reconnect_fee(customer_id,aid)
    return True

def run_nonpayment_suspensions():
    cutoff=(date.today()-timedelta(days=SUSPEND_AFTER_DAYS)).isoformat(); suspended=[]; failures=[]
    with conn() as c:
        rows=c.execute("""SELECT DISTINCT c.id,c.account_no FROM customers c JOIN invoices i ON i.customer_id=c.id WHERE c.status='Active' AND COALESCE(c.service_status,'Active')='Active' AND COALESCE(c.suspension_exempt,0)=0 AND COALESCE(c.payment_arrangement,0)=0 AND i.status NOT IN ('Paid','Void') AND i.due_date<=? AND (i.subtotal-i.amount_paid)>.005 AND EXISTS (SELECT 1 FROM sims s WHERE s.customer_id=c.id AND TRIM(COALESCE(s.iccid,''))<>'' AND (lower(trim(COALESCE(s.carrier,''))) IN ('vzw','verizon','verizon wireless') OR lower(COALESCE(s.carrier,'')) LIKE '%verizon%'))""",(cutoff,)).fetchall()
    for r in rows:
        try: verizon_device_action(r['id'],'suspend','Past due'); suspended.append(r['id'])
        except Exception as e:
            failures.append((r['id'],str(e)))
            with conn() as c: c.execute("INSERT INTO carrier_actions(customer_id,action,status,response) VALUES (?,?,?,?)",(r['id'],'suspend','Failed',str(e)[:8000]))
    return suspended,failures

def run_daily_tasks():
    with conn() as c:
        ids=[r['id'] for r in c.execute("SELECT id FROM invoices WHERE status NOT IN ('Paid','Void')").fetchall()]
        for iid in ids: update_invoice_status(c,iid)
        reminders=[r['id'] for r in c.execute("SELECT id FROM invoices WHERE status='Past Due' AND eod_notice_at IS NOT NULL AND (last_reminder_at IS NULL OR date(last_reminder_at) <= date('now',?))",(f'-{PAST_DUE_REMINDER_DAYS} day',)).fetchall()]
    for iid in reminders:
        try: email_statement(iid,True)
        except Exception as e: print('reminder error:',e)
    suspended,failures=run_nonpayment_suspensions()
    return len(reminders)+len(suspended)

def api_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def api_user(request: Request):
    auth=request.headers.get('authorization','')
    if not auth.lower().startswith('bearer '):
        raise HTTPException(401,'Missing bearer token')
    raw=auth.split(' ',1)[1].strip()
    if not raw:
        raise HTTPException(401,'Missing bearer token')
    th=api_token_hash(raw)
    now=datetime.utcnow().isoformat(timespec='seconds')
    with conn() as c:
        row=c.execute("""SELECT t.id token_id,t.expires_at,t.revoked_at,u.* FROM api_tokens t JOIN users u ON u.id=t.user_id WHERE t.token_hash=?""",(th,)).fetchone()
        if not row or row['revoked_at'] or not row['active']:
            raise HTTPException(401,'Invalid or deactivated credentials')
        try:
            if datetime.fromisoformat(row['expires_at']) <= datetime.utcnow():
                raise HTTPException(401,'Session expired')
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(401,'Invalid session')
        if bool(row['must_change_password']) or password_expired(row):
            if not row['must_change_password']:
                c.execute("UPDATE users SET must_change_password=1 WHERE id=?",(row['id'],))
            raise HTTPException(428,'Password change required')
        c.execute("UPDATE api_tokens SET last_used_at=? WHERE id=?",(now,row['token_id']))
    return row

def api_admin(request: Request):
    u=api_user(request)
    if u['role']!='admin': raise HTTPException(403,'Administrator access required')
    return u

def api_audit(user_email, action, entity, entity_id=None, details=''):
    with conn() as c:
        c.execute("INSERT INTO audit_log(user_email,action,entity,entity_id,details) VALUES (?,?,?,?,?)",(user_email,action,entity,entity_id,details))

@app.exception_handler(401)
async def auth_error(request, exc):
    if request.url.path.startswith('/api/'): return JSONResponse({'detail':getattr(exc,'detail','Unauthorized')},status_code=401)
    return RedirectResponse('/login',303)

@app.exception_handler(428)
async def password_change_error(request, exc):
    if request.url.path.startswith('/api/'): return JSONResponse({'detail':getattr(exc,'detail','Password change required')},status_code=428)
    return RedirectResponse('/change-password',303)

@app.get('/health')
def health(): return {'ok':True,'app':APP_NAME}

@app.get('/login',response_class=HTMLResponse)
def login_form():
    return HTMLResponse(f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Staff Login</title><style>{CSS}</style></head><body><div class="login"><div class="card"><div class="kicker">Secure Staff Access</div><h1>Entire Wireless CRM</h1><form method="post"><label>Email</label><input type="email" name="email" required><label>Password</label><input type="password" name="password" required><button class="btn">Sign in</button></form><p class="muted">Customer? <a href="/portal">Open customer portal</a>.</p></div></div></body></html>''')

@app.post('/login')
def login(request:Request,email:str=Form(...),password:str=Form(...)):
    with conn() as c:
        u=c.execute("SELECT * FROM users WHERE lower(email)=? AND active=1",(email.lower(),)).fetchone()
        if not u or not pcheck(password,u['password_hash']): return RedirectResponse('/login?error=1',303)
        required=bool(u['must_change_password']) or password_expired(u)
        if required and not u['must_change_password']:
            c.execute("UPDATE users SET must_change_password=1 WHERE id=?",(u['id'],))
    request.session.update({'user_id':u['id'],'user_email':u['email'],'user_name':u['name'],'role':u['role'],'password_change_required':required})
    return RedirectResponse('/change-password' if required else '/',303)

@app.get('/change-password',response_class=HTMLResponse)
def change_password_form(request:Request,error:str=''):
    if not staff(request): return RedirectResponse('/login',303)
    msg={'reuse':'New password cannot match any of your last 3 passwords.','mismatch':'The new passwords did not match.','length':'Password must be at least 8 characters.','current':'Current password was incorrect.'}.get(error,'')
    notice=f'<div class="notice" style="border-left-color:#b83b32">{msg}</div>' if msg else ''
    forced='<div class="notice">You must change your password before continuing to the CRM.</div>' if request.session.get('password_change_required') else ''
    return page(request,'Change Password',f'''<h1>Change Password</h1>{forced}{notice}<div class="card" style="max-width:600px"><form method="post"><label>Current Password</label><input type="password" name="current_password" required><label>New Password</label><input type="password" name="new_password" required minlength="8"><label>Confirm New Password</label><input type="password" name="confirm_password" required minlength="8"><p class="muted">Employee passwords cannot reuse any of the last {PASSWORD_HISTORY_COUNT} passwords. Non-admin employee passwords expire every {PASSWORD_MAX_AGE_DAYS} days.</p><button class="btn">Change Password</button></form></div>''')

@app.post('/change-password')
def change_password(request:Request,current_password:str=Form(...),new_password:str=Form(...),confirm_password:str=Form(...)):
    if not staff(request): return RedirectResponse('/login',303)
    if len(new_password)<8: return RedirectResponse('/change-password?error=length',303)
    if new_password!=confirm_password: return RedirectResponse('/change-password?error=mismatch',303)
    uid=request.session['user_id']
    with conn() as c:
        u=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
        if not u or not pcheck(current_password,u['password_hash']): return RedirectResponse('/change-password?error=current',303)
        if password_is_reused(c,uid,new_password,u['password_hash']): return RedirectResponse('/change-password?error=reuse',303)
        old_hash=u['password_hash']; new_hash=phash(new_password)
        c.execute("INSERT INTO password_history(user_id,password_hash) VALUES (?,?)",(uid,old_hash))
        c.execute("UPDATE users SET password_hash=?,must_change_password=0,password_changed_at=CURRENT_TIMESTAMP WHERE id=?",(new_hash,uid))
        c.execute("DELETE FROM password_history WHERE user_id=? AND id NOT IN (SELECT id FROM password_history WHERE user_id=? ORDER BY id DESC LIMIT ?)",(uid,uid,max(PASSWORD_HISTORY_COUNT,3)))
    request.session['password_change_required']=False
    audit(request,'PASSWORD_CHANGE','user',uid,'employee changed password')
    return RedirectResponse('/',303)

@app.get('/assets/entire-wireless-logo.png')
def entire_wireless_logo_asset():
    logo=BASE/'entire_wireless_logo.png'
    if not logo.exists(): raise HTTPException(404)
    return FileResponse(str(logo), media_type='image/png')

@app.get('/logout')
def logout(request:Request): request.session.clear(); return RedirectResponse('/login',303)

# ---------------- Native/mobile API v1 ----------------
@app.post('/api/v1/login')
async def api_login(request:Request):
    try: body=await request.json()
    except Exception: raise HTTPException(400,'JSON body required')
    email=str(body.get('email','')).strip().lower(); password=str(body.get('password',''))
    device=str(body.get('device_name','iOS'))[:100]
    if not email or not password: raise HTTPException(400,'Email and password are required')
    with conn() as c:
        u=c.execute("SELECT * FROM users WHERE lower(email)=? AND active=1",(email,)).fetchone()
        if not u or not pcheck(password,u['password_hash']): raise HTTPException(401,'Invalid credentials')
        required=bool(u['must_change_password']) or password_expired(u)
        if required and not u['must_change_password']:
            c.execute("UPDATE users SET must_change_password=1 WHERE id=?",(u['id'],))
        raw=secrets.token_urlsafe(48); th=api_token_hash(raw)
        expires=(datetime.utcnow()+timedelta(days=30)).isoformat(timespec='seconds')
        c.execute("INSERT INTO api_tokens(user_id,token_hash,expires_at,device_name) VALUES (?,?,?,?)",(u['id'],th,expires,device))
    api_audit(u['email'],'API_LOGIN','user',u['id'],f'device={device}')
    return {'token':raw,'expires_at':expires,'must_change_password':required,'user':{'id':u['id'],'name':u['name'],'email':u['email'],'role':u['role']}}

@app.post('/api/v1/logout')
def api_logout(request:Request):
    auth=request.headers.get('authorization','')
    if auth.lower().startswith('bearer '):
        th=api_token_hash(auth.split(' ',1)[1].strip())
        with conn() as c: c.execute("UPDATE api_tokens SET revoked_at=CURRENT_TIMESTAMP WHERE token_hash=?",(th,))
    return {'ok':True}

@app.get('/api/v1/me')
def api_me(request:Request):
    u=api_user(request)
    return {'id':u['id'],'name':u['name'],'email':u['email'],'role':u['role'],'password_expires_in_days':None if u['role']=='admin' else max(0,PASSWORD_MAX_AGE_DAYS-(datetime.now()-datetime.fromisoformat(u['password_changed_at'])).days)}

@app.post('/api/v1/change-password')
async def api_change_password(request:Request):
    auth=request.headers.get('authorization','')
    if not auth.lower().startswith('bearer '): raise HTTPException(401)
    raw_token=auth.split(' ',1)[1].strip(); th=api_token_hash(raw_token)
    try: body=await request.json()
    except Exception: raise HTTPException(400,'JSON body required')
    current=str(body.get('current_password','')); new=str(body.get('new_password',''))
    if len(new)<8: raise HTTPException(400,'Password must be at least 8 characters')
    with conn() as c:
        u=c.execute("SELECT u.*,t.id token_id FROM api_tokens t JOIN users u ON u.id=t.user_id WHERE t.token_hash=? AND t.revoked_at IS NULL AND u.active=1",(th,)).fetchone()
        if not u or not pcheck(current,u['password_hash']): raise HTTPException(401,'Current password is incorrect')
        if password_is_reused(c,u['id'],new,u['password_hash']): raise HTTPException(409,f'Password cannot match any of the last {PASSWORD_HISTORY_COUNT} passwords')
        old=u['password_hash']; nh=phash(new)
        c.execute("INSERT INTO password_history(user_id,password_hash) VALUES (?,?)",(u['id'],old))
        c.execute("UPDATE users SET password_hash=?,must_change_password=0,password_changed_at=CURRENT_TIMESTAMP WHERE id=?",(nh,u['id']))
        c.execute("DELETE FROM password_history WHERE user_id=? AND id NOT IN (SELECT id FROM password_history WHERE user_id=? ORDER BY id DESC LIMIT ?)",(u['id'],u['id'],max(PASSWORD_HISTORY_COUNT,3)))
    api_audit(u['email'],'PASSWORD_CHANGE','user',u['id'],'password changed from mobile app')
    return {'ok':True}

@app.get('/api/v1/dashboard')
def api_dashboard(request:Request):
    api_user(request); run_daily_tasks()
    with conn() as c:
        active=c.execute("SELECT count(*) n FROM customers WHERE status='Active'").fetchone()['n']
        mrr=c.execute("SELECT COALESCE(sum(p.monthly_price+p.modem_lease),0) v FROM subscriptions s JOIN customers c ON c.id=s.customer_id JOIN plans p ON p.id=s.plan_id WHERE c.status='Active' AND s.status='Active'").fetchone()['v']
        past=c.execute("SELECT COALESCE(sum(subtotal-amount_paid),0) v FROM invoices WHERE status='Past Due'").fetchone()['v']
        ar=c.execute("SELECT COALESCE(sum(subtotal-amount_paid),0) v FROM invoices WHERE status NOT IN ('Paid','Void')").fetchone()['v']
        am=c.execute("SELECT count(*) n FROM modems WHERE status='Available'").fetchone()['n']
        asi=c.execute("SELECT count(*) n FROM sims WHERE status='Available'").fetchone()['n']
    return {'active_customers':active,'monthly_recurring_revenue':round(float(mrr),2),'past_due':round(float(past),2),'accounts_receivable':round(float(ar),2),'available_modems':am,'available_sims':asi}

@app.get('/api/v1/customers')
def api_customers(request:Request,q:str=''):
    api_user(request)
    with conn() as c:
        if q:
            like=f'%{q}%'; rows=c.execute("SELECT id,account_no,first_name,last_name,company,email,phone,status,service_status FROM customers WHERE account_no LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR email LIKE ? ORDER BY id DESC LIMIT 250",(like,like,like,like)).fetchall()
        else: rows=c.execute("SELECT id,account_no,first_name,last_name,company,email,phone,status,service_status FROM customers ORDER BY id DESC LIMIT 250").fetchall()
    return {'customers':[dict(r) for r in rows]}

@app.get('/api/v1/customers/{cid}')
def api_customer_detail(request:Request,cid:int):
    api_user(request)
    with conn() as c:
        r=c.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone()
        if not r: raise HTTPException(404,'Customer not found')
        sub=c.execute("SELECT s.status subscription_status,s.start_date,p.name plan_name,p.monthly_price,p.modem_lease FROM subscriptions s JOIN plans p ON p.id=s.plan_id WHERE s.customer_id=?",(cid,)).fetchone()
        modems=[dict(x) for x in c.execute("SELECT id,imei,serial_no,manufacturer,model,status FROM modems WHERE customer_id=? ORDER BY id DESC",(cid,)).fetchall()]
        sims=[dict(x) for x in c.execute("SELECT id,iccid,carrier,mdn,status FROM sims WHERE customer_id=? ORDER BY id DESC",(cid,)).fetchall()]
        inv=[dict(x) for x in c.execute("SELECT id,invoice_no,issue_date,due_date,subtotal,amount_paid,status FROM invoices WHERE customer_id=? ORDER BY id DESC LIMIT 30",(cid,)).fetchall()]
    out=dict(r); out['subscription']=dict(sub) if sub else None; out['modems']=modems; out['sims']=sims; out['invoices']=inv
    return out

@app.get('/api/v1/invoices')
def api_invoices(request:Request,status:str=''):
    api_user(request)
    with conn() as c:
        if status: rows=c.execute("SELECT i.id,i.invoice_no,i.customer_id,i.issue_date,i.due_date,i.subtotal,i.amount_paid,i.status,c.first_name,c.last_name,c.account_no FROM invoices i JOIN customers c ON c.id=i.customer_id WHERE i.status=? ORDER BY i.id DESC LIMIT 250",(status,)).fetchall()
        else: rows=c.execute("SELECT i.id,i.invoice_no,i.customer_id,i.issue_date,i.due_date,i.subtotal,i.amount_paid,i.status,c.first_name,c.last_name,c.account_no FROM invoices i JOIN customers c ON c.id=i.customer_id ORDER BY i.id DESC LIMIT 250").fetchall()
    return {'invoices':[dict(r) for r in rows]}

@app.get('/api/v1/inventory')
def api_inventory(request:Request):
    api_user(request)
    with conn() as c:
        modems=[dict(x) for x in c.execute("SELECT m.id,m.imei,m.serial_no,m.manufacturer,m.model,m.status,m.customer_id,c.account_no FROM modems m LEFT JOIN customers c ON c.id=m.customer_id ORDER BY m.id DESC").fetchall()]
        sims=[dict(x) for x in c.execute("SELECT s.id,s.iccid,s.carrier,s.mdn,s.status,s.customer_id,c.account_no FROM sims s LEFT JOIN customers c ON c.id=s.customer_id ORDER BY s.id DESC").fetchall()]
    return {'modems':modems,'sims':sims}

@app.get('/api/v1/employees')
def api_employees(request:Request):
    api_admin(request)
    with conn() as c:
        rows=c.execute("SELECT id,email,name,role,active,created_at,password_changed_at,must_change_password,deactivated_at,deactivated_by,deactivation_reason FROM users ORDER BY name").fetchall()
    return {'employees':[dict(r) for r in rows]}

@app.get('/',response_class=HTMLResponse)
def dashboard(request:Request):
    require_staff(request); run_daily_tasks()
    with conn() as c:
        active=c.execute("SELECT count(*) n FROM customers WHERE status='Active'").fetchone()['n']; mrr=c.execute("SELECT COALESCE(sum(p.monthly_price+p.modem_lease),0) v FROM subscriptions s JOIN customers c ON c.id=s.customer_id JOIN plans p ON p.id=s.plan_id WHERE c.status='Active' AND s.status='Active'").fetchone()['v']; past=c.execute("SELECT COALESCE(sum(subtotal-amount_paid),0) v FROM invoices WHERE status='Past Due'").fetchone()['v']; ar=c.execute("SELECT COALESCE(sum(subtotal-amount_paid),0) v FROM invoices WHERE status NOT IN ('Paid','Void')").fetchone()['v']; am=c.execute("SELECT count(*) n FROM modems WHERE status='Available'").fetchone()['n']; asi=c.execute("SELECT count(*) n FROM sims WHERE status='Available'").fetchone()['n']; recent=c.execute("SELECT i.*,c.first_name,c.last_name FROM invoices i JOIN customers c ON c.id=i.customer_id ORDER BY i.id DESC LIMIT 8").fetchall()
        if ACCOUNTING_PROVIDER=='zoho':
            acct_row=c.execute("SELECT organization_name FROM zoho_oauth WHERE id=1").fetchone(); acct_connected=bool(acct_row); acct_name=(acct_row['organization_name'] if acct_row else '') or 'Zoho Books'; acct_failed=sum(c.execute(f"SELECT count(*) n FROM {t} WHERE zoho_sync_status='Failed'").fetchone()['n'] for t in ('customers','invoices','payments'))
        elif ACCOUNTING_PROVIDER=='quickbooks':
            acct_row=c.execute("SELECT company_name FROM quickbooks_oauth WHERE id=1").fetchone(); acct_connected=bool(acct_row); acct_name=(acct_row['company_name'] if acct_row else '') or 'QuickBooks Online'; acct_failed=sum(c.execute(f"SELECT count(*) n FROM {t} WHERE quickbooks_sync_status='Failed'").fetchone()['n'] for t in ('customers','invoices','payments'))
        else:
            acct_connected=False; acct_name='No accounting provider'; acct_failed=0
    trs=''.join(f"<tr><td><a href='/invoices/{r['id']}'>{r['invoice_no']}</a></td><td>{r['first_name']} {r['last_name']}</td><td>{money(r['subtotal'])}</td><td>{r['status']}</td></tr>" for r in recent) or '<tr><td colspan=4>No invoices yet.</td></tr>'
    acct_state='Connected' if acct_connected else ('Not configured' if ACCOUNTING_PROVIDER=='none' else 'Not connected')
    acct_extra=(f" · <span class='danger-text'>{acct_failed} failed sync{'s' if acct_failed!=1 else ''}</span>" if acct_failed else '')
    return page(request,'Dashboard',f'''<h1>ISP Operations Dashboard</h1><div class="grid"><div class="card"><div class="muted">Active Subscribers</div><div class="metric">{active}</div></div><div class="card"><div class="muted">Monthly Recurring Revenue</div><div class="metric">{money(mrr)}</div></div><div class="card"><div class="muted">Accounts Receivable</div><div class="metric">{money(ar)}</div></div><div class="card"><div class="muted">Past Due</div><div class="metric">{money(past)}</div></div></div><div class="section grid"><div class="card"><div class="muted">Available Modems</div><b>{am}</b></div><div class="card"><div class="muted">Available SIMs</div><b>{asi}</b></div><div class="card"><div class="muted">Customer Portal</div><a href="/portal">Open Portal</a></div><div class="card"><div class="muted">Accounting</div><b>{html.escape(acct_name)}</b><div>{acct_state}{acct_extra}</div>{('<a href="/integrations/accounting">Open Accounting</a>' if role(request)=='admin' else '')}</div></div><div class="section card"><h2>Recent Billing</h2><table><tr><th>Invoice</th><th>Customer</th><th>Total</th><th>Status</th></tr>{trs}</table></div>''')

@app.get('/customers',response_class=HTMLResponse)
def customers(request:Request,q:str=''):
    require_staff(request)
    with conn() as c:
        if q: rows=c.execute("SELECT * FROM customers WHERE account_no LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR email LIKE ? OR phone LIKE ? OR company LIKE ? ORDER BY id DESC",(*(f'%{q}%',)*6,)).fetchall()
        else: rows=c.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
    trs=''.join(f"<tr><td><a href='/customers/{r['id']}'>{r['account_no']}</a></td><td>{r['first_name']} {r['last_name']}</td><td>{r['customer_type'] or 'Residential'}</td><td>{r['company'] or ''}</td><td>{r['email'] or ''}</td><td>{r['status']}</td></tr>" for r in rows)
    export_q=urllib.parse.quote(q or '')
    return page(request,'Customers',f'''<div class="actions right"><a class="btn secondary" href="/customers/export?q={export_q}">Export Customer List (.CSV)</a><a class="btn" href="/customers/new">New Subscriber</a></div><h1>Customers</h1><form method="get"><div class="row"><input name="q" value="{html.escape(q)}" placeholder="Search account, name, company, email or phone"><div><button class="btn">Search</button></div></div></form><div class="muted" style="margin:8px 0 14px">Export downloads all customers currently matching this search. Clear the search to export the complete customer list.</div><table><tr><th>Account</th><th>Name</th><th>Customer Type</th><th>Company</th><th>Email</th><th>Status</th></tr>{trs}</table>''')


CUSTOMER_EXPORT_FIELDS = [
    ('account_no','Account Number'),
    ('first_name','First Name'),
    ('last_name','Last Name'),
    ('full_name','Customer Name'),
    ('customer_type','Customer Type'),
    ('company','Company'),
    ('email','Email'),
    ('phone','Phone'),
    ('service_address','Service Address'),
    ('billing_address','Billing Address'),
    ('city','City'),
    ('state','State'),
    ('zip','ZIP'),
    ('status','Customer Status'),
    ('service_status','Service Status'),
    ('service_plan','Service Plan'),
    ('billing_day','Billing Day'),
    ('contract_start','Contract Start'),
    ('contract_months','Contract Months'),
    ('signup_date','Service Signup Date'),
    ('member_since','Member Since'),
    ('created_at','CRM Record Created At'),
    ('notes','Customer Service Notes'),
]

@app.get('/customers/export',response_class=HTMLResponse)
def customers_export_choose(request:Request,q:str=''):
    require_staff(request)
    qesc=html.escape(q or '')
    checks=''.join(
        f"<label style='display:flex;gap:8px;align-items:center;margin:6px 0'><input type='checkbox' name='fields' value='{key}' {'checked' if key in ('full_name','email') else ''}> {html.escape(label)}</label>"
        for key,label in CUSTOMER_EXPORT_FIELDS
    )
    body = f"""
    <h1>Export Customer List</h1>
    <div class="card">
      <p>Select exactly which information should be included in the CSV. You can export only names and email addresses, or include the complete customer record including customer-service notes.</p>
      <form method="get" action="/customers/export.csv">
        <input type="hidden" name="q" value="{qesc}">
        <div class="actions" style="margin-bottom:12px">
          <button type="button" class="btn secondary" onclick="document.querySelectorAll('input[name=fields]').forEach(x=>x.checked=true)">Select All</button>
          <button type="button" class="btn secondary" onclick="document.querySelectorAll('input[name=fields]').forEach(x=>x.checked=false)">Deselect All</button>
          <button type="button" class="btn secondary" onclick="document.querySelectorAll('input[name=fields]').forEach(x=>x.checked=['full_name','email'].includes(x.value))">Name + Email</button>
        </div>
        <div style="columns:2;max-width:760px">{checks}</div>
        <div class="muted" style="margin:12px 0">Customer Service Notes exports all agent notes for each customer in one CSV cell, including category, timestamp, and agent name/email.</div>
        <button class="btn" type="submit">Download CSV</button>
        <a class="btn secondary" href="/customers">Cancel</a>
      </form>
    </div>
    """
    return page(request,'Export Customers',body)

@app.get('/customers/export.csv')
def customers_export_csv(request:Request,q:str='',fields:list[str]=[]):
    require_staff(request)
    allowed={k:v for k,v in CUSTOMER_EXPORT_FIELDS}
    chosen=[f for f in fields if f in allowed]
    if not chosen:
        chosen=['full_name','email']
    with conn() as c:
        sql="""SELECT c.id,c.account_no,c.first_name,c.last_name,c.customer_type,c.company,c.email,c.phone,c.service_address,c.billing_address,c.city,c.state,c.zip,c.status,c.service_status,c.billing_day,c.contract_start,c.contract_months,c.created_at,p.name AS service_plan
               FROM customers c
               LEFT JOIN subscriptions s ON s.customer_id=c.id AND s.status='Active'
               LEFT JOIN plans p ON p.id=s.plan_id"""
        params=()
        if q:
            like=f'%{q}%'
            sql += " WHERE c.account_no LIKE ? OR c.first_name LIKE ? OR c.last_name LIKE ? OR c.email LIKE ? OR c.phone LIKE ? OR c.company LIKE ?"
            params=(like,like,like,like,like,like)
        sql += " ORDER BY c.last_name COLLATE NOCASE,c.first_name COLLATE NOCASE,c.account_no"
        rows=c.execute(sql,params).fetchall()

        notes_by_customer={}
        if 'notes' in chosen and rows:
            ids=[r['id'] for r in rows]
            placeholders=','.join('?' for _ in ids)
            note_rows=c.execute(
                f"""SELECT customer_id,category,note,user_name,user_email,created_at
                    FROM customer_notes WHERE customer_id IN ({placeholders})
                    ORDER BY customer_id,created_at,id""",ids).fetchall()
            for n in note_rows:
                agent=(n['user_name'] or n['user_email'] or 'Unknown')
                if n['user_email'] and n['user_email'] not in agent:
                    agent=f"{agent} <{n['user_email']}>"
                line=f"[{n['created_at'] or ''}] {n['category'] or 'General'} — {agent}: {n['note'] or ''}"
                notes_by_customer.setdefault(n['customer_id'],[]).append(line)

    out=io.StringIO(newline='')
    writer=csv.writer(out)
    writer.writerow([allowed[f] for f in chosen])
    for r in rows:
        values={
            'account_no':r['account_no'] or '',
            'first_name':r['first_name'] or '',
            'last_name':r['last_name'] or '',
            'full_name':(' '.join(x for x in [r['first_name'] or '',r['last_name'] or ''] if x)).strip(),
            'customer_type':r['customer_type'] or 'Residential',
            'company':r['company'] or '',
            'email':r['email'] or '',
            'phone':r['phone'] or '',
            'service_address':r['service_address'] or '',
            'billing_address':r['billing_address'] or '',
            'city':r['city'] or '',
            'state':r['state'] or '',
            'zip':r['zip'] or '',
            'status':r['status'] or '',
            'service_status':r['service_status'] or '',
            'service_plan':r['service_plan'] or 'No Service Plan',
            'billing_day':r['billing_day'] or '',
            'contract_start':r['contract_start'] or '',
            'contract_months':r['contract_months'] or '',
            'signup_date':(r['contract_start'] or (str(r['created_at'] or '')[:10]) or ''),
            'member_since':(('Member Since '+(r['contract_start'] or str(r['created_at'] or '')[:10])[:4]) if (r['contract_start'] or str(r['created_at'] or '')[:10]) else ''),
            'created_at':r['created_at'] or '',
            'notes':'\\n'.join(notes_by_customer.get(r['id'],[])),
        }
        writer.writerow([values[f] for f in chosen])

    filename=f"entire_wireless_customers_{date.today().isoformat()}.csv"
    payload='\\ufeff'+out.getvalue()
    return Response(content=payload,media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="{filename}"','Cache-Control':'no-store'})

@app.get('/customers/new',response_class=HTMLResponse)
def customer_new(request:Request):
    require_staff(request)
    with conn() as c: plans=c.execute("SELECT * FROM plans WHERE active=1 ORDER BY name").fetchall()
    opts="<option value=''>No Service Plan</option>" + ''.join(f"<option value='{p['id']}'>{p['name']} — {money(p['monthly_price']+p['modem_lease'])}/mo</option>" for p in plans)
    return page(request,'New Customer',f'''<h1>New Subscriber</h1><form method="post"><div class="row"><div><label>Account Number</label><input value="Automatically assigned by customer type" disabled><div class="muted" style="margin-top:-8px;margin-bottom:12px">Residential accounts end in -0001; Business accounts end in -0002. The CRM assigns the next available 9-digit number automatically.</div><label>First Name</label><input name="first_name" required><label>Last Name</label><input name="last_name" required><label>Customer Type</label><select name="customer_type" required><option value="Residential">Residential</option><option value="Business">Business</option></select><div class="muted" style="margin-top:-8px;margin-bottom:12px">Every subscriber is classified as Residential or Business.</div><label>Company</label><input name="company"><label>Email</label><input type="email" name="email"><label>Phone</label><input name="phone"></div><div><label>Service Address</label><input name="service_address"><label>City</label><input name="city"><label>State</label><input name="state" value="IL"><label>ZIP</label><input name="zip"><label>Service Plan</label><select name="plan_id">{opts}</select><div class="muted" style="margin-top:-8px;margin-bottom:12px">Choose No Service Plan to create the customer without recurring service billing.</div><label>Billing Day (1-28)</label><input type="number" min="1" max="28" name="billing_day" value="{min(date.today().day,28)}"><label>Contract Start</label><input type="date" name="contract_start" value="{date.today().isoformat()}"><label>Contract Months</label><input type="number" name="contract_months" value="36"><label>Referred By (optional)</label><input name="referred_by" placeholder="Referral code or existing customer account number"><div class="muted" style="margin-top:-8px;margin-bottom:12px">The referral remains Pending until staff confirms this new customer qualifies. One qualified referral earns the referring customer one free modem-rental month.</div><label>Device Lease Promotion</label><select name="modem_promo_free_months"><option value="0">No Modem Rental Promotion</option><option value="6">6 Months Free Modem Rental</option></select><div class="muted" style="margin-top:-8px;margin-bottom:12px">When selected, the normal modem lease is waived for the first 6 recurring billing cycles. The regular modem lease automatically begins on billing cycle 7.</div><label>Initial Online Card Payment</label><select name="collect_first_payment"><option value="0">Create subscriber without taking payment now</option><option value="1">Create first monthly invoice and open secure Stripe Checkout</option></select><div class="muted" style="margin-top:-8px;margin-bottom:12px">Stripe hosts the card-entry screen, so card numbers are never stored in this CRM. After a successful first payment, recurring monthly invoices begin automatically and are emailed through the contract term.</div></div></div><label>Temporary Portal Password</label><input name="portal_password" placeholder="Customer can use this to sign in"><label>Notes</label><textarea name="notes"></textarea><button class="btn">Create Subscriber</button></form>''')

@app.post('/customers/new')
def customer_create(request:Request,first_name:str=Form(...),last_name:str=Form(...),customer_type:str=Form('Residential'),company:str=Form(''),email:str=Form(''),phone:str=Form(''),service_address:str=Form(''),city:str=Form(''),state:str=Form('IL'),zip:str=Form(''),plan_id:str=Form(''),billing_day:int=Form(1),contract_start:str=Form(''),contract_months:int=Form(36),modem_promo_free_months:int=Form(0),referred_by:str=Form(''),collect_first_payment:int=Form(0),portal_password:str=Form(''),notes:str=Form('')):
    require_staff(request)
    customer_type=(customer_type or 'Residential').strip().title()
    if customer_type not in ('Residential','Business'): raise HTTPException(400,'Customer type must be Residential or Business.')
    if int(collect_first_payment or 0)==1 and not str(plan_id).strip(): raise HTTPException(400,'Select a service plan before collecting the first monthly payment.')
    if int(collect_first_payment or 0)==1 and not STRIPE_SECRET_KEY: raise HTTPException(503,'Stripe is not configured.')
    try:
        with conn() as c:
            c.execute("BEGIN IMMEDIATE")
            account_customer_type='Residential' if customer_type=='Tablet' else customer_type
            account_no=generate_account_number(c,account_customer_type)
            promo_months=6 if int(modem_promo_free_months or 0)==6 else 0
            promo_name='6 Months Free Modem Rental' if promo_months else None
            promo_start=contract_start or date.today().isoformat() if promo_months else None
            cur=c.execute("INSERT INTO customers(account_no,first_name,last_name,customer_type,company,email,phone,service_address,city,state,zip,billing_day,contract_start,contract_months,portal_password_hash,notes,modem_promo_free_months,modem_promo_cycles_used,modem_promo_start,modem_promo_name) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(account_no,first_name,last_name,customer_type,company,email,phone,service_address,city,state,zip,billing_day,contract_start,contract_months,phash(portal_password) if portal_password else None,notes,promo_months,0,promo_start,promo_name)); cid=cur.lastrowid
            if str(plan_id).strip():
                c.execute("INSERT INTO subscriptions(customer_id,plan_id,start_date,status) VALUES (?,?,?,?)",(cid,int(plan_id),contract_start or date.today().isoformat(),'Active'))
        # Record an optional referral without granting the reward until staff qualifies it.
        refkey=(referred_by or '').strip()
        if refkey:
            with conn() as c:
                ref=c.execute("SELECT id FROM customers WHERE id<>? AND (referral_code=? OR account_no=?)",(cid,refkey,refkey)).fetchone()
                if ref: c.execute("INSERT OR IGNORE INTO customer_referrals(referrer_customer_id,referred_customer_id,status,notes) VALUES (?,?,?,?)",(ref['id'],cid,'Pending','Entered during customer creation'))
        audit(request,'CREATE','customer',cid,account_no); accounting_try('customer',cid)
        if int(collect_first_payment or 0)==1:
            # Hold future recurring billing until Stripe confirms this first payment.
            with conn() as c: c.execute("UPDATE customers SET billing_hold_until_first_payment=1 WHERE id=?",(cid,))
            iid=_recurring_invoice_for_customer(cid,date.today(),'AUTO')
            with conn() as c: c.execute("UPDATE customers SET initial_invoice_id=? WHERE id=?",(iid,cid))
            session=stripe_checkout_for_invoice(iid,f'{PUBLIC_URL}/payment/confirmation?session_id={{CHECKOUT_SESSION_ID}}',f'{PUBLIC_URL}/customers/{cid}',context='customer_signup')
            return RedirectResponse(session['url'],303)
        return RedirectResponse(f'/customers/{cid}',303)
    except sqlite3.IntegrityError as e: raise HTTPException(409,str(e))

@app.get('/customers/{cid}',response_class=HTMLResponse)
def customer_detail(request:Request,cid:int):
    require_staff(request)
    with conn() as c:
        r=c.execute('''SELECT c.*,p.name plan,p.monthly_price,p.modem_lease FROM customers c LEFT JOIN subscriptions s ON s.customer_id=c.id LEFT JOIN plans p ON p.id=s.plan_id WHERE c.id=?''',(cid,)).fetchone()
        if not r: raise HTTPException(404)
        ms=c.execute("SELECT * FROM modems WHERE customer_id=?",(cid,)).fetchall(); ss=c.execute("SELECT * FROM sims WHERE customer_id=?",(cid,)).fetchall(); inv=c.execute("SELECT * FROM invoices WHERE customer_id=? ORDER BY id DESC",(cid,)).fetchall(); avm=c.execute("SELECT * FROM modems WHERE customer_id IS NULL AND status='Available'").fetchall(); avs=c.execute("SELECT * FROM sims WHERE customer_id IS NULL AND status='Available'").fetchall(); docs=c.execute("SELECT * FROM customer_documents WHERE customer_id=? ORDER BY id DESC",(cid,)).fetchall()
        pending=c.execute("SELECT * FROM pending_charges WHERE customer_id=? AND applied_invoice_id IS NULL ORDER BY id",(cid,)).fetchall()
        support_notes=c.execute("SELECT * FROM customer_notes WHERE customer_id=? ORDER BY id DESC",(cid,)).fetchall()
        onboarding=c.execute("SELECT * FROM customer_onboarding WHERE customer_id=?",(cid,)).fetchone()
        referrals=c.execute("""SELECT cr.*,c.account_no,c.first_name,c.last_name FROM customer_referrals cr JOIN customers c ON c.id=cr.referred_customer_id WHERE cr.referrer_customer_id=? ORDER BY cr.id DESC""",(cid,)).fetchall()
        referred_by=c.execute("""SELECT cr.*,c.account_no,c.first_name,c.last_name FROM customer_referrals cr JOIN customers c ON c.id=cr.referrer_customer_id WHERE cr.referred_customer_id=?""",(cid,)).fetchone()
    signup_date=(r['contract_start'] or (str(r['created_at'] or '')[:10]) or '')
    member_year=(signup_date[:4] if len(signup_date)>=4 else '')
    bal=sum(x['subtotal']-x['amount_paid'] for x in inv if x['status']!='Void'); mo=''.join(f"<option value='{x['id']}'>{x['imei']} — {x['model'] or ''}</option>" for x in avm); so=''.join(f"<option value='{x['id']}'>{x['iccid']} — {x['carrier'] or ''}</option>" for x in avs)
    mrows=''.join(f"<tr><td>{x['imei']}</td><td>{x['manufacturer'] or ''} {x['model'] or ''}</td><td>{x['status']}</td><td><form method='post' action='/equipment/unassign/modem/{x['id']}' onsubmit=\"return confirm('Unassign this modem and return it to available inventory?')\"><input type='hidden' name='customer_id' value='{cid}'><input type='hidden' name='disposition' value='Available'><input type='hidden' name='reason' value='Released from customer'><button class='btn secondary' type='submit'>Unassign & Reuse</button></form></td></tr>" for x in ms) or '<tr><td colspan=4>None assigned.</td></tr>'
    srows=''.join(f"<tr><td>{x['iccid']}</td><td>{x['carrier'] or ''}</td><td>{x['mdn'] or ''}</td><td><form method='post' action='/equipment/unassign/sim/{x['id']}' onsubmit=\"return confirm('Unassign this SIM and return it to available inventory?')\"><input type='hidden' name='customer_id' value='{cid}'><input type='hidden' name='disposition' value='Available'><input type='hidden' name='reason' value='Released from customer'><button class='btn secondary' type='submit'>Unassign & Reuse</button></form></td></tr>" for x in ss) or '<tr><td colspan=4>None assigned.</td></tr>'
    irows=''.join(f"<tr><td><a href='/invoices/{x['id']}'>{x['invoice_no']}</a></td><td>{x['issue_date']}</td><td>{money(x['subtotal'])}</td><td>{money(0 if x['status']=='Void' else x['subtotal']-x['amount_paid'])}</td><td>{x['status']}</td></tr>" for x in inv) or '<tr><td colspan=5>No invoices.</td></tr>'

    drows=''.join(f"<tr><td><a href='/customers/{cid}/documents/{x['id']}'>{x['original_name']}</a></td><td>{x['document_type'] or ''}</td><td>{x['uploaded_at'] or ''}</td><td>{(x['size_bytes'] or 0)/1024:.1f} KB</td><td><form method='post' action='/customers/{cid}/documents/{x['id']}/delete' onsubmit=\"return confirm('Delete this document from the customer record?')\"><button class='btn danger' type='submit'>Delete</button></form></td></tr>" for x in docs) or '<tr><td colspan=5>No documents uploaded.</td></tr>'
    pcparts=[]
    for x in pending:
        action=''
        if role(request)=='admin':
            action=f"<form method='post' action='/customers/{cid}/pending-charges/{x['id']}/reverse'><button class='btn secondary' type='submit'>Reverse Pending Charge</button></form>"
        pcparts.append(f"<tr><td>{x['description']}</td><td>{money(x['amount'])}</td><td>{x['created_at']}</td><td>{action}</td></tr>")
    pcrows=''.join(pcparts) or '<tr><td colspan=4 class="muted">No pending charges.</td></tr>'
    note_rows=''.join(f"<tr><td>{html.escape(str(x['created_at'] or ''))}</td><td><span class='pill'>{html.escape(str(x['category'] or 'General'))}</span></td><td>{html.escape(str(x['user_name'] or x['user_email'] or 'Unknown'))}</td><td style='white-space:pre-wrap'>{html.escape(str(x['note'] or ''))}</td></tr>" for x in support_notes) or '<tr><td colspan=4 class="muted">No support notes yet.</td></tr>'
    note_categories=''.join(f"<option>{x}</option>" for x in ['Technical Support','Billing Support','Customer Service','Sales','Installation','Collections','Account Management','General'])
    remaining=whole_months_remaining(r['contract_start'] or '', int(r['contract_months'] or 36), date.today())
    etf_preview=remaining*EARLY_TERMINATION_MONTHLY_FEE
    lifecycle=(f"<form method='post' action='/customers/{cid}/deactivate' onsubmit=\"return confirm('Deactivate this customer, stop recurring billing, and create any selected cancellation charges?')\"><label>Cancellation / deactivation reason</label><input name='reason' value='Customer cancelled service' required><label><input style='width:auto;margin-right:8px' type='checkbox' name='apply_early_termination_fee' value='1' checked>Generate early termination fee invoice: {money(EARLY_TERMINATION_MONTHLY_FEE)} × {remaining} remaining whole month(s) = {money(etf_preview)}</label><label><input style='width:auto;margin-right:8px' type='checkbox' name='unreturned_equipment' value='1'>Equipment has NOT been returned — generate {money(UNRETURNED_EQUIPMENT_FEE)} unreturned equipment invoice</label><label><input style='width:auto;margin-right:8px' type='checkbox' name='release_equipment' value='1' checked>Release assigned modems and SIMs back to Available inventory if equipment was returned</label><p class='muted'>If “Equipment has NOT been returned” is selected, assigned equipment stays tied to the cancelled customer and is marked Unreturned instead of being released.</p><button class='btn danger' type='submit'>Deactivate Customer & Create Charges</button></form>" if r['status']=='Active' else f"<div class='notice'><b>Customer deactivated:</b> {r['deactivated_at'] or ''}<br>{r['deactivation_reason'] or ''}</div><form method='post' action='/customers/{cid}/reactivate' onsubmit=\"return confirm('Reactivate this customer in the CRM?')\"><button class='btn ok' type='submit'>Reactivate Customer</button></form>")
    reward_balance=referral_reward_balance(cid)
    refrows=''.join(f"<tr><td><a href='/customers/{x['referred_customer_id']}'>{html.escape(x['first_name']+' '+x['last_name'])}</a><br><span class='muted'>{html.escape(x['account_no'])}</span></td><td>{html.escape(x['status'])}</td><td>{int(x['reward_months'] or 0)}</td><td>{html.escape(str(x['qualified_at'] or x['created_at'] or ''))}</td></tr>" for x in referrals) or '<tr><td colspan=4 class="muted">No referrals yet.</td></tr>'
    referred_by_text=(f"Referred by <a href='/customers/{referred_by['referrer_customer_id']}'>{html.escape(referred_by['first_name']+' '+referred_by['last_name'])}</a> · {html.escape(referred_by['status'])}" if referred_by else 'No referring customer recorded.')
    referral_card=f"""<div class='section card'><h2>Customer Referral Program</h2><div class='grid'><div class='card'><div class='muted'>Referral Code</div><b>{html.escape(str(r['referral_code'] or ''))}</b></div><div class='card'><div class='muted'>Free Modem Months Available</div><div class='metric'>{reward_balance}</div></div><div class='card'><div class='muted'>Value Available</div><div class='metric'>{money(reward_balance*10)}</div></div></div><p class='muted'>Each qualified new-customer referral earns one free month of the $10 modem rental. Rewards accumulate and are automatically used only after any existing free-modem promotion has been exhausted.</p><p>{referred_by_text}</p><table><tr><th>Referred Customer</th><th>Status</th><th>Months Earned</th><th>Date</th></tr>{refrows}</table><div class='actions' style='margin-top:12px'><a class='btn secondary' href='/customers/{cid}/referrals'>Manage Referrals</a></div></div>"""

    return page(request,'Customer',f'''<div class="actions right"><a class="btn" href="/invoices/new?customer_id={cid}">New Invoice</a><a class="btn secondary" href="/customers/{cid}/edit">Edit Customer</a><a class="btn secondary" target="_blank" href="/reports/customers/{cid}.pdf">Print Customer Report</a><a class="btn secondary" href="/customers/{cid}/portal-password">Set Portal Password</a><a class="btn secondary" href="/messages?customer_id={cid}">Customer Messages</a><a class="btn secondary" href="/collections?customer_id={cid}">Internal Collections</a></div><h1>{r['first_name']} {r['last_name']} <span class="pill">{r['customer_type'] or 'Residential'}</span> <span class="pill">{r['status']}</span></h1><div class="grid"><div class="card"><div class="muted">Account</div><b>{r['account_no']}</b><div>{r['customer_type'] or 'Residential'} Customer</div></div><div class="card"><div class="muted">Customer Since</div><b>{signup_date or 'Not recorded'}</b><div>{('Member Since '+member_year) if member_year else 'Member Since —'}</div></div><div class="card"><div class="muted">Plan</div><b>{r['plan'] or 'None'}</b><div>{money((r['monthly_price'] or 0)+(r['modem_lease'] or 0))}/mo</div></div><div class="card"><div class="muted">Open Balance</div><div class="metric">{money(bal)}</div></div><div class="card"><div class="muted">Contract</div><b>{r['contract_months']} months</b><div>{r['contract_start'] or ''}</div></div><div class="card"><div class="muted">Network Service</div><b>{r['service_status'] or 'Active'}</b><div class="actions" style="margin-top:8px">{('<span class="muted">Customer is inactive</span>' if r['status']!='Active' else ('<a class="btn danger" href="/carrier/'+str(cid)+'/suspend">Suspend</a>' if (r['service_status'] or 'Active')=='Active' else '<a class="btn ok" href="/carrier/'+str(cid)+'/restore">Restore</a>'))}</div></div></div><div class="section card"><h2>Contact & Service</h2><div class="row"><div>{r['email'] or ''}<br>{r['phone'] or ''}</div><div>{r['service_address'] or ''}<br>{r['city'] or ''}, {r['state'] or ''} {r['zip'] or ''}</div></div></div><div class="section card"><div class="actions right"><a class="btn secondary" href="/customers/{cid}/onboarding">Manage Onboarding</a></div><h2>Customer Onboarding</h2><p><b>Current stage: {html.escape(onboarding['stage'] if onboarding else 'Not started')}</b></p>{onboarding_progress_html(onboarding) if onboarding else '<p class=muted>No onboarding workflow has been started for this customer.</p>'}</div><div class="section card"><h2>Recurring Billing</h2><p><b>{('Waiting for successful first Stripe payment' if int(r['billing_hold_until_first_payment'] or 0) else 'Active')}</b></p><p class="muted">{('Future monthly invoices are on hold until the first online payment is confirmed.' if int(r['billing_hold_until_first_payment'] or 0) else ('Monthly invoices are generated on billing day '+str(r['billing_day'])+' and emailed automatically. For fixed-term agreements, generation stops at the end of the '+str(r['contract_months'])+'-month term.' if int(r['contract_months'] or 0)>0 else 'Monthly invoices are generated and emailed automatically until the subscription is changed or cancelled.'))}</p></div><div class="section card"><h2>Device Lease Promotion</h2><p><b>{html.escape(r['modem_promo_name'] or 'No active modem rental promotion')}</b></p><p class="muted">{(f"{max(0,int(r['modem_promo_free_months'] or 0)-int(r['modem_promo_cycles_used'] or 0))} of {int(r['modem_promo_free_months'] or 0)} free modem-rental billing cycles remaining. The normal {money(r['modem_lease'] or 0)} monthly device lease begins automatically after the promotional cycles are used." if int(r['modem_promo_free_months'] or 0)>0 else 'No modem lease promotion is assigned to this customer.')}</p></div>{referral_card}<div class="section row"><div class="card"><h2>Assigned Modems</h2><table><tr><th>IMEI</th><th>Model</th><th>Status</th><th>Inventory Action</th></tr>{mrows}</table><form method="post" action="/equipment/assign/modem"><input type="hidden" name="customer_id" value="{cid}"><select name="equipment_id">{mo}</select><button class="btn">Assign Modem</button></form></div><div class="card"><h2>Assigned SIMs</h2><table><tr><th>ICCID</th><th>Carrier</th><th>MDN</th><th>Inventory Action</th></tr>{srows}</table><form method="post" action="/equipment/assign/sim"><input type="hidden" name="customer_id" value="{cid}"><select name="equipment_id">{so}</select><button class="btn">Assign SIM</button></form></div></div><div class="section card"><h2>Equipment Release</h2><p class="muted">Use this when service ends or equipment is returned. It removes all modem/SIM assignments from this subscriber while preserving the equipment history, then returns the equipment to Available inventory so it can be assigned to another customer.</p><form method="post" action="/customers/{cid}/release-equipment" onsubmit="return confirm('Release ALL assigned modems and SIMs from this customer?')"><label>Release reason</label><input name="reason" value="Customer ended service / equipment returned"><button class="btn secondary" type="submit">Release All Equipment to Inventory</button></form></div><div class="section card"><h2>Nonpayment Automation</h2><form method="post" action="/customers/{cid}/carrier-policy"><div class="row"><div><label>Suspension Exemption</label><select name="suspension_exempt"><option value="0" {'selected' if not r['suspension_exempt'] else ''}>No - follow normal suspension policy</option><option value="1" {'selected' if r['suspension_exempt'] else ''}>Yes - never auto-suspend</option></select></div><div><label>Payment Arrangement</label><select name="payment_arrangement"><option value="0" {'selected' if not r['payment_arrangement'] else ''}>No</option><option value="1" {'selected' if r['payment_arrangement'] else ''}>Yes - temporarily block auto-suspension</option></select></div></div><button class="btn secondary">Save Carrier Policy</button></form></div><div class="section card"><h2>Customer Support Notes</h2><p class="muted">Each note is permanently time stamped and attributed to the logged-in employee.</p><form method="post" action="/customers/{cid}/notes"><div class="row"><div><label>Department / Note Type</label><select name="category">{note_categories}</select></div><div></div></div><label>Support Note</label><textarea name="note" required placeholder="Enter the customer interaction, troubleshooting, billing discussion, follow-up, or other account note..."></textarea><button class="btn" type="submit">Add Time-Stamped Note</button></form><div style="overflow-x:auto;margin-top:18px"><table><tr><th>Date / Time</th><th>Department</th><th>Employee</th><th>Note</th></tr>{note_rows}</table></div></div><div class="section card"><h2>Customer Documents</h2><p class="muted">Upload signed service agreements, contracts, amendments, identification/supporting paperwork, or other customer documents. Supported formats: PDF, Word, PNG, JPG. Maximum {MAX_DOCUMENT_BYTES//(1024*1024)} MB per file.</p><table><tr><th>Document</th><th>Type</th><th>Uploaded</th><th>Size</th><th>Action</th></tr>{drows}</table><form method="post" action="/customers/{cid}/documents" enctype="multipart/form-data"><div class="row"><div><label>Document Type</label><select name="document_type"><option>Customer Agreement / Contract</option><option>Acceptable Use Policy</option><option>Contract Amendment</option><option>Installation / Work Order</option><option>Cancellation / Termination</option><option>Other</option></select></div><div><label>Select File</label><input type="file" name="document" accept=".pdf,.doc,.docx,.png,.jpg,.jpeg" required></div></div><label>Notes</label><input name="notes" placeholder="Optional document notes"><button class="btn" type="submit">Upload Document</button></form></div><div class="section card"><h2>SIM Replacement Charge</h2><p class="muted">Queue a {money(SIM_REPLACEMENT_FEE)} SIM Card Replacement Fee to appear on this customer's next monthly invoice.</p><form method="post" action="/customers/{cid}/sim-replacement-fee" onsubmit="return confirm('Add a SIM Card Replacement Fee to the next monthly invoice?')"><button class="btn secondary" type="submit">Add {money(SIM_REPLACEMENT_FEE)} SIM Replacement Fee</button></form></div><div class="section card"><h2>Pending Charges</h2><p class="muted">Charges waiting to be added to the next recurring invoice. Administrators can reverse a pending charge before it is billed.</p><table><tr><th>Description</th><th>Amount</th><th>Queued</th><th>Action</th></tr>{pcrows}</table></div><div class="section card"><h2>Customer Status</h2><p class="muted">Deactivation preserves billing, payment, document, audit, and equipment history while stopping future recurring invoices and disabling customer portal access.</p>{lifecycle}</div><div class="section card"><h2>Permanent Customer Deletion</h2><p class="muted">Administrators can permanently remove test, duplicate, or mistakenly-created customer records. This deletes the customer and their CRM invoices, payments, notes, documents, pending charges, subscriptions, carrier history, and accounting sync links. Assigned equipment is returned to Available inventory. This does not delete records already created inside Zoho Books or QuickBooks.</p><form method="post" action="/customers/{cid}/delete" onsubmit="return confirm('PERMANENTLY DELETE this customer and all of their CRM billing history? This cannot be undone.');"><label>Type DELETE to confirm</label><input name="confirmation" required autocomplete="off" placeholder="DELETE"><label>Reason</label><input name="reason" value="Test / duplicate customer" required><button class="btn danger" type="submit">Permanently Delete Customer</button></form></div><div class="section card"><h2>Billing History</h2><table><tr><th>Invoice</th><th>Date</th><th>Total</th><th>Balance</th><th>Status</th></tr>{irows}</table></div>''')

@app.get('/customers/{cid}/referrals',response_class=HTMLResponse)
def customer_referrals_page(request:Request,cid:int):
    require_staff(request)
    with conn() as c:
        cust=c.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone()
        if not cust: raise HTTPException(404)
        refs=c.execute("""SELECT cr.*,x.account_no,x.first_name,x.last_name FROM customer_referrals cr JOIN customers x ON x.id=cr.referred_customer_id WHERE cr.referrer_customer_id=? ORDER BY cr.id DESC""",(cid,)).fetchall()
        candidates=c.execute("SELECT id,account_no,first_name,last_name FROM customers WHERE id<>? ORDER BY last_name,first_name",(cid,)).fetchall()
    rows=''.join(f"<tr><td>{html.escape(x['first_name']+' '+x['last_name'])}<br><span class='muted'>{html.escape(x['account_no'])}</span></td><td>{html.escape(x['status'])}</td><td>{int(x['reward_months'] or 0)}</td><td>{('<form method=post action=/referrals/'+str(x['id'])+'/qualify><button class=\"btn ok\">Qualify & Award 1 Month</button></form>' if x['status']=='Pending' else '')}</td></tr>" for x in refs) or '<tr><td colspan=4>No referrals recorded.</td></tr>'
    opts=''.join(f"<option value='{x['id']}'>{html.escape(x['last_name']+', '+x['first_name']+' — '+x['account_no'])}</option>" for x in candidates)
    return page(request,'Customer Referrals',f"""<div class='actions right'><a class='btn secondary' href='/customers/{cid}'>Back to Customer</a></div><h1>Customer Referral Program</h1><div class='notice'><b>{html.escape(cust['first_name']+' '+cust['last_name'])}</b> · Account {html.escape(cust['account_no'])}<br>Referral code: <b>{html.escape(str(cust['referral_code'] or ''))}</b> · Available free modem months: <b>{referral_reward_balance(cid)}</b></div><div class='card'><h2>Record a Referral</h2><form method='post' action='/customers/{cid}/referrals'><label>New Customer</label><select name='referred_customer_id' required>{opts}</select><label>Notes</label><input name='notes' placeholder='Optional referral notes'><button class='btn'>Record Pending Referral</button></form></div><div class='section card'><h2>Referral History</h2><table><tr><th>New Customer</th><th>Status</th><th>Reward Months</th><th>Action</th></tr>{rows}</table></div>""")

@app.post('/customers/{cid}/referrals')
def customer_referrals_add(request:Request,cid:int,referred_customer_id:int=Form(...),notes:str=Form('')):
    require_staff(request)
    if cid==referred_customer_id: raise HTTPException(400,'A customer cannot refer themselves.')
    try:
        with conn() as c:
            c.execute("INSERT INTO customer_referrals(referrer_customer_id,referred_customer_id,status,notes) VALUES (?,?,?,?)",(cid,referred_customer_id,'Pending',notes.strip()))
    except sqlite3.IntegrityError:
        raise HTTPException(400,'That new customer already has a referring customer recorded.')
    audit(request,'CREATE','customer_referral',referred_customer_id,f'referrer_customer={cid}; status=Pending')
    return RedirectResponse(f'/customers/{cid}/referrals',303)

@app.post('/referrals/{rid}/qualify')
def referral_qualify(request:Request,rid:int):
    require_staff(request)
    with conn() as c:
        rr=c.execute("SELECT * FROM customer_referrals WHERE id=?",(rid,)).fetchone()
        if not rr: raise HTTPException(404)
        if rr['status']!='Pending': return RedirectResponse(f"/customers/{rr['referrer_customer_id']}/referrals",303)
        now=datetime.now().isoformat(timespec='seconds')
        who=request.session.get('email','Staff')
        c.execute("UPDATE customer_referrals SET status='Qualified',reward_months=1,qualified_at=?,qualified_by=? WHERE id=?",(now,who,rid))
        c.execute("INSERT INTO referral_reward_ledger(customer_id,referral_id,months,entry_type,notes,created_by) VALUES (?,?,?,?,?,?)",(rr['referrer_customer_id'],rid,1,'Earned','Qualified customer referral — one free modem-rental month',who))
    audit(request,'QUALIFY','customer_referral',rid,'Awarded 1 free modem-rental month')
    return RedirectResponse(f"/customers/{rr['referrer_customer_id']}/referrals",303)

@app.get('/customers/{cid}/onboarding',response_class=HTMLResponse)
def customer_onboarding_page(request:Request,cid:int):
    require_staff(request)
    with conn() as c:
        cust=c.execute('SELECT * FROM customers WHERE id=?',(cid,)).fetchone()
        if not cust: raise HTTPException(404)
        ob=c.execute('SELECT * FROM customer_onboarding WHERE customer_id=?',(cid,)).fetchone()
    if not ob:
        ensure_onboarding(cid,None,'Order Received')
        with conn() as c: ob=c.execute('SELECT * FROM customer_onboarding WHERE customer_id=?',(cid,)).fetchone()
    opts=''.join(f"<option value='{html.escape(st)}' {'selected' if st==ob['stage'] else ''}>{html.escape(st)}</option>" for st in ONBOARDING_STAGES)
    return page(request,'Customer Onboarding',f"""<div class='actions right'><a class='btn secondary' href='/customers/{cid}'>Back to Customer</a></div><h1>Customer Onboarding</h1><div class='notice'><b>{html.escape(cust['first_name']+' '+cust['last_name'])}</b> · Account {html.escape(cust['account_no'])}<br>Use this workflow to move the subscriber from order/payment through equipment, provisioning, and activation.</div><div class='row'><div class='card'><h2>Progress</h2>{onboarding_progress_html(ob)}</div><div class='card'><h2>Update Onboarding</h2><form method='post'><label>Current Stage</label><select name='stage'>{opts}</select><label>Internal Staff Notes</label><textarea name='staff_notes' rows='8'>{html.escape(str(ob['staff_notes'] or ''))}</textarea><button class='btn'>Save Onboarding Status</button></form><p class='muted'>WooCommerce order: {('#'+str(ob['woo_order_id'])) if ob['woo_order_id'] else 'Manual / none'}</p></div></div>""")

@app.post('/customers/{cid}/onboarding')
def customer_onboarding_save(request:Request,cid:int,stage:str=Form(...),staff_notes:str=Form('')):
    require_staff(request)
    if stage not in ONBOARDING_STAGES: raise HTTPException(400,'Invalid onboarding stage.')
    ensure_onboarding(cid,None,stage)
    now=datetime.now().isoformat(timespec='seconds')
    col={'Order Received':'order_received_at','Payment Confirmed':'payment_confirmed_at','Agreement Signed':'agreement_signed_at','Equipment Assignment':'equipment_assigned_at','Provisioning':'provisioning_started_at','Ready for Service':'ready_for_service_at','Active':'activated_at'}.get(stage)
    with conn() as c:
        c.execute('UPDATE customer_onboarding SET stage=?,staff_notes=?,updated_at=? WHERE customer_id=?',(stage,staff_notes.strip(),now,cid))
        if col: c.execute(f"UPDATE customer_onboarding SET {col}=COALESCE({col},?) WHERE customer_id=?",(now,cid))
    audit(request,'UPDATE','customer_onboarding',cid,f'stage={stage}')
    return RedirectResponse(f'/customers/{cid}',303)

@app.get('/customers/{cid}/edit',response_class=HTMLResponse)
def customer_edit(request:Request,cid:int):
    require_staff(request)
    with conn() as c:
        r=c.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone()
        if not r: raise HTTPException(404)
        plans=c.execute("SELECT * FROM plans WHERE active=1 ORDER BY name").fetchall()
        sub=c.execute("SELECT * FROM subscriptions WHERE customer_id=?",(cid,)).fetchone()
    current_plan=int(sub['plan_id']) if sub else 0
    opts=f"<option value='' {'selected' if current_plan==0 else ''}>No Service Plan</option>" + ''.join(f"<option value='{p['id']}' {'selected' if int(p['id'])==current_plan else ''}>{p['name']} — {money(p['monthly_price']+p['modem_lease'])}/mo</option>" for p in plans)
    def val(k): return str(r[k] or '').replace('&','&amp;').replace('"','&quot;').replace('<','&lt;').replace('>','&gt;')
    body = f"""<div class='actions right'><a class='btn secondary' href='/customers/{cid}'>Cancel</a></div><h1>Edit Customer</h1><div class='notice'><b>Customer information can be updated at any time.</b> Changes are saved to the CRM immediately. When Zoho Books is the active accounting provider, linked contact information is also updated in Zoho.</div><form method='post'><div class='row'><div><label>Account Number</label>{(f"<input name='account_no' value='{val('account_no')}' required><div class='muted' style='margin-top:-8px;margin-bottom:12px'>Administrator override enabled. Changing this updates the customer's CRM account number used by the portal, invoices, reports, collection letters, and future generated documents. The change is recorded in the Audit Log.</div>" if role(request)=='admin' else f"<input value='{val('account_no')}' readonly><input type='hidden' name='account_no' value='{val('account_no')}'><div class='muted' style='margin-top:-8px;margin-bottom:12px'>Only an administrator can change an existing account number.</div>")}<label>First Name</label><input name='first_name' value='{val('first_name')}' required><label>Last Name</label><input name='last_name' value='{val('last_name')}' required><label>Customer Type</label><select name='customer_type' required><option value='Residential' {'selected' if (r['customer_type'] or 'Residential')=='Residential' else ''}>Residential</option><option value='Business' {'selected' if r['customer_type']=='Business' else ''}>Business</option></select><label>Company Name</label><input name='company' value='{val('company')}'><label>Email</label><input type='email' name='email' value='{val('email')}'><label>Phone</label><input name='phone' value='{val('phone')}'></div><div><label>Service Address</label><input name='service_address' value='{val('service_address')}'><label>Billing Address</label><input name='billing_address' value='{val('billing_address')}' placeholder='Leave blank to use service address'><label>City</label><input name='city' value='{val('city')}'><label>State</label><input name='state' value='{val('state')}'><label>ZIP</label><input name='zip' value='{val('zip')}'><label>Service Plan</label><select name='plan_id'>{opts}</select><div class='muted' style='margin-top:-8px;margin-bottom:12px'>Choose No Service Plan to remove the current subscription and stop plan-based recurring billing for this customer.</div></div></div><div class='row'><div><label>Billing Day (1-28)</label><input type='number' min='1' max='28' name='billing_day' value='{int(r['billing_day'] or 1)}'></div><div><label>Contract Start</label><input type='date' name='contract_start' value='{val('contract_start')}'></div></div><label>Contract Months</label><input type='number' min='0' name='contract_months' value='{int(r['contract_months'] or 0)}'><label>Device Lease Promotion</label><select name='modem_promo_free_months'><option value='0' {'selected' if int(r['modem_promo_free_months'] or 0)==0 else ''}>No Modem Rental Promotion</option><option value='6' {'selected' if int(r['modem_promo_free_months'] or 0)==6 else ''}>6 Months Free Modem Rental</option></select><div class='muted' style='margin-top:-8px;margin-bottom:12px'>Progress: {int(r['modem_promo_cycles_used'] or 0)} of {int(r['modem_promo_free_months'] or 0)} free billing cycles used. Removing and later re-adding the promotion starts a new 6-cycle promotion.</div><button class='btn' type='submit'>Save Customer Changes</button></form>"""
    return page(request,'Edit Customer',body)

@app.post('/customers/{cid}/edit')
def customer_edit_save(request:Request,cid:int,account_no:str=Form(...),first_name:str=Form(...),last_name:str=Form(...),customer_type:str=Form('Residential'),company:str=Form(''),email:str=Form(''),phone:str=Form(''),service_address:str=Form(''),billing_address:str=Form(''),city:str=Form(''),state:str=Form(''),zip:str=Form(''),plan_id:str=Form(''),billing_day:int=Form(1),contract_start:str=Form(''),contract_months:int=Form(36),modem_promo_free_months:int=Form(0)):
    require_staff(request)
    account_no=account_no.strip(); first_name=first_name.strip(); last_name=last_name.strip(); customer_type=(customer_type or 'Residential').strip().title()
    if not account_no or not first_name or not last_name: raise HTTPException(400,'Account number, first name, and last name are required.')
    if customer_type not in ('Residential','Business'): raise HTTPException(400,'Customer type must be Residential or Business.')
    if billing_day < 1 or billing_day > 28: raise HTTPException(400,'Billing day must be between 1 and 28.')
    try:
        with conn() as c:
            old=c.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone()
            if not old: raise HTTPException(404)
            # Existing account numbers are immutable for staff. Administrators may
            # explicitly override them when correcting an account. Do not silently
            # regenerate or rewrite an administrator-entered number.
            old_account_no=str(old['account_no'] or '').strip()
            if role(request) != 'admin':
                account_no=old_account_no
            else:
                account_no=account_no.strip()
                if not account_no:
                    raise HTTPException(400,'Account number is required.')
                # Permit the CRM's normal 9-digit + 4-digit suffix format and
                # legacy 9-digit account numbers already used by Entire Wireless.
                import re
                if not re.fullmatch(r'\d{9}(?:-\d{4})?', account_no):
                    raise HTTPException(400,'Account number must be 9 digits, optionally followed by a 4-digit suffix (example: 100000001-0001).')
                duplicate=c.execute("SELECT id FROM customers WHERE account_no=? AND id<>?",(account_no,cid)).fetchone()
                if duplicate:
                    raise HTTPException(409,'That account number is already in use by another customer.')
            promo_months=6 if int(modem_promo_free_months or 0)==6 else 0
            old_promo=int(old['modem_promo_free_months'] or 0)
            promo_used=int(old['modem_promo_cycles_used'] or 0) if promo_months==old_promo and promo_months else 0
            promo_start=(old['modem_promo_start'] or contract_start or date.today().isoformat()) if promo_months else None
            promo_name='6 Months Free Modem Rental' if promo_months else None
            c.execute("UPDATE customers SET account_no=?,first_name=?,last_name=?,customer_type=?,company=?,email=?,phone=?,service_address=?,billing_address=?,city=?,state=?,zip=?,billing_day=?,contract_start=?,contract_months=?,modem_promo_free_months=?,modem_promo_cycles_used=?,modem_promo_start=?,modem_promo_name=? WHERE id=?",(account_no,first_name,last_name,customer_type,company.strip(),email.strip(),phone.strip(),service_address.strip(),billing_address.strip(),city.strip(),state.strip(),zip.strip(),billing_day,contract_start,contract_months,promo_months,promo_used,promo_start,promo_name,cid))
            sub=c.execute("SELECT id,plan_id FROM subscriptions WHERE customer_id=?",(cid,)).fetchone()
            selected_plan=str(plan_id).strip()
            if selected_plan:
                selected_plan_id=int(selected_plan)
                if sub: c.execute("UPDATE subscriptions SET plan_id=?,status='Active' WHERE customer_id=?",(selected_plan_id,cid))
                else: c.execute("INSERT INTO subscriptions(customer_id,plan_id,start_date,status) VALUES (?,?,?,?)",(cid,selected_plan_id,contract_start or date.today().isoformat(),'Active'))
            elif sub:
                c.execute("DELETE FROM subscriptions WHERE customer_id=?",(cid,))
        plan_note = f'plan={plan_id}' if str(plan_id).strip() else 'plan=None'
        audit(request,'UPDATE','customer',cid,f'Customer profile updated: {old["account_no"]} -> {account_no}; type={customer_type}; {plan_note}')
        if ACCOUNTING_PROVIDER=='zoho' and ZOHO_ENABLED:
            try: zoho_update_customer(cid)
            except Exception as e:
                with conn() as c: c.execute("UPDATE customers SET zoho_sync_status='Failed',zoho_sync_error=? WHERE id=?",(str(e)[:2000],cid))
                _zoho_log('customer',cid,'update','Failed','',str(e))
        elif ACCOUNTING_PROVIDER=='quickbooks' and QUICKBOOKS_ENABLED:
            with conn() as c: c.execute("UPDATE customers SET quickbooks_sync_status='Needs Update',quickbooks_sync_error='CRM customer profile changed; QuickBooks customer update is not automatic in this release.' WHERE id=?",(cid,))
        return RedirectResponse(f'/customers/{cid}',303)
    except sqlite3.IntegrityError:
        raise HTTPException(409,'That account number is already in use.')

@app.post('/customers/{cid}/notes')
def customer_note_add(request:Request,cid:int,category:str=Form('General'),note:str=Form(...)):
    require_staff(request)
    category=category.strip() or 'General'; note=note.strip()
    allowed={'Technical Support','Billing Support','Customer Service','Sales','Installation','Collections','Account Management','General'}
    if category not in allowed: raise HTTPException(400,'Invalid note category')
    if not note: raise HTTPException(400,'Note is required')
    uid=request.session.get('user_id'); email=request.session.get('user_email','')
    with conn() as c:
        if not c.execute("SELECT 1 FROM customers WHERE id=?",(cid,)).fetchone(): raise HTTPException(404,'Customer not found')
        u=c.execute("SELECT name,email FROM users WHERE id=?",(uid,)).fetchone() if uid else None
        uname=(u['name'] if u else '') or email or 'Unknown'; uemail=(u['email'] if u else email) or email
        cur=c.execute("INSERT INTO customer_notes(customer_id,category,note,user_id,user_name,user_email) VALUES (?,?,?,?,?,?)",(cid,category,note,uid,uname,uemail)); nid=cur.lastrowid
    audit(request,'CREATE','customer_note',nid,f'customer={cid}; category={category}')
    return RedirectResponse(f'/customers/{cid}',303)

@app.post('/customers/{cid}/documents')
async def customer_document_upload(request:Request,cid:int,document_type:str=Form('Customer Agreement / Contract'),notes:str=Form(''),document:UploadFile=File(...)):
    require_staff(request)
    with conn() as c:
        if not c.execute("SELECT 1 FROM customers WHERE id=?",(cid,)).fetchone(): raise HTTPException(404,'Customer not found')
    original=Path(document.filename or 'document').name
    ext=Path(original).suffix.lower()
    if ext not in ALLOWED_DOCUMENT_EXTENSIONS: raise HTTPException(400,'Unsupported document type. Upload PDF, DOC, DOCX, PNG, JPG, or JPEG.')
    data=await document.read(MAX_DOCUMENT_BYTES+1)
    if len(data)>MAX_DOCUMENT_BYTES: raise HTTPException(413,f'Document exceeds {MAX_DOCUMENT_BYTES//(1024*1024)} MB limit')
    customer_dir=DOCUMENTS / str(cid); customer_dir.mkdir(parents=True,exist_ok=True)
    stored=f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(6)}{ext}"
    path=customer_dir/stored; path.write_bytes(data)
    with conn() as c:
        cur=c.execute("INSERT INTO customer_documents(customer_id,original_name,stored_name,document_type,notes,content_type,size_bytes,uploaded_by) VALUES (?,?,?,?,?,?,?,?)",(cid,original,stored,document_type,notes,document.content_type or '',len(data),request.session.get('user_email','')))
        did=cur.lastrowid
    audit(request,'UPLOAD','customer_document',did,f'customer={cid}; file={original}; type={document_type}')
    return RedirectResponse(f'/customers/{cid}',303)

@app.get('/customers/{cid}/documents/{did}')
def customer_document_download(request:Request,cid:int,did:int):
    require_staff(request)
    with conn() as c: d=c.execute("SELECT * FROM customer_documents WHERE id=? AND customer_id=?",(did,cid)).fetchone()
    if not d: raise HTTPException(404,'Document not found')
    path=DOCUMENTS/str(cid)/d['stored_name']
    if not path.exists(): raise HTTPException(404,'Stored document file is missing')
    return FileResponse(path,media_type=d['content_type'] or 'application/octet-stream',filename=d['original_name'])

@app.post('/customers/{cid}/documents/{did}/delete')
def customer_document_delete(request:Request,cid:int,did:int):
    require_admin(request)
    with conn() as c:
        d=c.execute("SELECT * FROM customer_documents WHERE id=? AND customer_id=?",(did,cid)).fetchone()
        if not d: raise HTTPException(404,'Document not found')
        c.execute("DELETE FROM customer_documents WHERE id=?",(did,))
    path=DOCUMENTS/str(cid)/d['stored_name']
    try: path.unlink(missing_ok=True)
    except Exception: pass
    audit(request,'DELETE','customer_document',did,f'customer={cid}; file={d["original_name"]}')
    return RedirectResponse(f'/customers/{cid}',303)


@app.post('/customers/{cid}/delete')
def customer_permanent_delete(request:Request,cid:int,confirmation:str=Form(...),reason:str=Form('Test / duplicate customer')):
    require_admin(request)
    if confirmation.strip() != 'DELETE':
        raise HTTPException(400,'Type DELETE exactly to permanently delete the customer')
    with conn() as c:
        customer=c.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone()
        if not customer: raise HTTPException(404,'Customer not found')
        inv_ids=[r['id'] for r in c.execute("SELECT id FROM invoices WHERE customer_id=?",(cid,)).fetchall()]
        # Preserve the identifier in the audit trail before removing customer-linked rows.
        ident=f"account={customer['account_no']}; name={customer['first_name']} {customer['last_name']}; reason={reason}"
        c.execute("UPDATE modems SET customer_id=NULL,status='Available' WHERE customer_id=?",(cid,))
        c.execute("UPDATE sims SET customer_id=NULL,status='Available' WHERE customer_id=?",(cid,))
        if inv_ids:
            marks=','.join('?'*len(inv_ids))
            c.execute(f"DELETE FROM charge_reversals WHERE invoice_id IN ({marks})",inv_ids)
            c.execute(f"DELETE FROM invoice_items WHERE invoice_id IN ({marks})",inv_ids)
        c.execute("DELETE FROM customer_messages WHERE customer_id=?",(cid,))
        c.execute("DELETE FROM customer_message_threads WHERE customer_id=?",(cid,))
        c.execute("DELETE FROM customer_onboarding WHERE customer_id=?",(cid,))
        # Remove referral ledger/history involving the deleted test customer before customer deletion.
        referral_ids=[x['id'] for x in c.execute("SELECT id FROM customer_referrals WHERE referrer_customer_id=? OR referred_customer_id=?",(cid,cid)).fetchall()]
        if referral_ids:
            rmarks=','.join('?'*len(referral_ids))
            c.execute(f"DELETE FROM referral_reward_ledger WHERE referral_id IN ({rmarks})",referral_ids)
        c.execute("DELETE FROM referral_reward_ledger WHERE customer_id=?",(cid,))
        c.execute("DELETE FROM customer_referrals WHERE referrer_customer_id=? OR referred_customer_id=?",(cid,cid))
        c.execute("DELETE FROM woocommerce_orders WHERE customer_id=?",(cid,))
        for table in ('collection_letters','tablet_services','payments','pending_charges','customer_notes','customer_documents','carrier_actions','subscriptions','equipment_history'):
            c.execute(f"DELETE FROM {table} WHERE customer_id=?",(cid,))
        c.execute("DELETE FROM quickbooks_sync_log WHERE (entity_type='customer' AND entity_id=?) OR (entity_type='invoice' AND entity_id IN (SELECT id FROM invoices WHERE customer_id=?)) OR (entity_type='payment' AND entity_id IN (SELECT id FROM payments WHERE customer_id=?))",(cid,cid,cid))
        c.execute("DELETE FROM zoho_sync_log WHERE (entity_type='customer' AND entity_id=?) OR (entity_type='invoice' AND entity_id IN (SELECT id FROM invoices WHERE customer_id=?)) OR (entity_type='payment' AND entity_id IN (SELECT id FROM payments WHERE customer_id=?))",(cid,cid,cid))
        c.execute("UPDATE zoho_history_runs SET customer_id=NULL WHERE customer_id=?",(cid,))
        c.execute("DELETE FROM invoices WHERE customer_id=?",(cid,))
        c.execute("DELETE FROM customers WHERE id=?",(cid,))
        c.execute("INSERT INTO audit_log(user_email,action,entity,entity_id,details) VALUES (?,?,?,?,?)",(request.session.get('user_email',''),'PERMANENT_DELETE','customer',cid,ident))
    customer_dir=DOCUMENTS/str(cid)
    if customer_dir.exists():
        for f in customer_dir.iterdir():
            try:
                if f.is_file(): f.unlink()
            except OSError: pass
        try: customer_dir.rmdir()
        except OSError: pass
    return RedirectResponse('/customers',303)

@app.post('/customers/{cid}/deactivate')
def customer_deactivate(request:Request,cid:int,reason:str=Form('Customer cancelled service'),release_equipment:int=Form(0),apply_early_termination_fee:int=Form(0),unreturned_equipment:int=Form(0)):
    require_staff(request)
    released=[]; created=[]; remaining=0
    with conn() as c:
        cust=c.execute("SELECT c.*,s.start_date subscription_start FROM customers c LEFT JOIN subscriptions s ON s.customer_id=c.id WHERE c.id=?",(cid,)).fetchone()
        if not cust: raise HTTPException(404,'Customer not found')
        contract_start=cust['contract_start'] or cust['subscription_start'] or ''
        remaining=whole_months_remaining(contract_start,int(cust['contract_months'] or 36),date.today())
        now=datetime.now().isoformat(timespec='seconds')
        c.execute("UPDATE customers SET status='Inactive',service_status='Cancelled',portal_enabled=0,deactivated_at=?,deactivation_reason=? WHERE id=?",(now,reason,cid))
        c.execute("UPDATE subscriptions SET status='Cancelled' WHERE customer_id=?",(cid,))
        if unreturned_equipment:
            for kind,table in [('modem','modems'),('sim','sims')]:
                rows=c.execute(f"SELECT id FROM {table} WHERE customer_id=?",(cid,)).fetchall()
                for x in rows:
                    c.execute(f"UPDATE {table} SET status='Unreturned' WHERE id=?",(x['id'],))
                    c.execute("INSERT INTO equipment_history(kind,equipment_id,customer_id,action,details) VALUES (?,?,?,'UNRETURNED',?)",(kind,x['id'],cid,f'reason={reason}; cancellation'))
        elif release_equipment:
            for kind,table in [('modem','modems'),('sim','sims')]:
                rows=c.execute(f"SELECT id FROM {table} WHERE customer_id=?",(cid,)).fetchall()
                for x in rows:
                    c.execute(f"UPDATE {table} SET customer_id=NULL,status='Available' WHERE id=?",(x['id'],))
                    c.execute("INSERT INTO equipment_history(kind,equipment_id,customer_id,action,details) VALUES (?,?,?,'UNASSIGNED',?)",(kind,x['id'],cid,f'disposition=Available; reason={reason}; customer deactivation'))
                    released.append((kind,x['id']))
    if apply_early_termination_fee and remaining>0:
        iid=create_invoice(cid,[(f'Early Termination Fee — {remaining} remaining whole month(s) × {money(EARLY_TERMINATION_MONTHLY_FEE)}',remaining,EARLY_TERMINATION_MONTHLY_FEE)],date.today(),date.today()+timedelta(days=15),'ETF')
        created.append(iid)
    if unreturned_equipment:
        iid=create_invoice(cid,[('Unreturned Equipment Charge',1,UNRETURNED_EQUIPMENT_FEE)],date.today(),date.today()+timedelta(days=15),'EQUIP')
        created.append(iid)
    for iid in created:
        try: email_statement(iid)
        except Exception as e: print('cancellation invoice email error:',e)
    audit(request,'DEACTIVATE','customer',cid,f'reason={reason}; released_equipment={len(released)}; remaining_months={remaining}; cancellation_invoices={created}')
    return RedirectResponse(f'/customers/{cid}',303)

@app.post('/customers/{cid}/pending-charges/{pcid}/reverse')
def reverse_pending_charge(request:Request,cid:int,pcid:int):
    require_admin(request)
    with conn() as c:
        pc=c.execute("SELECT * FROM pending_charges WHERE id=? AND customer_id=?",(pcid,cid)).fetchone()
        if not pc: raise HTTPException(404)
        if pc['applied_invoice_id'] is not None: raise HTTPException(409,'This charge has already been placed on an invoice. Reverse it from the invoice instead.')
        details=f"{pc['description']} {money(pc['amount'])}; source={pc['source'] or ''}"
        c.execute("DELETE FROM pending_charges WHERE id=?",(pcid,))
    audit(request,'REVERSE_PENDING_CHARGE','pending_charge',pcid,details)
    return RedirectResponse(f'/customers/{cid}',303)

@app.post('/customers/{cid}/sim-replacement-fee')
def customer_sim_replacement_fee(request:Request,cid:int):
    require_staff(request)
    with conn() as c:
        cust=c.execute("SELECT status FROM customers WHERE id=?",(cid,)).fetchone()
        if not cust: raise HTTPException(404,'Customer not found')
        if cust['status']!='Active': raise HTTPException(400,'SIM replacement fee can only be queued for an active customer')
        cur=c.execute("INSERT INTO pending_charges(customer_id,description,amount,source) VALUES (?,?,?,'SIM_REPLACEMENT')",(cid,'SIM Card Replacement Fee',SIM_REPLACEMENT_FEE))
        pcid=cur.lastrowid
    audit(request,'QUEUE','pending_charge',pcid,f'customer={cid}; SIM replacement fee={SIM_REPLACEMENT_FEE:.2f}')
    return RedirectResponse(f'/customers/{cid}',303)

@app.post('/customers/{cid}/reactivate')
def customer_reactivate(request:Request,cid:int):
    require_admin(request)
    with conn() as c:
        if not c.execute("SELECT 1 FROM customers WHERE id=?",(cid,)).fetchone(): raise HTTPException(404,'Customer not found')
        c.execute("UPDATE customers SET status='Active',service_status='Active',portal_enabled=1,deactivated_at=NULL,deactivation_reason=NULL WHERE id=?",(cid,))
        c.execute("UPDATE subscriptions SET status='Active' WHERE customer_id=?",(cid,))
    audit(request,'REACTIVATE','customer',cid,'customer restored to active status; equipment must be assigned separately')
    return RedirectResponse(f'/customers/{cid}',303)

@app.post('/customers/{cid}/carrier-policy')
def customer_carrier_policy(request:Request,cid:int,suspension_exempt:int=Form(0),payment_arrangement:int=Form(0)):
    require_staff(request)
    with conn() as c: c.execute("UPDATE customers SET suspension_exempt=?,payment_arrangement=? WHERE id=?",(1 if suspension_exempt else 0,1 if payment_arrangement else 0,cid))
    audit(request,'UPDATE','carrier_policy',cid,f'exempt={suspension_exempt}; arrangement={payment_arrangement}')
    return RedirectResponse(f'/customers/{cid}',303)

@app.get('/customers/{cid}/portal-password',response_class=HTMLResponse)
def portal_pw_form(request:Request,cid:int):
    require_staff(request); return page(request,'Portal Password',f'''<h1>Set Customer Portal Password</h1><form method="post"><label>New password</label><input type="password" name="password" required minlength="8"><button class="btn">Update Password</button></form>''')
@app.post('/customers/{cid}/portal-password')
def portal_pw(request:Request,cid:int,password:str=Form(...)):
    require_staff(request)
    with conn() as c: c.execute("UPDATE customers SET portal_password_hash=?,portal_enabled=1 WHERE id=?",(phash(password),cid))
    audit(request,'UPDATE','customer',cid,'portal password reset'); return RedirectResponse(f'/customers/{cid}',303)

@app.post('/equipment/assign/{kind}')
def assign(request:Request,kind:str,customer_id:int=Form(...),equipment_id:int=Form(...)):
    require_staff(request); table={'modem':'modems','sim':'sims'}.get(kind)
    if not table: raise HTTPException(400)
    with conn() as c:
        x=c.execute(f"SELECT customer_id FROM {table} WHERE id=?",(equipment_id,)).fetchone()
        if not x or x['customer_id'] is not None: raise HTTPException(409,'Equipment already assigned')
        c.execute(f"UPDATE {table} SET customer_id=?,status='Assigned' WHERE id=?",(customer_id,equipment_id)); c.execute("INSERT INTO equipment_history(kind,equipment_id,customer_id,action) VALUES (?,?,?,'ASSIGNED')",(kind,equipment_id,customer_id))
    audit(request,'ASSIGN',kind,equipment_id,f'customer={customer_id}'); return RedirectResponse(f'/customers/{customer_id}',303)

@app.post('/equipment/unassign/{kind}/{eid}')
def unassign(request:Request,kind:str,eid:int,customer_id:int=Form(...),disposition:str=Form('Available'),reason:str=Form('Released from customer')):
    require_staff(request); table={'modem':'modems','sim':'sims'}.get(kind)
    if not table: raise HTTPException(400)
    allowed={'Available','Testing','Damaged','Lost','Retired'}
    if disposition not in allowed: raise HTTPException(400,'Invalid inventory disposition')
    with conn() as c:
        x=c.execute(f"SELECT customer_id FROM {table} WHERE id=?",(eid,)).fetchone()
        if not x: raise HTTPException(404,'Equipment not found')
        if x['customer_id'] is None: raise HTTPException(409,'Equipment is already unassigned')
        if int(x['customer_id']) != int(customer_id): raise HTTPException(409,'Equipment is assigned to a different customer')
        c.execute(f"UPDATE {table} SET customer_id=NULL,status=? WHERE id=?",(disposition,eid))
        c.execute("INSERT INTO equipment_history(kind,equipment_id,customer_id,action,details) VALUES (?,?,?,'UNASSIGNED',?)",(kind,eid,customer_id,f'disposition={disposition}; reason={reason}'))
    audit(request,'UNASSIGN',kind,eid,f'customer={customer_id}; disposition={disposition}; reason={reason}')
    return RedirectResponse(f'/customers/{customer_id}',303)

@app.post('/customers/{cid}/release-equipment')
def release_all_equipment(request:Request,cid:int,reason:str=Form('Customer ended service / equipment returned')):
    require_staff(request)
    released=[]
    with conn() as c:
        cust=c.execute("SELECT id FROM customers WHERE id=?",(cid,)).fetchone()
        if not cust: raise HTTPException(404,'Customer not found')
        for kind,table in [('modem','modems'),('sim','sims')]:
            rows=c.execute(f"SELECT id FROM {table} WHERE customer_id=?",(cid,)).fetchall()
            for x in rows:
                c.execute(f"UPDATE {table} SET customer_id=NULL,status='Available' WHERE id=?",(x['id'],))
                c.execute("INSERT INTO equipment_history(kind,equipment_id,customer_id,action,details) VALUES (?,?,?,'UNASSIGNED',?)",(kind,x['id'],cid,f'disposition=Available; reason={reason}; bulk release'))
                released.append((kind,x['id']))
    audit(request,'RELEASE_ALL','equipment',cid,f'count={len(released)}; reason={reason}')
    return RedirectResponse(f'/customers/{cid}',303)

def inv_page(request,kind):
    require_staff(request)
    table='modems' if kind=='modem' else 'sims'; title='Modems / IMEI' if kind=='modem' else 'SIM Cards / ICCID'; report_kind='modems' if kind=='modem' else 'sims'
    with conn() as c: rows=c.execute(f"SELECT e.*,c.account_no,c.first_name,c.last_name FROM {table} e LEFT JOIN customers c ON c.id=e.customer_id ORDER BY e.id DESC").fetchall()
    rendered=[]
    if kind=='modem':
        hdr='<th>IMEI</th><th>Serial</th><th>Manufacturer</th><th>Model</th><th>Status</th><th>Assigned</th><th>Action</th>'
        for x in rows:
            assigned=f"{x['account_no'] or ''} {x['first_name'] or ''} {x['last_name'] or ''}".strip()
            if x['customer_id']:
                action=f"<form method='post' action='/equipment/unassign/modem/{x['id']}'><input type='hidden' name='customer_id' value='{x['customer_id']}'><input type='hidden' name='disposition' value='Available'><input type='hidden' name='reason' value='Released from inventory screen'><button class='btn secondary' type='submit'>Unassign & Reuse</button></form>"
            else:
                action="<span class='pill'>Ready to assign</span>"+(f"<form method='post' action='/inventory/modem/{x['id']}/delete' onsubmit='return confirm(&quot;PERMANENTLY delete this IMEI from active inventory? This cannot be undone.&quot;)'><button class='btn danger' type='submit'>Delete Permanently</button></form>" if role(request)=='admin' else '')
            rendered.append(f"<tr><td>{html.escape(str(x['imei']))}</td><td>{html.escape(str(x['serial_no'] or ''))}</td><td>{html.escape(str(x['manufacturer'] or ''))}</td><td>{html.escape(str(x['model'] or ''))}</td><td>{html.escape(str(x['status']))}</td><td>{html.escape(assigned)}</td><td>{action}</td></tr>")
        form='<label>IMEI</label><input name="uid" required><label>Serial Number</label><input name="serial"><label>Manufacturer</label><input name="manufacturer"><label>Model</label><input name="model">'
    else:
        hdr='<th>ICCID</th><th>Carrier</th><th>MDN</th><th>Status</th><th>Assigned</th><th>Action</th>'
        for x in rows:
            assigned=f"{x['account_no'] or ''} {x['first_name'] or ''} {x['last_name'] or ''}".strip()
            if x['customer_id']:
                action=f"<form method='post' action='/equipment/unassign/sim/{x['id']}'><input type='hidden' name='customer_id' value='{x['customer_id']}'><input type='hidden' name='disposition' value='Available'><input type='hidden' name='reason' value='Released from inventory screen'><button class='btn secondary' type='submit'>Unassign & Reuse</button></form>"
            else:
                action="<span class='pill'>Ready to assign</span>"+(f"<form method='post' action='/inventory/sim/{x['id']}/delete' onsubmit='return confirm(&quot;PERMANENTLY delete this ICCID from active inventory? This cannot be undone.&quot;)'><button class='btn danger' type='submit'>Delete Permanently</button></form>" if role(request)=='admin' else '')
            rendered.append(f"<tr><td>{html.escape(str(x['iccid']))}</td><td>{html.escape(str(x['carrier'] or ''))}</td><td>{html.escape(str(x['mdn'] or ''))}</td><td>{html.escape(str(x['status']))}</td><td>{html.escape(assigned)}</td><td>{action}</td></tr>")
        form='<label>ICCID</label><input name="uid" required><label>Carrier</label><input name="carrier"><label>MDN / Phone Number</label><input name="mdn">'
    trs=''.join(rendered) or '<tr><td colspan="7">No inventory records yet.</td></tr>'
    buttons=f"<div class='actions'><a class='btn secondary' target='_blank' href='/reports/{report_kind}.pdf?status=all'>Print All</a><a class='btn secondary' target='_blank' href='/reports/{report_kind}.pdf?status=available'>Print Available</a><a class='btn secondary' target='_blank' href='/reports/{report_kind}.pdf?status=assigned'>Print Assigned</a></div>"
    body=f'<h1>{title}</h1>{buttons}<div class="row"><div class="card"><table><tr>{hdr}</tr>{trs}</table></div><div class="card"><h2>Add Inventory</h2><form method="post">{form}<button class="btn">Add</button></form></div></div>'
    return page(request,title,body)

@app.get('/modems',response_class=HTMLResponse)
def modems(request:Request): return inv_page(request,'modem')
@app.post('/modems')
def modem_add(request:Request,uid:str=Form(...),serial:str=Form(''),manufacturer:str=Form(''),model:str=Form('')):
    require_staff(request)
    try:
        with conn() as c: c.execute("INSERT INTO modems(imei,serial_no,manufacturer,model) VALUES (?,?,?,?)",(uid.strip(),serial,manufacturer,model))
    except sqlite3.IntegrityError: raise HTTPException(409,'IMEI already exists')
    return RedirectResponse('/modems',303)
@app.get('/sims',response_class=HTMLResponse)
def sims(request:Request): return inv_page(request,'sim')
@app.post('/sims')
def sim_add(request:Request,uid:str=Form(...),carrier:str=Form(''),mdn:str=Form('')):
    require_staff(request)
    try:
        with conn() as c: c.execute("INSERT INTO sims(iccid,carrier,mdn) VALUES (?,?,?)",(uid.strip(),carrier,mdn))
    except sqlite3.IntegrityError: raise HTTPException(409,'ICCID already exists')
    return RedirectResponse('/sims',303)

@app.post('/inventory/{kind}/{eid}/delete')
def inventory_delete(request:Request,kind:str,eid:int):
    require_admin(request)
    table={'modem':'modems','sim':'sims'}.get(kind); idcol={'modem':'imei','sim':'iccid'}.get(kind)
    if not table: raise HTTPException(400,'Invalid inventory type')
    with conn() as c:
        r=c.execute(f"SELECT * FROM {table} WHERE id=?",(eid,)).fetchone()
        if not r: raise HTTPException(404,'Inventory record not found')
        if r['customer_id'] is not None: raise HTTPException(409,'Assigned equipment must be unassigned before permanent deletion')
        ident=r[idcol]
        c.execute("INSERT INTO equipment_history(kind,equipment_id,customer_id,action,details) VALUES (?,?,NULL,'DELETED',?)",(kind,eid,f'{idcol}={ident}; permanently removed from active inventory'))
        c.execute(f"DELETE FROM {table} WHERE id=?",(eid,))
    audit(request,'DELETE',kind,eid,f'{idcol}={ident}; permanently removed from inventory')
    return RedirectResponse('/modems' if kind=='modem' else '/sims',303)

@app.get('/plans',response_class=HTMLResponse)
def plans(request:Request):
    require_staff(request)
    with conn() as c: rows=c.execute("SELECT * FROM plans WHERE active=1 ORDER BY CASE WHEN name LIKE '%Residential' THEN 0 ELSE 1 END, monthly_price").fetchall()
    trs=''.join(f"<tr><td>{x['name']}</td><td>{money(x['monthly_price'])}</td><td>{money(x['modem_lease'])}</td><td>{x['description'] or ''}</td></tr>" for x in rows)
    return page(request,'Plans',f'''<h1>Service Plans</h1><div class="row"><div class="card"><table><tr><th>Plan</th><th>Service</th><th>Modem</th><th>Description</th></tr>{trs}</table></div><div class="card"><h2>Add Plan</h2><form method="post"><label>Name</label><input name="name" required><label>Monthly Service</label><input type="number" step=".01" name="monthly_price" required><label>Modem Lease</label><input type="number" step=".01" name="modem_lease" value="0"><label>Description</label><textarea name="description"></textarea><button class="btn">Add Plan</button></form></div></div>''')
@app.post('/plans')
def plan_add(request:Request,name:str=Form(...),monthly_price:float=Form(...),modem_lease:float=Form(0),description:str=Form('')):
    require_admin(request)
    try:
        with conn() as c: c.execute("INSERT INTO plans(name,monthly_price,modem_lease,description) VALUES (?,?,?,?)",(name,monthly_price,modem_lease,description))
    except sqlite3.IntegrityError: raise HTTPException(409,'Plan already exists')
    return RedirectResponse('/plans',303)

@app.get('/invoices',response_class=HTMLResponse)
def invoices(request:Request):
    require_staff(request); run_daily_tasks()
    with conn() as c: rows=c.execute("SELECT i.*,c.account_no,c.first_name,c.last_name FROM invoices i JOIN customers c ON c.id=i.customer_id ORDER BY i.id DESC").fetchall()
    trs=''.join(f"<tr><td><a href='/invoices/{x['id']}'>{x['invoice_no']}</a></td><td>{x['account_no']}</td><td>{x['first_name']} {x['last_name']}</td><td>{x['issue_date']}</td><td>{money(x['subtotal'])}</td><td>{money(0 if x['status']=='Void' else x['subtotal']-x['amount_paid'])}</td><td>{x['status']}</td></tr>" for x in rows)
    return page(request,'Invoices',f'''<div class="actions right"><a class="btn" href="/invoices/new">New Invoice</a></div><h1>Invoices</h1><table><tr><th>Invoice</th><th>Account</th><th>Customer</th><th>Issue</th><th>Total</th><th>Balance</th><th>Status</th></tr>{trs}</table>''')

@app.get('/invoices/new',response_class=HTMLResponse)
def invoice_new(request:Request,customer_id:int=0):
    require_staff(request)
    with conn() as c: cs=c.execute("SELECT id,account_no,first_name,last_name FROM customers ORDER BY last_name").fetchall()
    opts=''.join(f"<option value='{x['id']}' {'selected' if x['id']==customer_id else ''}>{x['account_no']} — {x['first_name']} {x['last_name']}</option>" for x in cs)
    return page(request,'New Invoice',f'''<h1>New Invoice</h1><form method="post"><label>Customer</label><select name="customer_id">{opts}</select><label>Description</label><input name="description" required><label>Amount</label><input type="number" step=".01" name="amount" required><label>Due in days</label><input type="number" name="due_days" value="15"><button class="btn">Create Invoice</button></form>''')
@app.post('/invoices/new')
def invoice_create(request:Request,customer_id:int=Form(...),description:str=Form(...),amount:float=Form(...),due_days:int=Form(15)):
    require_staff(request); iid=create_invoice(customer_id,[(description,1,amount)],date.today(),date.today()+timedelta(days=due_days),'INV'); audit(request,'CREATE','invoice',iid,description); accounting_try('invoice',iid); return RedirectResponse(f'/invoices/{iid}',303)

@app.get('/invoices/{iid}',response_class=HTMLResponse)
def invoice_detail(request:Request,iid:int):
    require_staff(request)
    with conn() as c:
        inv=c.execute("SELECT i.*,c.first_name,c.last_name,c.account_no,c.email FROM invoices i JOIN customers c ON c.id=i.customer_id WHERE i.id=?",(iid,)).fetchone()
        items=c.execute("SELECT * FROM invoice_items WHERE invoice_id=? ORDER BY id",(iid,)).fetchall()
        revs=c.execute("SELECT original_item_id,COALESCE(SUM(amount),0) reversed FROM charge_reversals WHERE invoice_id=? GROUP BY original_item_id",(iid,)).fetchall()
        revmap={int(x['original_item_id']):float(x['reversed'] or 0) for x in revs}
    if not inv: raise HTTPException(404)
    rowparts=[]
    for x in items:
        reversed_amt=revmap.get(int(x['id']),0.0)
        remaining=max(0.0,float(x['amount'])-reversed_amt) if float(x['amount'])>0 else 0.0
        action=''
        if role(request)=='admin' and inv['status']!='Void' and float(x['amount'])>0 and remaining>.005:
            action=f"<a class='btn secondary' href='/invoices/{iid}/items/{x['id']}/reverse'>Reverse Charge</a>"
        note=f"<div class='muted'>Reversed: {money(reversed_amt)} | Remaining reversible: {money(remaining)}</div>" if reversed_amt>.005 else ''
        rowparts.append(f"<tr><td>{x['description']}{note}</td><td>{x['qty']}</td><td>{money(x['unit_price'])}</td><td>{money(x['amount'])}</td><td>{action}</td></tr>")
    rows=''.join(rowparts)
    bal=0 if inv['status']=='Void' else inv['subtotal']-inv['amount_paid']
    admin_actions=''
    if role(request)=='admin':
        if not revmap:
            admin_actions=f'''<a class="btn secondary" href="/invoices/{iid}/edit">Edit Invoice</a>'''
        if inv['status']!='Void': admin_actions+=f'''<a class="btn secondary" href="/invoices/{iid}/credit">Issue Credit</a><a class="btn danger" href="/invoices/{iid}/void">Void Invoice</a><a class="btn danger" href="/invoices/{iid}/delete-test">Delete Test Invoice</a>'''
    void_notice=''
    if inv['status']=='Void':
        void_notice=f'''<div class="section card" style="border-left:5px solid var(--danger)"><h2 class="danger-text">VOID INVOICE</h2><p>This invoice is void and is excluded from the customer balance and collection workflows.</p><p><b>Reason:</b> {inv['void_reason'] or 'Not specified'}<br><b>Voided:</b> {inv['voided_at'] or ''}<br><b>By:</b> {inv['voided_by'] or ''}</p></div>'''
    payment=''
    if inv['status']!='Void':
        payment=f'''<div class="section card"><h2>Post Payment</h2><form method="post" action="/payments"><input type="hidden" name="customer_id" value="{inv['customer_id']}"><input type="hidden" name="invoice_id" value="{iid}"><div class="row"><div><label>Amount</label><input type="number" step=".01" min="0.01" name="amount" value="{max(0,bal):.2f}" required></div><div><label>Method</label><select name="method"><option>Card</option><option>ACH</option><option>Cash</option><option>Check</option><option>Other</option></select></div></div><label>Reference</label><input name="reference"><button class="btn ok">Record Payment</button></form></div>'''
    stripe_action=(f'<a class="btn ok" href="/invoices/{iid}/stripe-checkout">Take Online Card Payment</a>' if STRIPE_SECRET_KEY and inv['status'] not in ('Paid','Void') and bal>0.005 else '')
    return page(request,'Invoice',f'''<div class="actions right"><a class="btn" href="/invoices/{iid}/statement">PDF Statement</a><a class="btn secondary" href="/invoices/{iid}/email">Email Statement</a>{stripe_action}{admin_actions}</div><h1>{inv['invoice_no']} <span class="pill {'bad' if inv['status']=='Void' else ''}">{inv['status']}</span></h1>{void_notice}<div class="grid"><div class="card"><div class="muted">Customer</div><b>{inv['first_name']} {inv['last_name']}</b><div>{inv['account_no']}</div></div><div class="card"><div class="muted">Total</div><div class="metric">{money(inv['subtotal'])}</div></div><div class="card"><div class="muted">Paid</div><div class="metric">{money(inv['amount_paid'])}</div></div><div class="card"><div class="muted">Balance</div><div class="metric">{money(bal)}</div></div></div><div class="section card"><div class="row"><div><b>Issue Date:</b> {inv['issue_date']}</div><div><b>Due Date:</b> {inv['due_date']}</div></div><table><tr><th>Description</th><th>Qty</th><th>Price</th><th>Amount</th><th>Adjustment</th></tr>{rows}</table></div>{payment}''')

@app.get('/invoices/{iid}/stripe-checkout')
def invoice_staff_stripe_checkout(request:Request,iid:int):
    require_staff(request)
    session=stripe_checkout_for_invoice(iid,f'{PUBLIC_URL}/payment/confirmation?session_id={{CHECKOUT_SESSION_ID}}',f'{PUBLIC_URL}/invoices/{iid}',context='staff_invoice')
    if not session: return RedirectResponse(f'/invoices/{iid}',303)
    return RedirectResponse(session['url'],303)

@app.get('/payment/confirmation',response_class=HTMLResponse)
def payment_confirmation_page(request:Request,session_id:str=''):
    # The webhook is authoritative. This page intentionally does not mark anything paid.
    return HTMLResponse(f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Payment Submitted</title><style>{CSS}</style></head><body><div class="portal"><div class="card"><h1>Payment submitted</h1><p>Thank you. Stripe has returned a successful checkout. The CRM will mark the invoice paid after the signed Stripe webhook confirms the transaction.</p><p>A payment confirmation email will be sent to the customer email address on file after confirmation.</p><a class="btn" href="/">Return to CRM</a></div></div></body></html>''')

@app.get('/invoices/{iid}/edit',response_class=HTMLResponse)
def invoice_edit_form(request:Request,iid:int):
    require_admin(request)
    with conn() as c:
        inv=c.execute("SELECT * FROM invoices WHERE id=?",(iid,)).fetchone()
        items=c.execute("SELECT * FROM invoice_items WHERE invoice_id=? ORDER BY id",(iid,)).fetchall()
    if not inv: raise HTTPException(404)
    if inv['status']=='Void': raise HTTPException(409,'A void invoice cannot be edited.')
    rows=[]
    for x in items:
        rows.append(f'''<div class="row"><div><label>Description</label><input name="description" value="{x['description']}" required></div><div class="row"><div><label>Quantity</label><input type="number" step="0.01" min="0" name="qty" value="{x['qty']}" required></div><div><label>Unit Price</label><input type="number" step="0.01" name="unit_price" value="{x['unit_price']}" required></div></div></div>''')
    for _ in range(3):
        rows.append('''<div class="row"><div><label>Additional Description</label><input name="description" placeholder="Leave blank if unused"></div><div class="row"><div><label>Quantity</label><input type="number" step="0.01" min="0" name="qty" value="1"></div><div><label>Unit Price</label><input type="number" step="0.01" name="unit_price" value="0.00"></div></div></div>''')
    return page(request,'Edit Invoice',f'''<h1>Edit {inv['invoice_no']}</h1><div class="notice">Changes are recorded in the audit log. The invoice PDF will be regenerated after saving. Blank additional rows are ignored.</div><form method="post"><div class="row"><div><label>Issue Date</label><input type="date" name="issue_date" value="{inv['issue_date']}" required></div><div><label>Due Date</label><input type="date" name="due_date" value="{inv['due_date']}" required></div></div><h2>Invoice Items</h2>{''.join(rows)}<div class="actions"><button class="btn" type="submit">Save Invoice Changes</button><a class="btn secondary" href="/invoices/{iid}">Cancel</a></div></form>''')

@app.post('/invoices/{iid}/edit')
def invoice_edit(request:Request,iid:int,issue_date:str=Form(...),due_date:str=Form(...),description:list[str]=Form(...),qty:list[float]=Form(...),unit_price:list[float]=Form(...)):
    require_admin(request)
    try:
        issue=date.fromisoformat(issue_date); due=date.fromisoformat(due_date)
    except Exception: raise HTTPException(400,'Invalid invoice date.')
    if due < issue: raise HTTPException(400,'Due date cannot be before issue date.')
    items=[]
    for d,q,p in zip(description,qty,unit_price):
        d=(d or '').strip()
        if not d: continue
        if q < 0: raise HTTPException(400,'Quantity cannot be negative.')
        items.append((d,float(q),float(p)))
    if not items: raise HTTPException(400,'Invoice must contain at least one line item.')
    total=round(sum(q*p for _,q,p in items),2)
    with conn() as c:
        inv=c.execute("SELECT * FROM invoices WHERE id=?",(iid,)).fetchone()
        if not inv: raise HTTPException(404)
        if inv['status']=='Void': raise HTTPException(409,'A void invoice cannot be edited.')
        if c.execute("SELECT 1 FROM charge_reversals WHERE invoice_id=? LIMIT 1",(iid,)).fetchone():
            raise HTTPException(409,'This invoice contains charge reversals. For accounting integrity, add further adjustments or void the invoice rather than rewriting its original line items.')
        if total + .005 < float(inv['amount_paid'] or 0): raise HTTPException(409,'Invoice total cannot be reduced below payments already posted. Reverse or correct the payment first.')
        before=f"issue={inv['issue_date']}; due={inv['due_date']}; subtotal={inv['subtotal']}"
        c.execute("DELETE FROM invoice_items WHERE invoice_id=?",(iid,))
        for d,q,pv in items:
            c.execute("INSERT INTO invoice_items(invoice_id,description,qty,unit_price,amount) VALUES (?,?,?,?,?)",(iid,d,q,pv,round(q*pv,2)))
        c.execute("UPDATE invoices SET issue_date=?,due_date=?,subtotal=?,pdf_path=NULL,eod_notice_at=NULL,eod_notice_pdf=NULL,last_reminder_at=NULL,edited_at=?,edited_by=? WHERE id=?",(issue.isoformat(),due.isoformat(),total,business_now().isoformat(timespec='seconds'),request.session.get('user_email',''),iid))
        update_invoice_status(c,iid)
    generate_statement(iid)
    audit(request,'EDIT','invoice',iid,f"{before} -> issue={issue_date}; due={due_date}; subtotal={total}; items={len(items)}")
    return RedirectResponse(f'/invoices/{iid}',303)

@app.get('/invoices/{iid}/items/{item_id}/reverse',response_class=HTMLResponse)
def reverse_charge_form(request:Request,iid:int,item_id:int):
    require_admin(request)
    with conn() as c:
        inv=c.execute("SELECT i.*,c.first_name,c.last_name,c.account_no FROM invoices i JOIN customers c ON c.id=i.customer_id WHERE i.id=?",(iid,)).fetchone()
        item=c.execute("SELECT * FROM invoice_items WHERE id=? AND invoice_id=?",(item_id,iid)).fetchone()
        reversed_amt=float(c.execute("SELECT COALESCE(SUM(amount),0) v FROM charge_reversals WHERE invoice_id=? AND original_item_id=?",(iid,item_id)).fetchone()['v'] or 0)
    if not inv or not item: raise HTTPException(404)
    if inv['status']=='Void': raise HTTPException(409,'Charges cannot be reversed on a void invoice.')
    if float(item['amount']) <= 0: raise HTTPException(409,'A credit or reversal line cannot itself be reversed.')
    remaining=max(0,float(item['amount'])-reversed_amt)
    if remaining <= .005: raise HTTPException(409,'This charge has already been fully reversed.')
    return page(request,'Reverse Charge',f'''<h1>Reverse Charge</h1><div class="card"><p><b>Invoice:</b> {inv['invoice_no']}<br><b>Customer:</b> {inv['account_no']} — {inv['first_name']} {inv['last_name']}</p><p><b>Original charge:</b> {item['description']} — {money(item['amount'])}<br><b>Already reversed:</b> {money(reversed_amt)}<br><b>Available to reverse:</b> {money(remaining)}</p><form method="post"><label>Reversal Amount</label><input type="number" step="0.01" min="0.01" max="{remaining:.2f}" name="amount" value="{remaining:.2f}" required><label>Reason for reversal</label><textarea name="reason" required placeholder="Example: fee waived, billing error, service credit"></textarea><div class="actions"><button class="btn danger" type="submit">Post Charge Reversal</button><a class="btn secondary" href="/invoices/{iid}">Cancel</a></div></form></div>''')

@app.post('/invoices/{iid}/items/{item_id}/reverse')
def reverse_charge(request:Request,iid:int,item_id:int,amount:float=Form(...),reason:str=Form(...)):
    require_admin(request); reason=(reason or '').strip()
    if amount <= 0: raise HTTPException(400,'Reversal amount must be greater than zero.')
    if not reason: raise HTTPException(400,'A reversal reason is required.')
    with conn() as c:
        inv=c.execute("SELECT * FROM invoices WHERE id=?",(iid,)).fetchone()
        item=c.execute("SELECT * FROM invoice_items WHERE id=? AND invoice_id=?",(item_id,iid)).fetchone()
        if not inv or not item: raise HTTPException(404)
        if inv['status']=='Void': raise HTTPException(409,'Charges cannot be reversed on a void invoice.')
        if float(item['amount']) <= 0: raise HTTPException(409,'A credit or reversal line cannot itself be reversed.')
        reversed_amt=float(c.execute("SELECT COALESCE(SUM(amount),0) v FROM charge_reversals WHERE invoice_id=? AND original_item_id=?",(iid,item_id)).fetchone()['v'] or 0)
        remaining=max(0,float(item['amount'])-reversed_amt)
        if amount > remaining + .005: raise HTTPException(409,'Reversal amount exceeds the remaining reversible charge.')
        new_total=round(float(inv['subtotal'])-amount,2)
        if new_total + .005 < float(inv['amount_paid'] or 0):
            raise HTTPException(409,'This reversal would reduce the invoice below payments already posted. Reverse/correct the payment first or issue a separate customer credit.')
        desc=f"Charge Reversal — {item['description']}"
        cur=c.execute("INSERT INTO invoice_items(invoice_id,description,qty,unit_price,amount) VALUES (?,?,?,?,?)",(iid,desc,1,-amount,-amount))
        reversal_item_id=cur.lastrowid
        c.execute("INSERT INTO charge_reversals(invoice_id,original_item_id,reversal_item_id,amount,reason,reversed_by,reversed_at) VALUES (?,?,?,?,?,?,?)",(iid,item_id,reversal_item_id,amount,reason,request.session.get('user_email',''),business_now().isoformat(timespec='seconds')))
        c.execute("UPDATE invoices SET subtotal=?,pdf_path=NULL,eod_notice_at=NULL,eod_notice_pdf=NULL,last_reminder_at=NULL,edited_at=?,edited_by=? WHERE id=?",(new_total,business_now().isoformat(timespec='seconds'),request.session.get('user_email',''),iid))
        update_invoice_status(c,iid)
    generate_statement(iid)
    audit(request,'REVERSE_CHARGE','invoice',iid,f'item={item_id}; amount={amount:.2f}; reason={reason}')
    return RedirectResponse(f'/invoices/{iid}',303)

@app.get('/invoices/{iid}/credit',response_class=HTMLResponse)
def invoice_credit_form(request:Request,iid:int):
    require_admin(request)
    with conn() as c: inv=c.execute("SELECT i.*,c.first_name,c.last_name,c.account_no FROM invoices i JOIN customers c ON c.id=i.customer_id WHERE i.id=?",(iid,)).fetchone()
    if not inv: raise HTTPException(404)
    if inv['status']=='Void': raise HTTPException(409,'A void invoice cannot receive a credit.')
    open_amount=max(0.0,float(inv['subtotal'] or 0)-float(inv['amount_paid'] or 0))
    return page(request,'Issue Customer Credit',f'''<h1>Issue Customer Credit</h1><div class="card"><p><b>Invoice:</b> {inv['invoice_no']}<br><b>Customer:</b> {inv['account_no']} — {inv['first_name']} {inv['last_name']}<br><b>Current balance:</b> {money(open_amount)}</p><form method="post"><label>Credit Amount</label><input type="number" step="0.01" min="0.01" max="{open_amount:.2f}" name="amount" value="{open_amount:.2f}" required><label>Reason</label><textarea name="reason" required placeholder="Example: test invoice credit, courtesy credit, billing adjustment"></textarea><div class="actions"><button class="btn ok" type="submit">Post Customer Credit</button><a class="btn secondary" href="/invoices/{iid}">Cancel</a></div></form></div>''')

@app.post('/invoices/{iid}/credit')
def invoice_credit(request:Request,iid:int,amount:float=Form(...),reason:str=Form(...)):
    require_admin(request); reason=(reason or '').strip()
    if amount<=0 or not reason: raise HTTPException(400,'A positive credit amount and reason are required.')
    with conn() as c:
        inv=c.execute('SELECT * FROM invoices WHERE id=?',(iid,)).fetchone()
        if not inv: raise HTTPException(404)
        if inv['status']=='Void': raise HTTPException(409,'A void invoice cannot receive a credit.')
        open_amount=max(0.0,float(inv['subtotal'] or 0)-float(inv['amount_paid'] or 0))
        if amount>open_amount+.005: raise HTTPException(409,'Credit cannot exceed the current unpaid invoice balance.')
        c.execute('INSERT INTO invoice_items(invoice_id,description,qty,unit_price,amount) VALUES (?,?,?,?,?)',(iid,'Customer Credit — '+reason,1,-amount,-amount))
        new_total=round(float(inv['subtotal'])-amount,2)
        c.execute("UPDATE invoices SET subtotal=?,pdf_path=NULL,eod_notice_at=NULL,eod_notice_pdf=NULL,last_reminder_at=NULL,edited_at=?,edited_by=? WHERE id=?",(new_total,business_now().isoformat(timespec='seconds'),request.session.get('user_email',''),iid)); update_invoice_status(c,iid)
    generate_statement(iid); audit(request,'CREDIT','invoice',iid,f'amount={amount:.2f}; reason={reason}')
    return RedirectResponse(f'/invoices/{iid}',303)

@app.get('/invoices/{iid}/delete-test',response_class=HTMLResponse)
def invoice_delete_test_form(request:Request,iid:int):
    require_admin(request)
    with conn() as c: inv=c.execute("SELECT i.*,c.first_name,c.last_name,c.account_no FROM invoices i JOIN customers c ON c.id=i.customer_id WHERE i.id=?",(iid,)).fetchone()
    if not inv: raise HTTPException(404)
    return page(request,'Delete Test Invoice',f'''<h1>Permanently Delete Test Invoice</h1><div class="notice" style="border-left-color:var(--danger)"><b>Use this only for test, duplicate, or mistakenly-created CRM invoices.</b> This permanently removes the invoice, its line items, CRM payment records, reversals, and sync-log references. It does not delete transactions already created in an external accounting provider.</div><div class="card"><p><b>{inv['invoice_no']}</b> — {inv['account_no']} — {inv['first_name']} {inv['last_name']}</p><form method="post"><label>Type DELETE INVOICE to confirm</label><input name="confirmation" required autocomplete="off"><label>Reason</label><input name="reason" value="Test / duplicate invoice" required><button class="btn danger" type="submit">Permanently Delete Test Invoice</button></form></div>''')

@app.post('/invoices/{iid}/delete-test')
def invoice_delete_test(request:Request,iid:int,confirmation:str=Form(...),reason:str=Form('Test / duplicate invoice')):
    require_admin(request)
    if confirmation.strip()!='DELETE INVOICE': raise HTTPException(400,'Type DELETE INVOICE exactly to permanently delete the invoice.')
    with conn() as c:
        inv=c.execute('SELECT * FROM invoices WHERE id=?',(iid,)).fetchone()
        if not inv: raise HTTPException(404)
        ident=f"invoice={inv['invoice_no']}; customer_id={inv['customer_id']}; reason={reason}"
        c.execute("DELETE FROM quickbooks_sync_log WHERE entity_type='invoice' AND entity_id=?",(iid,)); c.execute("DELETE FROM zoho_sync_log WHERE entity_type='invoice' AND entity_id=?",(iid,))
        c.execute('DELETE FROM payments WHERE invoice_id=?',(iid,)); c.execute('DELETE FROM charge_reversals WHERE invoice_id=?',(iid,)); c.execute('DELETE FROM invoice_items WHERE invoice_id=?',(iid,)); c.execute('DELETE FROM invoices WHERE id=?',(iid,))
        c.execute("INSERT INTO audit_log(user_email,action,entity,entity_id,details) VALUES (?,?,?,?,?)",(request.session.get('user_email',''),'PERMANENT_DELETE_TEST','invoice',iid,ident))
    return RedirectResponse('/invoices',303)

@app.get('/invoices/{iid}/void',response_class=HTMLResponse)
def invoice_void_form(request:Request,iid:int):
    require_admin(request)
    with conn() as c: inv=c.execute("SELECT i.*,c.first_name,c.last_name,c.account_no FROM invoices i JOIN customers c ON c.id=i.customer_id WHERE i.id=?",(iid,)).fetchone()
    if not inv: raise HTTPException(404)
    if inv['status']=='Void': return RedirectResponse(f'/invoices/{iid}',303)
    blocked=''
    if float(inv['amount_paid'] or 0) > .005:
        blocked=f'''<div class="notice" style="border-left-color:var(--danger)"><b>This invoice has {money(inv['amount_paid'])} in posted payments and cannot be voided.</b> Correct/reverse those payments before voiding so the accounting history remains consistent.</div>'''
    form='' if blocked else f'''<form method="post"><label>Reason for voiding this invoice</label><textarea name="reason" required placeholder="Example: duplicate invoice, billing correction, customer billed in error"></textarea><div class="actions"><button class="btn danger" type="submit">Confirm Void Invoice</button><a class="btn secondary" href="/invoices/{iid}">Cancel</a></div></form>'''
    return page(request,'Void Invoice',f'''<h1>Void {inv['invoice_no']}</h1><div class="card"><p><b>Customer:</b> {inv['account_no']} — {inv['first_name']} {inv['last_name']}</p><p><b>Invoice total:</b> {money(inv['subtotal'])}</p><p>Voiding does not delete the invoice. It remains in the CRM and audit history, but its balance becomes $0.00 and it is excluded from collections, past-due notices, suspension calculations, and customer payment options.</p>{blocked}{form}</div>''')

@app.post('/invoices/{iid}/void')
def invoice_void(request:Request,iid:int,reason:str=Form(...)):
    require_admin(request); reason=reason.strip()
    if not reason: raise HTTPException(400,'A void reason is required.')
    with conn() as c:
        inv=c.execute("SELECT * FROM invoices WHERE id=?",(iid,)).fetchone()
        if not inv: raise HTTPException(404)
        if inv['status']=='Void': return RedirectResponse(f'/invoices/{iid}',303)
        if float(inv['amount_paid'] or 0) > .005: raise HTTPException(409,'Invoice has posted payments and cannot be voided until those payments are corrected.')
        c.execute("UPDATE invoices SET status='Void',voided_at=?,voided_by=?,void_reason=?,eod_notice_at=NULL,last_reminder_at=NULL WHERE id=?",(business_now().isoformat(timespec='seconds'),request.session.get('user_email',''),reason,iid))
    generate_statement(iid)
    audit(request,'VOID','invoice',iid,reason)
    return RedirectResponse(f'/invoices/{iid}',303)

@app.get('/invoices/{iid}/statement')
def statement(request:Request,iid:int): require_staff(request); return FileResponse(generate_statement(iid),media_type='application/pdf',filename=f'invoice-{iid}.pdf')
@app.get('/invoices/{iid}/email')
def statement_email(request:Request,iid:int): require_staff(request); email_statement(iid); audit(request,'EMAIL','invoice',iid,'statement'); return RedirectResponse(f'/invoices/{iid}',303)

@app.get('/integrations/accounting',response_class=HTMLResponse)
def accounting_integration(request:Request):
    require_admin(request)
    with conn() as c:
        z=c.execute("SELECT organization_name FROM zoho_oauth WHERE id=1").fetchone()
        q=c.execute("SELECT company_name FROM quickbooks_oauth WHERE id=1").fetchone()
        z_failed=sum(c.execute(f"SELECT count(*) n FROM {t} WHERE zoho_sync_status='Failed'").fetchone()['n'] for t in ('customers','invoices','payments'))
        q_failed=sum(c.execute(f"SELECT count(*) n FROM {t} WHERE quickbooks_sync_status='Failed'").fetchone()['n'] for t in ('customers','invoices','payments'))
        z_last=c.execute("SELECT created_at,status FROM zoho_sync_log ORDER BY id DESC LIMIT 1").fetchone()
        q_last=c.execute("SELECT created_at,status FROM quickbooks_sync_log ORDER BY id DESC LIMIT 1").fetchone()
    def provider_card(name,key,connected,company,failed,last,url):
        is_active=ACCOUNTING_PROVIDER==key
        state='<span class="pill">Active Provider</span>' if is_active else '<span class="pill warn">Inactive / Standby</span>'
        conn_state='<span class="pill">Connected</span>' if connected else '<span class="pill bad">Not Connected</span>'
        last_text=(f"{last['created_at']} — {last['status']}" if last else 'No sync activity')
        warning=(f"<div class='notice'><b>{failed} failed sync{'s' if failed!=1 else ''}</b> need attention.</div>" if failed else '')
        return f'''<div class="card"><h2>{name}</h2><p>{state} {conn_state}</p><p><b>Company:</b> {html.escape(company or 'Not connected')}</p><p><b>Failed Syncs:</b> {failed}</p><p><b>Last Activity:</b> {html.escape(last_text)}</p>{warning}<a class="btn" href="{url}">Open {name}</a></div>'''
    zcard=provider_card('Zoho Books','zoho',bool(z),(z['organization_name'] if z else ''),z_failed,z_last,'/integrations/zoho')
    qcard=provider_card('QuickBooks Online','quickbooks',bool(q),(q['company_name'] if q else ''),q_failed,q_last,'/integrations/quickbooks')
    note='Only the active provider receives new customer, invoice, and payment syncs. Inactive-provider retry actions are blocked to prevent accidental duplicate accounting entries.'
    return page(request,'Accounting Integrations',f'''<h1>Accounting Integrations</h1><div class="notice"><b>Active accounting provider:</b> {html.escape(ACCOUNTING_PROVIDER)}<br>{note}</div><div class="row">{zcard}{qcard}</div><div class="section card"><h2>Display Preference</h2><p>Inactive accounting providers are {'shown' if ACCOUNTING_SHOW_INACTIVE else 'hidden'} in the main sidebar. Set <code>ACCOUNTING_SHOW_INACTIVE=1</code> in Render to show both provider links without changing which provider is active.</p></div>''')

@app.get('/integrations/zoho',response_class=HTMLResponse)
def zoho_integration(request:Request):
    require_admin(request); row=_zoho_oauth()
    connected=bool(row and row['access_token'] and row['organization_id']); status='Connected' if connected else 'Not Connected'
    org=row['organization_name'] if row else ''
    with conn() as c: logs=c.execute("SELECT * FROM zoho_sync_log ORDER BY id DESC LIMIT 50").fetchall()
    trs=''.join(f"<tr><td>{x['created_at']}</td><td>{html.escape(x['entity_type'])}</td><td>{x['entity_id'] or ''}</td><td>{html.escape(x['action'] or '')}</td><td>{html.escape(x['status'] or '')}</td><td>{html.escape(x['zoho_id'] or '')}</td><td>{html.escape((x['error'] or '')[:180])}</td></tr>" for x in logs) or '<tr><td colspan=7>No Zoho Books sync activity yet.</td></tr>'
    btn='<a class="btn" href="/zoho/connect">Connect Zoho Books</a>' if not connected else '<a class="btn secondary" href="/zoho/test">Test Connection</a> <form style="display:inline" method="post" action="/zoho/disconnect"><button class="btn danger">Disconnect</button></form>'
    active='<span class="pill">Active accounting provider</span>' if ACCOUNTING_PROVIDER=='zoho' else '<span class="pill warn">Inactive / standby</span>'
    return page(request,'Zoho Books',f'''<h1>Zoho Books</h1><div class="card"><p><b>Status:</b> {status}</p><p><b>Organization:</b> {html.escape(org or 'Not connected')}</p><p><b>Accounting Provider:</b> {html.escape(ACCOUNTING_PROVIDER)} {active}</p><p><b>Redirect URI:</b> {html.escape(ZOHO_REDIRECT_URI)}</p><div class="actions">{btn}</div></div><div class="card section"><h2>Synchronization</h2><p>When Zoho is the active accounting provider, new CRM subscribers, invoices, and posted payments synchronize to Zoho Books. Partial payments are applied to the matching Zoho invoice. Failed calls remain in the CRM and can be retried.</p><div class="actions"><a class="btn secondary" href="/zoho/history">Sync Existing CRM Records</a>{('<form method="post" action="/zoho/retry"><button class="btn">Retry Failed Zoho Syncs</button></form>' if ACCOUNTING_PROVIDER=='zoho' else '<p class="muted">Retry is disabled while Zoho is not the active accounting provider.</p>')}</div></div><div class="section"><h2>Recent Sync Activity</h2><table><tr><th>Time</th><th>Type</th><th>CRM ID</th><th>Action</th><th>Status</th><th>Zoho ID</th><th>Error</th></tr>{trs}</table></div>''')

def _zoho_history_where(filter_mode='all', start_date='', end_date='', customer_id=0, table_alias='i'):
    clauses=[]; args=[]
    if filter_mode=='date':
        if start_date:
            clauses.append(f"{table_alias}.issue_date>=?"); args.append(start_date)
        if end_date:
            clauses.append(f"{table_alias}.issue_date<=?"); args.append(end_date)
    elif filter_mode=='customer' and customer_id:
        clauses.append(f"{table_alias}.customer_id=?"); args.append(int(customer_id))
    return (' AND '+ ' AND '.join(clauses)) if clauses else '', args

def _zoho_history_candidates(filter_mode='all', start_date='', end_date='', customer_id=0):
    where,args=_zoho_history_where(filter_mode,start_date,end_date,customer_id,'i')
    with conn() as c:
        invoices=c.execute("SELECT i.id,i.invoice_no,i.customer_id,i.issue_date,i.due_date,i.subtotal,i.amount_paid,i.status,c.account_no,c.first_name,c.last_name,c.company FROM invoices i JOIN customers c ON c.id=i.customer_id WHERE i.status!='Void' AND (i.zoho_invoice_id IS NULL OR i.zoho_invoice_id='')"+where+" ORDER BY i.issue_date,i.id",args).fetchall()
        invoice_ids=[x['id'] for x in invoices]
        customer_ids=sorted(set(x['customer_id'] for x in invoices))
        pclauses=["p.invoice_id IS NOT NULL", "(p.zoho_payment_id IS NULL OR p.zoho_payment_id='')"]
        pargs=[]
        if filter_mode=='customer' and customer_id:
            pclauses.append("p.customer_id=?"); pargs.append(int(customer_id))
        elif filter_mode=='date':
            if start_date: pclauses.append("p.payment_date>=?"); pargs.append(start_date)
            if end_date: pclauses.append("p.payment_date<=?"); pargs.append(end_date)
        payments=c.execute("SELECT p.id,p.customer_id,p.invoice_id,p.amount,p.payment_date,p.method,p.reference,i.invoice_no,i.zoho_invoice_id FROM payments p JOIN invoices i ON i.id=p.invoice_id WHERE "+" AND ".join(pclauses)+" ORDER BY p.payment_date,p.id",pargs).fetchall()
        invset=set(invoice_ids)
        payments=[p for p in payments if p['invoice_id'] in invset or p['zoho_invoice_id']]
        customer_ids=sorted(set(customer_ids)|set(p['customer_id'] for p in payments))
        customers=[]
        if customer_ids:
            q=','.join('?'*len(customer_ids))
            customers=c.execute(f"SELECT id,account_no,first_name,last_name,company,email,zoho_contact_id FROM customers WHERE id IN ({q}) ORDER BY id",customer_ids).fetchall()
    return customers,invoices,payments

@app.get('/zoho/history',response_class=HTMLResponse)
def zoho_history(request:Request,mode:str='all',start_date:str='',end_date:str='',customer_id:int=0):
    require_admin(request)
    if ACCOUNTING_PROVIDER!='zoho': raise HTTPException(409,'Zoho Books must be the active accounting provider for historical synchronization.')
    if not _zoho_oauth(): raise HTTPException(409,'Zoho Books is not connected.')
    mode=mode if mode in ('all','date','customer') else 'all'
    customers,invoices,payments=_zoho_history_candidates(mode,start_date,end_date,customer_id)
    with conn() as c:
        all_customers=c.execute("SELECT id,account_no,first_name,last_name,company FROM customers ORDER BY last_name,first_name").fetchall()
        runs=c.execute("SELECT * FROM zoho_history_runs ORDER BY id DESC LIMIT 10").fetchall()
    customer_options='<option value="0">Select customer</option>'+''.join(f'<option value="{x["id"]}" {"selected" if int(customer_id or 0)==x["id"] else ""}>{html.escape(x["account_no"]+" - "+((x["company"] or "").strip() or (x["first_name"]+" "+x["last_name"])))}</option>' for x in all_customers)
    invrows=''.join(f'<tr><td><input class="hist-invoice" style="width:auto" type="checkbox" name="invoice_ids" value="{x["id"]}" checked></td><td>{html.escape(x["invoice_no"])}</td><td>{html.escape((x["company"] or "").strip() or (x["first_name"]+" "+x["last_name"]))}</td><td>{x["issue_date"]}</td><td>{money(x["subtotal"])}</td><td>{money(x["amount_paid"])}</td><td>{html.escape(x["status"])}</td></tr>' for x in invoices[:50]) or '<tr><td colspan="7">No unsynced invoices match this selection.</td></tr>'
    runrows=''.join(f'<tr><td>{x["started_at"]}</td><td>{html.escape(x["filter_mode"] or "all")}</td><td>{x["invoices_synced"]}/{x["invoices_attempted"]}</td><td>{x["payments_synced"]}/{x["payments_attempted"]}</td><td>{x["failures"]}</td></tr>' for x in runs) or '<tr><td colspan="5">No historical sync runs yet.</td></tr>'
    history_html=f'''<h1>Sync Existing CRM Records to Zoho</h1><div class="notice"><b>Duplicate protection is enabled.</b> Existing Zoho links are skipped, invoice numbers are checked before invoice creation, and CRM payment IDs are used as stable payment references.</div><div class="card"><h2>Preview</h2><form method="get" action="/zoho/history"><label>Selection</label><select name="mode"><option value="all" {"selected" if mode=="all" else ""}>All existing records</option><option value="date" {"selected" if mode=="date" else ""}>Invoice/payment date range</option><option value="customer" {"selected" if mode=="customer" else ""}>One customer</option></select><div class="row"><div><label>Start date</label><input type="date" name="start_date" value="{html.escape(start_date)}"></div><div><label>End date</label><input type="date" name="end_date" value="{html.escape(end_date)}"></div></div><label>Customer</label><select name="customer_id">{customer_options}</select><button class="btn secondary">Refresh Preview</button></form></div><div class="grid section"><div class="card"><div class="kicker">Customers needed</div><div class="metric">{len(customers)}</div></div><div class="card"><div class="kicker">Invoices to sync</div><div class="metric">{len(invoices)}</div></div><div class="card"><div class="kicker">Payments to sync</div><div class="metric">{len(payments)}</div></div><div class="card"><div class="kicker">Already linked</div><div class="metric">Skipped</div></div></div><form method="post" action="/zoho/history/run" id="history-sync-form"><input type="hidden" name="mode" value="{html.escape(mode)}"><input type="hidden" name="start_date" value="{html.escape(start_date)}"><input type="hidden" name="end_date" value="{html.escape(end_date)}"><input type="hidden" name="customer_id" value="{int(customer_id or 0)}"><div class="section"><h2>Invoice Preview</h2><p><button type="button" class="btn secondary" onclick="setHist(true)">Select All</button> <button type="button" class="btn secondary" onclick="setHist(false)">Deselect All</button> <span class="muted">Only checked invoices and their CRM payments will be sent to Zoho.</span></p><table><tr><th style="width:70px">Sync</th><th>Invoice</th><th>Customer</th><th>Issue Date</th><th>Total</th><th>CRM Paid</th><th>Status</th></tr>{invrows}</table>{'<p class="muted">Showing first 50 matching invoices. Sync these or narrow the preview before continuing.</p>' if len(invoices)>50 else ''}</div><div class="card section"><h2>Run Historical Sync</h2><p>Review the checked invoices above. Uncheck tests, demos, training records, or anything else you do not want in Zoho Books. Payments are synchronized only for the invoices you select.</p><label>Maximum invoices this run</label><select name="batch_size"><option>10</option><option selected>25</option><option>50</option></select><label><input style="width:auto;margin-right:8px" type="checkbox" name="confirm" value="YES" required>I reviewed the selected invoices and want to synchronize them to Zoho Books.</label><button class="btn">Sync Selected Invoices</button></div></form><script>function setHist(v){{document.querySelectorAll('.hist-invoice').forEach(function(x){{x.checked=v;}});}}</script><div class="section"><h2>Recent Historical Runs</h2><table><tr><th>Started</th><th>Selection</th><th>Invoices</th><th>Payments</th><th>Failures</th></tr>{runrows}</table></div>'''
    return page(request,'Zoho Historical Sync',history_html)

@app.post('/zoho/history/run')
async def zoho_history_run(request:Request,mode:str=Form('all'),start_date:str=Form(''),end_date:str=Form(''),customer_id:int=Form(0),batch_size:int=Form(25),confirm:str=Form('')):
    require_admin(request)
    if ACCOUNTING_PROVIDER!='zoho': raise HTTPException(409,'Zoho Books must be the active accounting provider.')
    if confirm!='YES': raise HTTPException(400,'Historical synchronization was not confirmed.')
    mode=mode if mode in ('all','date','customer') else 'all'; batch_size=max(1,min(int(batch_size),50))
    form=await request.form(); requested=[]
    for raw in form.getlist('invoice_ids'):
        try: requested.append(int(raw))
        except (TypeError,ValueError): pass
    requested=list(dict.fromkeys(requested))[:batch_size]
    if not requested: raise HTTPException(400,'Select at least one invoice to synchronize.')
    customers,invoices,payments=_zoho_history_candidates(mode,start_date,end_date,customer_id)
    eligible={x['id']:x for x in invoices}; selected_invoices=[eligible[i] for i in requested if i in eligible]
    if not selected_invoices: raise HTTPException(409,'The selected invoices are no longer eligible for synchronization. Refresh the preview and try again.')
    selected_invoice_ids={x['id'] for x in selected_invoices}
    started=datetime.utcnow().isoformat(); user=request.session.get('user_email','admin')
    with conn() as c:
        cur=c.execute("INSERT INTO zoho_history_runs(filter_mode,start_date,end_date,customer_id,batch_size,invoices_attempted,payments_attempted,started_at,run_by) VALUES (?,?,?,?,?,?,?,?,?)",(mode,start_date,end_date,customer_id or None,batch_size,len(selected_invoices),0,started,user)); run_id=cur.lastrowid
    inv_ok=pay_ok=fail=0
    for x in selected_invoices:
        zoho_try('invoice',x['id'])
        with conn() as c: r=c.execute("SELECT zoho_invoice_id FROM invoices WHERE id=?",(x['id'],)).fetchone()
        if r and r['zoho_invoice_id']: inv_ok+=1
        else: fail+=1
    with conn() as c:
        qmarks=','.join('?'*len(selected_invoice_ids))
        chosen=c.execute(f"SELECT id FROM payments WHERE invoice_id IN ({qmarks}) AND (zoho_payment_id IS NULL OR zoho_payment_id='') ORDER BY payment_date,id",list(selected_invoice_ids)).fetchall()
    for p in chosen:
        zoho_try('payment',p['id'])
        with conn() as c: r=c.execute("SELECT zoho_payment_id FROM payments WHERE id=?",(p['id'],)).fetchone()
        if r and r['zoho_payment_id']: pay_ok+=1
        else: fail+=1
    with conn() as c:
        c.execute("UPDATE zoho_history_runs SET payments_attempted=?,invoices_synced=?,payments_synced=?,failures=?,completed_at=? WHERE id=?",(len(chosen),inv_ok,pay_ok,fail,datetime.utcnow().isoformat(),run_id))
    audit(request,'historical_sync','zoho',run_id,f'mode={mode}; selected={sorted(selected_invoice_ids)}; invoices={inv_ok}/{len(selected_invoices)}; payments={pay_ok}/{len(chosen)}; failures={fail}')
    q=urllib.parse.urlencode({'mode':mode,'start_date':start_date,'end_date':end_date,'customer_id':customer_id})
    return RedirectResponse('/zoho/history?'+q,303)

@app.get('/zoho/connect')
def zoho_connect(request:Request):
    require_admin(request)
    if not ZOHO_ENABLED: raise HTTPException(409,'Zoho Books integration is disabled in Render.')
    if not ZOHO_CLIENT_ID or not ZOHO_CLIENT_SECRET: raise HTTPException(409,'Zoho credentials are not configured.')
    state=secrets.token_urlsafe(32); request.session['zoho_oauth_state']=state
    params={'scope':ZOHO_SCOPES,'client_id':ZOHO_CLIENT_ID,'response_type':'code','redirect_uri':ZOHO_REDIRECT_URI,'access_type':'offline','prompt':'consent','state':state}
    return RedirectResponse(ZOHO_ACCOUNTS_BASE+'/oauth/v2/auth?'+urllib.parse.urlencode(params),303)

@app.get('/zoho/callback')
def zoho_callback(request:Request,code:str='',state:str='',error:str='',location:str='',accounts_server:str=''):
    require_admin(request)
    if error: raise HTTPException(400,'Zoho OAuth error: '+error)
    expected=request.session.get('zoho_oauth_state','')
    if not state or not hmac.compare_digest(state,expected): raise HTTPException(400,'Invalid Zoho OAuth state.')
    if not code: raise HTTPException(400,'Zoho authorization code is missing.')
    tok=_zoho_token_request({'grant_type':'authorization_code','code':code,'redirect_uri':ZOHO_REDIRECT_URI})
    _zoho_store_tokens(tok)
    # Organization discovery is required for every Zoho Books API request.
    orgs=_zoho_api('GET','organizations',require_org=False).get('organizations') or []
    if not orgs: raise HTTPException(409,'No Zoho Books organization was found for this account.')
    chosen=next((x for x in orgs if x.get('is_default_org')),orgs[0])
    row=_zoho_oauth(); _zoho_store_tokens({'access_token':row['access_token'],'refresh_token':row['refresh_token'],'expires_in':3600,'api_domain':row['api_domain']},str(chosen['organization_id']),str(chosen.get('name') or ''))
    request.session.pop('zoho_oauth_state',None)
    return RedirectResponse('/integrations/zoho',303)

@app.get('/zoho/test')
def zoho_test(request:Request):
    require_admin(request); row=_zoho_oauth()
    if not row or not row['organization_id']: raise HTTPException(409,'Zoho Books is not connected.')
    out=_zoho_api('GET','organizations/'+str(row['organization_id']))
    org=out.get('organization') or {}; name=str(org.get('name') or row['organization_name'] or '')
    with conn() as c: c.execute("UPDATE zoho_oauth SET organization_name=?,updated_at=? WHERE id=1",(name,datetime.utcnow().isoformat()))
    return RedirectResponse('/integrations/zoho',303)

@app.post('/zoho/disconnect')
def zoho_disconnect(request:Request):
    require_admin(request)
    with conn() as c: c.execute("DELETE FROM zoho_oauth WHERE id=1")
    return RedirectResponse('/integrations/zoho',303)

@app.post('/zoho/retry')
def zoho_retry(request:Request):
    require_admin(request)
    if ACCOUNTING_PROVIDER!='zoho': raise HTTPException(409,'Zoho Books is not the active accounting provider. Retry is blocked to prevent duplicate accounting entries.')
    with conn() as c:
        cs=[x['id'] for x in c.execute("SELECT id FROM customers WHERE zoho_sync_status='Failed'").fetchall()]
        ins=[x['id'] for x in c.execute("SELECT id FROM invoices WHERE zoho_sync_status='Failed'").fetchall()]
        ps=[x['id'] for x in c.execute("SELECT id FROM payments WHERE zoho_sync_status='Failed'").fetchall()]
    for x in cs: zoho_try('customer',x)
    for x in ins: zoho_try('invoice',x)
    for x in ps: zoho_try('payment',x)
    return RedirectResponse('/integrations/zoho',303)

@app.get('/integrations/quickbooks',response_class=HTMLResponse)
def quickbooks_integration(request:Request):
    require_admin(request); row=_qb_oauth()
    connected=bool(row and row['refresh_token']); company=(row['company_name'] if row else '') or ''
    with conn() as c: logs=c.execute("SELECT * FROM quickbooks_sync_log ORDER BY id DESC LIMIT 50").fetchall()
    trs=''.join(f"<tr><td>{x['created_at']}</td><td>{html.escape(x['entity_type'])}</td><td>{x['entity_id'] or ''}</td><td>{html.escape(x['action'] or '')}</td><td>{html.escape(x['status'] or '')}</td><td>{html.escape(x['quickbooks_id'] or '')}</td><td>{html.escape((x['error'] or '')[:180])}</td></tr>" for x in logs) or '<tr><td colspan=7>No QuickBooks sync activity yet.</td></tr>'
    status='<span class="pill">Connected</span>' if connected else '<span class="pill bad">Not Connected</span>'
    btn='<a class="btn" href="/quickbooks/connect">Connect QuickBooks</a>' if not connected else '<a class="btn secondary" href="/quickbooks/test">Test Connection</a> <form style="display:inline" method="post" action="/quickbooks/disconnect"><button class="btn danger">Disconnect</button></form>'
    qb_active='<span class="pill">Active accounting provider</span>' if ACCOUNTING_PROVIDER=='quickbooks' else '<span class="pill warn">Inactive / standby</span>'; retry_html='<form method="post" action="/quickbooks/retry"><button class="btn">Retry Failed Syncs</button></form>' if ACCOUNTING_PROVIDER=='quickbooks' else '<p class="muted">New CRM records are not sent to QuickBooks while another accounting provider is active. Retry is disabled to prevent accidental duplicate entries.</p>'; return page(request,'QuickBooks Online',f'''<h1>QuickBooks Online</h1><div class="card"><p><b>Status:</b> {status}</p><p><b>Accounting Provider:</b> {html.escape(ACCOUNTING_PROVIDER)} {qb_active}</p><p><b>Environment:</b> {html.escape(QUICKBOOKS_ENVIRONMENT)}</p><p><b>Company:</b> {html.escape(company or 'Not connected')}</p><p><b>Redirect URI:</b> {html.escape(QUICKBOOKS_REDIRECT_URI)}</p><div class="actions">{btn}</div></div><div class="card section"><h2>Synchronization</h2>{retry_html}</div><div class="section"><h2>Recent Sync Activity</h2><table><tr><th>Time</th><th>Type</th><th>CRM ID</th><th>Action</th><th>Status</th><th>QB ID</th><th>Error</th></tr>{trs}</table></div>''')

@app.get('/quickbooks/connect')
def quickbooks_connect(request:Request):
    require_admin(request)
    if not QUICKBOOKS_ENABLED: raise HTTPException(409,'QuickBooks integration is disabled in Render.')
    if not QUICKBOOKS_CLIENT_ID or not QUICKBOOKS_CLIENT_SECRET: raise HTTPException(409,'QuickBooks credentials are not configured.')
    state=secrets.token_urlsafe(32); request.session['qb_oauth_state']=state
    params={'client_id':QUICKBOOKS_CLIENT_ID,'response_type':'code','scope':'com.intuit.quickbooks.accounting','redirect_uri':QUICKBOOKS_REDIRECT_URI,'state':state}
    return RedirectResponse(QB_AUTH_URL+'?'+urllib.parse.urlencode(params),302)

@app.get('/quickbooks/callback')
def quickbooks_callback(request:Request,code:str='',state:str='',realmId:str='',error:str=''):
    require_admin(request)
    if error: raise HTTPException(400,f'QuickBooks authorization failed: {error}')
    if not state or not hmac.compare_digest(state,request.session.get('qb_oauth_state','')): raise HTTPException(400,'Invalid QuickBooks OAuth state.')
    tok=_qb_token_request({'grant_type':'authorization_code','code':code,'redirect_uri':QUICKBOOKS_REDIRECT_URI}); _qb_store_tokens(tok,realmId)
    try:
        info=_qb_api('GET','companyinfo/'+realmId).get('CompanyInfo',{}); name=info.get('CompanyName','')
        with conn() as c: c.execute("UPDATE quickbooks_oauth SET company_name=? WHERE id=1",(name,))
    except Exception: pass
    request.session.pop('qb_oauth_state',None); return RedirectResponse('/integrations/quickbooks',303)

@app.get('/quickbooks/test')
def quickbooks_test(request:Request):
    require_admin(request); token,realm=_qb_access_token(); info=_qb_api('GET','companyinfo/'+realm).get('CompanyInfo',{}); name=info.get('CompanyName','')
    with conn() as c: c.execute("UPDATE quickbooks_oauth SET company_name=?,updated_at=? WHERE id=1",(name,datetime.utcnow().isoformat()))
    return RedirectResponse('/integrations/quickbooks',303)

@app.post('/quickbooks/disconnect')
def quickbooks_disconnect(request:Request):
    require_admin(request)
    with conn() as c: c.execute("DELETE FROM quickbooks_oauth WHERE id=1")
    return RedirectResponse('/integrations/quickbooks',303)

@app.post('/quickbooks/retry')
def quickbooks_retry(request:Request):
    require_admin(request)
    if ACCOUNTING_PROVIDER!='quickbooks': raise HTTPException(409,'QuickBooks is not the active accounting provider. Retry is blocked to prevent duplicate accounting entries.')
    with conn() as c:
        cs=[x['id'] for x in c.execute("SELECT id FROM customers WHERE quickbooks_sync_status='Failed'").fetchall()]
        ins=[x['id'] for x in c.execute("SELECT id FROM invoices WHERE quickbooks_sync_status='Failed'").fetchall()]
        ps=[x['id'] for x in c.execute("SELECT id FROM payments WHERE quickbooks_sync_status='Failed'").fetchall()]
    for x in cs: qb_try('customer',x)
    for x in ins: qb_try('invoice',x)
    for x in ps: qb_try('payment',x)
    return RedirectResponse('/integrations/quickbooks',303)

@app.get('/payments',response_class=HTMLResponse)
def payments(request:Request):
    require_staff(request)
    with conn() as c: rows=c.execute("SELECT p.*,c.account_no,c.first_name,c.last_name,i.invoice_no FROM payments p JOIN customers c ON c.id=p.customer_id LEFT JOIN invoices i ON i.id=p.invoice_id ORDER BY p.id DESC").fetchall()
    trs=''.join(f"<tr><td>{x['payment_date']}</td><td>{x['account_no']} — {x['first_name']} {x['last_name']}</td><td>{x['invoice_no'] or ''}</td><td>{money(x['amount'])}</td><td>{x['method'] or ''}</td><td>{x['reference'] or ''}</td></tr>" for x in rows)
    return page(request,'Payments',f'''<h1>Payments</h1><table><tr><th>Date</th><th>Customer</th><th>Invoice</th><th>Amount</th><th>Method</th><th>Reference</th></tr>{trs}</table>''')
@app.post('/payments')
def payment_add(request:Request,customer_id:int=Form(...),invoice_id:int=Form(...),amount:float=Form(...),method:str=Form('Other'),reference:str=Form('')):
    require_staff(request)
    if amount <= 0: raise HTTPException(400,'Payment amount must be greater than zero.')
    with conn() as c:
        inv=c.execute("SELECT status,subtotal,amount_paid,customer_id FROM invoices WHERE id=?",(invoice_id,)).fetchone()
        if not inv or int(inv['customer_id'])!=int(customer_id): raise HTTPException(404,'Invoice not found.')
        if inv['status']=='Void': raise HTTPException(409,'Payments cannot be posted to a void invoice.')
        balance=float(inv['subtotal'])-float(inv['amount_paid'] or 0)
        if amount > balance + .005: raise HTTPException(409,'Payment exceeds the invoice balance.')
        cur=c.execute("INSERT INTO payments(customer_id,invoice_id,amount,payment_date,method,reference) VALUES (?,?,?,?,?,?)",(customer_id,invoice_id,amount,date.today().isoformat(),method,reference)); pid=cur.lastrowid; c.execute("UPDATE invoices SET amount_paid=amount_paid+? WHERE id=?",(amount,invoice_id)); update_invoice_status(c,invoice_id)
    audit(request,'CREATE','payment',pid,f'invoice={invoice_id}; amount={amount}'); accounting_try('payment',pid)
    try: maybe_restore_after_payment(customer_id)
    except Exception as e: audit(request,'ERROR','carrier_restore',customer_id,str(e))
    return RedirectResponse(f'/invoices/{invoice_id}',303)

COLLECTION_STAGE_COPY = {
    'Past-Due Notice': {
        'subject': 'Past-Due Account Notice',
        'heading': 'PAST-DUE ACCOUNT NOTICE',
        'paragraphs': [
            'Our records show that your Entire Wireless account has a past-due balance of {balance}. This letter is being sent by Entire Wireless Internal Collections to provide formal notice of the outstanding balance on account {account}.',
            'Please remit payment promptly or contact Entire Wireless if you believe the balance is incorrect or need to discuss available account options. Payment and account information may be reviewed through the customer portal.',
            'If the balance remains unpaid, the account may remain subject to collection activity and other actions permitted by your service agreement and applicable law.'
        ]
    },
    'Second Collection Notice': {
        'subject': 'Second Collection Notice',
        'heading': 'SECOND COLLECTION NOTICE',
        'paragraphs': [
            'Entire Wireless Internal Collections is contacting you again regarding the past-due balance of {balance} on account {account}. Our records indicate that the balance remains outstanding as of the date of this letter.',
            'Please make payment promptly or contact Entire Wireless to address the account. If you have already submitted payment, please allow appropriate processing time and retain this notice for your records.',
            'Continued nonpayment may result in additional collection activity and other account actions permitted by your service agreement and applicable law.'
        ]
    },
    'Final Collection Notice': {
        'subject': 'Final Internal Collection Notice',
        'heading': 'FINAL INTERNAL COLLECTION NOTICE',
        'paragraphs': [
            'This is a final internal collection notice from Entire Wireless regarding the past-due balance of {balance} on account {account}. The balance remains outstanding according to our records.',
            'Please pay the outstanding balance or contact Entire Wireless promptly to resolve the account. If you dispute the balance, contact us with the details of your concern so the account can be reviewed.',
            'If the account remains unresolved, Entire Wireless may pursue further collection activity or other remedies available under the service agreement and applicable law. This notice does not state that any particular legal or third-party collection action has already been taken.'
        ]
    }
}

def customer_past_due_balance(c, cid):
    row=c.execute("SELECT COALESCE(SUM(CASE WHEN status NOT IN ('Paid','Void') AND due_date < date('now') THEN MAX(subtotal-amount_paid,0) ELSE 0 END),0) AS balance FROM invoices WHERE customer_id=?",(cid,)).fetchone()
    return float(row['balance'] or 0)

def generate_collection_letter(cid, stage, generated_by=''):
    if stage not in COLLECTION_STAGE_COPY: raise ValueError('Invalid collection letter stage')
    with conn() as c:
        cust=c.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone()
        if not cust: raise ValueError('Customer not found')
        balance=customer_past_due_balance(c,cid)
        if balance <= .005: raise ValueError('Customer does not have a past-due balance')
        cur=c.execute("INSERT INTO collection_letters(customer_id,stage,balance,generated_by) VALUES (?,?,?,?)",(cid,stage,balance,generated_by or 'CRM'))
        lid=cur.lastrowid
        safe_account=''.join(ch for ch in str(cust['account_no']) if ch.isalnum() or ch in ('-','_'))
        path=COLLECTIONS / f"{safe_account}-{lid}-{stage.replace(' ','-')}.pdf"
        cfg=COLLECTION_STAGE_COPY[stage]
        pdf=canvas.Canvas(str(path),pagesize=letter); w,h=letter
        # Reuse the user's #9 double-window letterhead artwork.
        art=BASE/'entire_wireless_collections_letterhead.png'
        if art.exists():
            pdf.drawImage(str(art),.50*inch,h-.88*inch,width=1.15*inch,height=.46*inch,preserveAspectRatio=True,mask='auto')
        else:
            logo=BASE/'entire_wireless_logo.png'
            if logo.exists(): pdf.drawImage(str(logo),.50*inch,h-.88*inch,width=1.15*inch,height=.46*inch,preserveAspectRatio=True,mask='auto')
        pdf.setFillColorRGB(37/255,150/255,190/255); pdf.setFont('Helvetica-Bold',8.5); pdf.drawString(1.68*inch,h-.56*inch,'ENTIRE WIRELESS')
        pdf.setFillColorRGB(0,0,0); pdf.setFont('Helvetica',7.5); pdf.drawString(1.68*inch,h-.71*inch,'35412 N 770 East Rd'); pdf.drawString(1.68*inch,h-.84*inch,'Rossville, IL 60963')
        # Address block aligned to the attached #9 double-window letterhead.
        y=h-2.05*inch; pdf.setFont('Helvetica-Bold',10)
        full=f"{cust['first_name']} {cust['last_name']}".strip(); pdf.drawString(.72*inch,y,full); y-=.18*inch
        pdf.setFont('Helvetica',10)
        if cust['company']: pdf.drawString(.72*inch,y,str(cust['company'])); y-=.18*inch
        addr=cust['billing_address'] or cust['service_address'] or ''
        if addr: pdf.drawString(.72*inch,y,str(addr)); y-=.18*inch
        cityline=', '.join(x for x in [str(cust['city'] or '').strip(), str(cust['state'] or '').strip()] if x)
        if cust['zip']: cityline=(cityline+' '+str(cust['zip'])).strip()
        if cityline: pdf.drawString(.72*inch,y,cityline)
        # Letter body
        y=h-3.25*inch; pdf.setFont('Helvetica',10); pdf.drawString(.72*inch,y,business_now().strftime('%B %d, %Y')); y-=.42*inch
        pdf.setFont('Helvetica-Bold',10); pdf.drawString(.72*inch,y,cfg['heading']); y-=.32*inch
        pdf.setFont('Helvetica',10); pdf.drawString(.72*inch,y,f"Dear {cust['first_name']} {cust['last_name']}:"); y-=.34*inch
        for para in cfg['paragraphs']:
            text=para.format(balance=money(balance),account=cust['account_no'])
            for line in _wrap_pdf_text(text,96):
                pdf.drawString(.72*inch,y,line); y-=.18*inch
            y-=.15*inch
        pdf.setFont('Helvetica-Bold',10); pdf.drawString(.72*inch,y,'Account Number:'); pdf.setFont('Helvetica',10); pdf.drawString(2.0*inch,y,str(cust['account_no'])); y-=.22*inch
        pdf.setFont('Helvetica-Bold',10); pdf.drawString(.72*inch,y,'Past-Due Balance:'); pdf.setFont('Helvetica',10); pdf.drawString(2.0*inch,y,money(balance)); y-=.38*inch
        pdf.drawString(.72*inch,y,'Sincerely,'); y-=.25*inch; pdf.setFont('Helvetica-Bold',10); pdf.drawString(.72*inch,y,'Entire Wireless Internal Collections'); y-=.18*inch
        pdf.setFont('Helvetica',9); pdf.drawString(.72*inch,y,f'{COMPANY_PHONE}  |  {SUPPORT_EMAIL}')
        # Fixed collections disclosure: printed on every collection notice.
        disclosure = ('NOTICE: This communication is from Entire Wireless Internal Collections. '
                      'This is an attempt to collect a debt, and any information obtained will be used for that purpose.')
        pdf.setFillColorRGB(.25,.25,.25); pdf.setFont('Helvetica',6.5)
        disclosure_y = .68*inch
        for disclosure_line in reversed(_wrap_pdf_text(disclosure,126)):
            pdf.drawString(.72*inch,disclosure_y,disclosure_line)
            disclosure_y += .11*inch
        # Footer matching the attached letterhead's contact strip.
        pdf.setStrokeColorRGB(75/255,180/255,73/255); pdf.setLineWidth(1.2); pdf.line(.72*inch,.48*inch,w-.72*inch,.48*inch)
        pdf.setFillColorRGB(37/255,150/255,190/255); pdf.setFont('Helvetica',7.5); pdf.drawCentredString(w/2,.28*inch,f'natureswireless.org   |   {SUPPORT_EMAIL}   |   (815) 694-WIRE (9473)')
        pdf.save()
        c.execute("UPDATE collection_letters SET pdf_path=? WHERE id=?",(str(path),lid))
        return lid,path,balance,cust

def email_collection_letter(lid):
    with conn() as c:
        r=c.execute("SELECT cl.*,c.email,c.first_name,c.last_name,c.account_no FROM collection_letters cl JOIN customers c ON c.id=cl.customer_id WHERE cl.id=?",(lid,)).fetchone()
        if not r or not r['email'] or not r['pdf_path']: return False
        cfg=COLLECTION_STAGE_COPY.get(r['stage'],COLLECTION_STAGE_COPY['Past-Due Notice'])
        body=f"Hello {r['first_name']},\n\nAttached is your {r['stage']} from Entire Wireless Internal Collections.\n\nAccount: {r['account_no']}\nPast-due balance: {money(r['balance'])}\n\nIf you have already paid or believe the balance is incorrect, please contact {SUPPORT_EMAIL} or {COMPANY_PHONE}.\n\nNOTICE: This communication is from Entire Wireless Internal Collections. This is an attempt to collect a debt, and any information obtained will be used for that purpose.\n\nEntire Wireless Internal Collections\n{COMPANY_SITE}"
        ok=smtp_send(r['email'],f"{cfg['subject']} — Account {r['account_no']}",body,r['pdf_path'])
        if ok: c.execute("UPDATE collection_letters SET emailed_at=?,email_to=? WHERE id=?",(business_now().isoformat(timespec='seconds'),r['email'],lid))
        return ok

@app.get('/collections',response_class=HTMLResponse)
def collections_center(request:Request, customer_id:int=0):
    require_staff(request)
    with conn() as c:
        rows=c.execute("""SELECT c.id,c.account_no,c.first_name,c.last_name,c.company,c.email,c.billing_address,c.service_address,c.city,c.state,c.zip,
            COALESCE(SUM(CASE WHEN i.status NOT IN ('Paid','Void') AND i.due_date < date('now') THEN MAX(i.subtotal-i.amount_paid,0) ELSE 0 END),0) balance,
            MIN(CASE WHEN i.status NOT IN ('Paid','Void') AND i.due_date < date('now') AND (i.subtotal-i.amount_paid)>.005 THEN i.due_date END) oldest_due
            FROM customers c LEFT JOIN invoices i ON i.customer_id=c.id GROUP BY c.id HAVING balance>.005 ORDER BY oldest_due,c.last_name,c.first_name""").fetchall()
        history=c.execute("""SELECT cl.*,c.account_no,c.first_name,c.last_name FROM collection_letters cl JOIN customers c ON c.id=cl.customer_id ORDER BY cl.id DESC LIMIT 100""").fetchall()
    filtered=[r for r in rows if not customer_id or r['id']==customer_id]
    trs=''.join(f"<tr><td><a href='/customers/{r['id']}'>{html.escape(r['account_no'])}</a></td><td>{html.escape((r['company'] or (r['first_name']+' '+r['last_name'])))}</td><td>{money(r['balance'])}</td><td>{html.escape(str(r['oldest_due'] or ''))}</td><td>{html.escape(r['email'] or '')}</td><td><form method='post' action='/collections/generate'><input type='hidden' name='customer_id' value='{r['id']}'><select name='stage'><option>Past-Due Notice</option><option>Second Collection Notice</option><option>Final Collection Notice</option></select><button class='btn' type='submit'>Generate Letter</button></form></td></tr>" for r in filtered) or '<tr><td colspan=6 class="muted">No customers currently have an eligible past-due balance.</td></tr>'
    htrs=''.join(f"<tr><td>{html.escape(str(r['generated_at'] or ''))}</td><td>{html.escape(r['account_no'])}</td><td>{html.escape(r['first_name']+' '+r['last_name'])}</td><td>{html.escape(r['stage'])}</td><td>{money(r['balance'])}</td><td>{('<span class=\"pill\">Emailed</span>' if r['emailed_at'] else '<span class=\"pill warn\">Not emailed</span>')}</td><td><a class='btn secondary' target='_blank' href='/collections/{r['id']}/pdf'>Print PDF</a> <form style='display:inline' method='post' action='/collections/{r['id']}/email'><button class='btn' type='submit'>Email</button></form></td></tr>" for r in history) or '<tr><td colspan=7 class="muted">No collection letters generated yet.</td></tr>'
    return page(request,'Internal Collections',f"""<h1>Entire Wireless Internal Collections</h1><div class="notice"><b>Manual collections workflow.</b> Customers below have a past-due balance based on CRM invoices. Review the account before generating or emailing a notice. Letters are preconfigured and use the Entire Wireless #9 double-window letterhead for printing and mailing.</div><div class="section card"><h2>Customers Subject to Collection Activity</h2><table><tr><th>Account</th><th>Customer</th><th>Past-Due Balance</th><th>Oldest Due Date</th><th>Email</th><th>Collection Letter</th></tr>{trs}</table></div><div class="section card"><h2>Collection Letter History</h2><table><tr><th>Generated</th><th>Account</th><th>Customer</th><th>Notice</th><th>Balance</th><th>Email Status</th><th>Actions</th></tr>{htrs}</table></div>""")

@app.post('/collections/generate')
def collections_generate(request:Request,customer_id:int=Form(...),stage:str=Form(...)):
    require_staff(request)
    try:
        lid,path,balance,cust=generate_collection_letter(customer_id,stage,request.session.get('user_email',''))
        audit(request,'GENERATE','collection_letter',lid,f'{stage}; customer {customer_id}; balance {money(balance)}')
        return RedirectResponse(f'/collections/{lid}/pdf',303)
    except ValueError as e:
        return page(request,'Collections Error',f'<h1>Collection Letter Not Generated</h1><div class="notice">{html.escape(str(e))}</div><a class="btn secondary" href="/collections">Back to Internal Collections</a>')

@app.get('/collections/{lid}/pdf')
def collections_pdf(request:Request,lid:int):
    require_staff(request)
    with conn() as c: r=c.execute("SELECT cl.*,c.account_no FROM collection_letters cl JOIN customers c ON c.id=cl.customer_id WHERE cl.id=?",(lid,)).fetchone()
    if not r or not r['pdf_path'] or not Path(r['pdf_path']).exists(): raise HTTPException(404)
    return FileResponse(r['pdf_path'],media_type='application/pdf',filename=f"Entire-Wireless-Collection-Letter-{r['account_no']}.pdf")

@app.post('/collections/{lid}/email')
def collections_email(request:Request,lid:int):
    require_staff(request)
    ok=email_collection_letter(lid)
    audit(request,'EMAIL','collection_letter',lid,'sent' if ok else 'failed')
    return RedirectResponse('/collections',303)

@app.get('/billing',response_class=HTMLResponse)
def billing(request:Request):
    require_staff(request)
    return page(request,'Billing Center',f'''<h1>Billing Center</h1><div class="three"><div class="card"><h2>Recurring Billing</h2><p>Generate monthly invoices for subscribers whose billing day is today.</p><form method="post" action="/billing/run"><button class="btn">Run Monthly Billing</button></form></div><div class="card"><h2>End-of-Business Past-Due Notices</h2><p>At {BUSINESS_CLOSE_HOUR}:00 {BUSINESS_TIMEZONE}, unpaid invoices due that day receive a formal PDF past-due notice by email.</p><form method="post" action="/billing/eod-notices"><button class="btn danger">Run Due-Date Notices Now</button></form></div><div class="card"><h2>Follow-up Reminders</h2><p>Send follow-up reminders on already-noticed past-due invoices.</p><form method="post" action="/billing/reminders"><button class="btn secondary">Run Reminders</button></form></div></div>''')
@app.post('/billing/run')
def billing_run(request:Request): require_admin(request); ids=run_monthly_billing(True); audit(request,'RUN','billing',None,f'{len(ids)} invoices'); return RedirectResponse('/invoices',303)
@app.post('/billing/eod-notices')
def billing_eod_notices(request:Request): require_admin(request); n=run_eod_due_notices(True); audit(request,'RUN','eod_past_due_notices',None,f'{n} notices'); return RedirectResponse('/billing',303)

@app.post('/billing/reminders')
def billing_reminders(request:Request): require_admin(request); n=run_daily_tasks(); audit(request,'RUN','reminders',None,f'{n} reminders'); return RedirectResponse('/billing',303)

def _report_pdf(title,headers,rows,filename):
    path=STATEMENTS/filename; p=canvas.Canvas(str(path),pagesize=letter); w,h=letter; left=.45*inch; right=w-.45*inch; y=h-.55*inch
    widths=[(right-left)/max(len(headers),1)]*len(headers)
    def header():
        nonlocal y
        try:
            logo=BASE/'entire_wireless_logo.png'
            if logo.exists(): p.drawImage(ImageReader(str(logo)),left,h-.7*inch,width=1.35*inch,height=.43*inch,preserveAspectRatio=True,mask='auto')
        except Exception: pass
        p.setFont('Helvetica-Bold',15); p.drawString(left+1.55*inch,h-.48*inch,title); p.setFont('Helvetica',8); p.drawRightString(right,h-.48*inch,datetime.now().strftime('Generated %Y-%m-%d %H:%M')); y=h-.95*inch; p.setFont('Helvetica-Bold',7); x=left
        for i,v in enumerate(headers): p.drawString(x,y,str(v)[:28]); x+=widths[i]
        y-=.16*inch; p.line(left,y+.06*inch,right,y+.06*inch)
    header(); p.setFont('Helvetica',7)
    for row in rows:
        if y<.55*inch: p.showPage(); header(); p.setFont('Helvetica',7)
        x=left
        for i,v in enumerate(row):
            txt=str(v if v is not None else ''); maxchars=max(8,int(widths[i]/4.2)); p.drawString(x,y,txt[:maxchars]); x+=widths[i]
        y-=.17*inch
    p.save(); return path

@app.get('/reports/modems.pdf')
def report_modems(request:Request,status:str='all'):
    require_staff(request); status=status.lower(); where=''
    if status=='available': where="WHERE m.customer_id IS NULL AND m.status='Available'"
    elif status=='assigned': where="WHERE m.customer_id IS NOT NULL"
    elif status!='all': raise HTTPException(400,'Invalid report status')
    with conn() as c: rows=c.execute(f"SELECT m.imei,m.serial_no,m.manufacturer,m.model,m.status,c.account_no,c.first_name,c.last_name FROM modems m LEFT JOIN customers c ON c.id=m.customer_id {where} ORDER BY m.imei").fetchall()
    data=[(r['imei'],r['serial_no'] or '',r['manufacturer'] or '',r['model'] or '',r['status'],((r['account_no'] or '')+' '+(r['first_name'] or '')+' '+(r['last_name'] or '')).strip()) for r in rows]
    path=_report_pdf(f"{status.title()} IMEI Inventory",['IMEI','Serial','Manufacturer','Model','Status','Assigned Customer'],data,f'imei-{status}.pdf'); return FileResponse(path,media_type='application/pdf',filename=f'Entire-Wireless-IMEI-{status}.pdf')

@app.get('/reports/sims.pdf')
def report_sims(request:Request,status:str='all'):
    require_staff(request); status=status.lower(); where=''
    if status=='available': where="WHERE s.customer_id IS NULL AND s.status='Available'"
    elif status=='assigned': where="WHERE s.customer_id IS NOT NULL"
    elif status!='all': raise HTTPException(400,'Invalid report status')
    with conn() as c: rows=c.execute(f"SELECT s.iccid,s.carrier,s.mdn,s.status,c.account_no,c.first_name,c.last_name FROM sims s LEFT JOIN customers c ON c.id=s.customer_id {where} ORDER BY s.iccid").fetchall()
    data=[(r['iccid'],r['carrier'] or '',r['mdn'] or '',r['status'],((r['account_no'] or '')+' '+(r['first_name'] or '')+' '+(r['last_name'] or '')).strip()) for r in rows]
    path=_report_pdf(f"{status.title()} SIM / ICCID Inventory",['ICCID','Carrier','MDN','Status','Assigned Customer'],data,f'sim-{status}.pdf'); return FileResponse(path,media_type='application/pdf',filename=f'Entire-Wireless-SIM-{status}.pdf')

@app.get('/reports/customers.pdf')
def report_customers(request:Request,status:str='all'):
    require_staff(request); status=status.lower(); where=''; params=()
    if status in ('active','inactive'): where='WHERE lower(c.status)=?'; params=(status,)
    elif status!='all': raise HTTPException(400,'Invalid report status')
    with conn() as c: rows=c.execute(f"SELECT c.account_no,c.first_name,c.last_name,c.customer_type,c.company,c.email,c.phone,c.status,p.name plan FROM customers c LEFT JOIN subscriptions s ON s.customer_id=c.id LEFT JOIN plans p ON p.id=s.plan_id {where} ORDER BY c.last_name,c.first_name",params).fetchall()
    data=[(r['account_no'],f"{r['first_name']} {r['last_name']}",r['customer_type'] or 'Residential',r['company'] or '',r['email'] or '',r['phone'] or '',r['status'],r['plan'] or '') for r in rows]
    path=_report_pdf(f"{status.title()} Customer Report",['Account','Customer','Type','Company','Email','Phone','Status','Plan'],data,f'customers-{status}.pdf'); return FileResponse(path,media_type='application/pdf',filename=f'Entire-Wireless-Customers-{status}.pdf')

@app.get('/reports/customers/{cid}.pdf')
def report_customer_detail(request:Request,cid:int):
    require_staff(request)
    with conn() as c:
        r=c.execute("SELECT c.*,p.name plan FROM customers c LEFT JOIN subscriptions s ON s.customer_id=c.id LEFT JOIN plans p ON p.id=s.plan_id WHERE c.id=?",(cid,)).fetchone()
        if not r: raise HTTPException(404,'Customer not found')
        ms=c.execute("SELECT imei,manufacturer,model,status FROM modems WHERE customer_id=?",(cid,)).fetchall(); ss=c.execute("SELECT iccid,carrier,mdn,status FROM sims WHERE customer_id=?",(cid,)).fetchall(); ns=c.execute("SELECT created_at,category,user_name,note FROM customer_notes WHERE customer_id=? ORDER BY id DESC",(cid,)).fetchall()
    rows=[('Account',r['account_no']),('Customer',f"{r['first_name']} {r['last_name']}"),('Customer Type',r['customer_type'] or 'Residential'),('Company',r['company'] or ''),('Status',r['status']),('Plan',r['plan'] or ''),('Email',r['email'] or ''),('Phone',r['phone'] or ''),('Service Address',f"{r['service_address'] or ''}, {r['city'] or ''}, {r['state'] or ''} {r['zip'] or ''}")]
    rows += [('IMEI',f"{x['imei']} {x['manufacturer'] or ''} {x['model'] or ''} [{x['status']}]") for x in ms]; rows += [('SIM/ICCID',f"{x['iccid']} {x['carrier'] or ''} {x['mdn'] or ''} [{x['status']}]") for x in ss]; rows += [('Support Note',f"{x['created_at']} | {x['category']} | {x['user_name'] or ''} | {x['note']}") for x in ns]
    path=_report_pdf(f"Customer Report - {r['account_no']}",['Section','Details'],rows,f'customer-{cid}.pdf'); return FileResponse(path,media_type='application/pdf',filename=f"Entire-Wireless-Customer-{r['account_no']}.pdf")

@app.get('/reports',response_class=HTMLResponse)
def reports(request:Request):
    require_staff(request)
    with conn() as c:
        aging=[]
        for label,lo,hi in [('Current',0,0),('1-30',1,30),('31-60',31,60),('61-90',61,90),('90+',91,9999)]:
            total=0
            for r in c.execute("SELECT due_date,subtotal,amount_paid,status FROM invoices WHERE status NOT IN ('Paid','Void')").fetchall():
                d=(date.today()-date.fromisoformat(r['due_date'])).days
                if (label=='Current' and d<=0) or (label!='Current' and lo<=d<=hi): total+=r['subtotal']-r['amount_paid']
            aging.append((label,total))
        histories=c.execute("SELECT h.*,c.account_no FROM equipment_history h LEFT JOIN customers c ON c.id=h.customer_id ORDER BY h.id DESC LIMIT 50").fetchall()
    atr=''.join(f"<tr><td>{a}</td><td>{money(v)}</td></tr>" for a,v in aging); htr=''.join(f"<tr><td>{x['created_at']}</td><td>{x['kind']}</td><td>{x['equipment_id']}</td><td>{x['account_no'] or ''}</td><td>{x['action']}</td></tr>" for x in histories)
    return page(request,'Reports',f'''<h1>Reports</h1><div class="three"><div class="card"><h2>IMEI / Modem Reports</h2><div class="actions"><a class="btn secondary" target="_blank" href="/reports/modems.pdf?status=available">Available IMEIs</a><a class="btn secondary" target="_blank" href="/reports/modems.pdf?status=assigned">Assigned IMEIs</a><a class="btn secondary" target="_blank" href="/reports/modems.pdf?status=all">All IMEIs</a></div></div><div class="card"><h2>SIM / ICCID Reports</h2><div class="actions"><a class="btn secondary" target="_blank" href="/reports/sims.pdf?status=available">Available SIMs</a><a class="btn secondary" target="_blank" href="/reports/sims.pdf?status=assigned">Assigned SIMs</a><a class="btn secondary" target="_blank" href="/reports/sims.pdf?status=all">All SIMs</a></div></div><div class="card"><h2>Customer Reports</h2><div class="actions"><a class="btn secondary" target="_blank" href="/reports/customers.pdf?status=active">Active Customers</a><a class="btn secondary" target="_blank" href="/reports/customers.pdf?status=inactive">Inactive Customers</a><a class="btn secondary" target="_blank" href="/reports/customers.pdf?status=all">All Customers</a></div></div></div><div class="section row"><div class="card"><h2>A/R Aging</h2><table><tr><th>Bucket</th><th>Balance</th></tr>{atr}</table></div><div class="card"><h2>Equipment Assignment History</h2><table><tr><th>Date</th><th>Type</th><th>ID</th><th>Account</th><th>Action</th></tr>{htr}</table></div></div>''')

@app.get('/users',response_class=HTMLResponse)
def users(request:Request):
    require_admin(request)
    with conn() as c: rows=c.execute("SELECT * FROM users ORDER BY active DESC,name").fetchall()
    def expiry_text(x):
        if not x['active']: return 'Disabled'
        if x['role']=='admin': return 'Admin exempt'
        if x['must_change_password']: return 'Reset required'
        if not x['password_changed_at']: return 'Change required'
        try:
            changed=datetime.fromisoformat(str(x['password_changed_at']).replace('Z','+00:00')).replace(tzinfo=None)
            return (changed+timedelta(days=PASSWORD_MAX_AGE_DAYS)).strftime('%Y-%m-%d')
        except Exception: return 'Change required'
    trs=[]
    current_uid=request.session.get('user_id')
    for x in rows:
        if x['active']:
            reset=f"<form method='post' action='/users/{x['id']}/reset-password'><input type='password' name='temporary_password' minlength='8' required placeholder='Temporary password'><button class='btn secondary' type='submit'>Reset Password</button></form>"
            if x['id']==current_uid:
                lifecycle="<span class='muted'>Current signed-in account cannot be deactivated here.</span>"
            else:
                lifecycle=f"<form method='post' action='/users/{x['id']}/deactivate'><input name='reason' required placeholder='Reason, e.g. Employment terminated'><button class='btn danger' type='submit'>Deactivate Credentials</button></form>"
        else:
            reset="<span class='muted'>Password reset unavailable while disabled.</span>"
            reason=x['deactivation_reason'] or 'No reason recorded'
            lifecycle=f"<div class='muted'>Disabled {x['deactivated_at'] or ''}<br>{reason}</div><form method='post' action='/users/{x['id']}/reactivate'><button class='btn ok' type='submit'>Reactivate Credentials</button></form>"
        status_html='<span class="pill">Active</span>' if x['active'] else '<span class="pill bad">Disabled</span>'
        trs.append(f"<tr><td>{x['name']}</td><td>{x['email']}</td><td>{x['role']}</td><td>{status_html}</td><td>{expiry_text(x)}</td><td>{reset}<div style='margin-top:8px'>{lifecycle}</div></td></tr>")
    body=f'''<h1>Employee Accounts</h1><div class="card"><p class="muted">Administrators can reset employee passwords and immediately deactivate credentials when employment ends. Disabled employees cannot log in, and existing sessions are rejected on their next CRM request. Employee records remain in the system for audit history. New and reset accounts must change their temporary password; non-admin passwords expire every {PASSWORD_MAX_AGE_DAYS} days and the last {PASSWORD_HISTORY_COUNT} passwords cannot be reused.</p><table><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Password / Expiration</th><th>Admin Action</th></tr>{''.join(trs)}</table></div><div class="section card" style="max-width:650px"><h2>Add Employee</h2><form method="post"><label>Name</label><input name="name" required><label>Email</label><input type="email" name="email" required><label>Temporary Password</label><input type="password" name="password" required minlength="8"><label>Role</label><select name="new_role"><option value="staff">Staff</option><option value="admin">Administrator</option></select><p class="muted">The employee will be required to replace this temporary password at first login.</p><button class="btn">Create Employee</button></form></div>'''
    return page(request,'Employees',body)

@app.post('/users')
def user_add(request:Request,name:str=Form(...),email:str=Form(...),password:str=Form(...),new_role:str=Form('staff')):
    require_admin(request)
    if len(password)<8: raise HTTPException(400,'Temporary password must be at least 8 characters')
    try:
        with conn() as c:
            h=phash(password)
            cur=c.execute("INSERT INTO users(email,name,password_hash,role,must_change_password,password_changed_at,password_reset_at,password_reset_by) VALUES (?,?,?,?,1,NULL,CURRENT_TIMESTAMP,?)",(email.lower(),name,h,new_role if new_role in ('staff','admin') else 'staff',request.session.get('user_email','')))
            c.execute("INSERT INTO password_history(user_id,password_hash) VALUES (?,?)",(cur.lastrowid,h))
    except sqlite3.IntegrityError: raise HTTPException(409,'Email already exists')
    audit(request,'CREATE','user',cur.lastrowid,email+'; first-login password change required')
    return RedirectResponse('/users',303)

@app.post('/users/{uid}/reset-password')
def user_reset_password(request:Request,uid:int,temporary_password:str=Form(...)):
    require_admin(request)
    if len(temporary_password)<8: raise HTTPException(400,'Temporary password must be at least 8 characters')
    with conn() as c:
        u=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
        if not u: raise HTTPException(404,'Employee not found')
        if password_is_reused(c,uid,temporary_password,u['password_hash']):
            raise HTTPException(400,'Temporary password cannot match any of the employee last 3 passwords')
        old_hash=u['password_hash']; new_hash=phash(temporary_password)
        c.execute("INSERT INTO password_history(user_id,password_hash) VALUES (?,?)",(uid,old_hash))
        c.execute("UPDATE users SET password_hash=?,must_change_password=1,password_changed_at=NULL,password_reset_at=CURRENT_TIMESTAMP,password_reset_by=? WHERE id=?",(new_hash,request.session.get('user_email',''),uid))
        c.execute("DELETE FROM password_history WHERE user_id=? AND id NOT IN (SELECT id FROM password_history WHERE user_id=? ORDER BY id DESC LIMIT ?)",(uid,uid,max(PASSWORD_HISTORY_COUNT,3)))
    audit(request,'PASSWORD_RESET','user',uid,f'admin reset employee password for {u["email"]}; change required at next login')
    return RedirectResponse('/users',303)

@app.post('/users/{uid}/deactivate')
def user_deactivate(request:Request,uid:int,reason:str=Form(...)):
    require_admin(request)
    if uid==request.session.get('user_id'):
        raise HTTPException(400,'You cannot deactivate the account you are currently signed in with')
    reason=(reason or '').strip()
    if not reason: raise HTTPException(400,'A deactivation reason is required')
    with conn() as c:
        u=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
        if not u: raise HTTPException(404,'Employee not found')
        if not u['active']: return RedirectResponse('/users',303)
        if u['role']=='admin':
            active_admins=c.execute("SELECT COUNT(*) n FROM users WHERE role='admin' AND active=1").fetchone()['n']
            if active_admins<=1: raise HTTPException(400,'The last active administrator account cannot be deactivated')
        c.execute("UPDATE users SET active=0,deactivated_at=CURRENT_TIMESTAMP,deactivated_by=?,deactivation_reason=? WHERE id=?",(request.session.get('user_email',''),reason,uid))
    audit(request,'DEACTIVATE','user',uid,f'employee credentials disabled for {u["email"]}; reason: {reason}')
    return RedirectResponse('/users',303)

@app.post('/users/{uid}/reactivate')
def user_reactivate(request:Request,uid:int):
    require_admin(request)
    with conn() as c:
        u=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
        if not u: raise HTTPException(404,'Employee not found')
        c.execute("UPDATE users SET active=1,must_change_password=1,deactivated_at=NULL,deactivated_by=NULL,deactivation_reason=NULL WHERE id=?",(uid,))
    audit(request,'REACTIVATE','user',uid,f'employee credentials reactivated for {u["email"]}; password change required at next login')
    return RedirectResponse('/users',303)

@app.get('/audit',response_class=HTMLResponse)
def audit_log(request:Request):
    require_admin(request)
    with conn() as c: rows=c.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 250").fetchall()
    trs=''.join(f"<tr><td>{x['created_at']}</td><td>{x['user_email'] or ''}</td><td>{x['action']}</td><td>{x['entity']}</td><td>{x['entity_id'] or ''}</td><td>{x['details'] or ''}</td></tr>" for x in rows)
    return page(request,'Audit',f'''<h1>Audit Log</h1><table><tr><th>Date</th><th>User</th><th>Action</th><th>Entity</th><th>ID</th><th>Details</th></tr>{trs}</table>''')

# CUSTOMER PORTAL
@app.post('/verizon/callback/{token}')
async def verizon_callback(request:Request,token:str):
    if not VERIZON_CALLBACK_TOKEN or not hmac.compare_digest(token,VERIZON_CALLBACK_TOKEN): raise HTTPException(403)
    payload=await request.json(); reqid=payload.get('requestId') or payload.get('RequestId') or ''; status=payload.get('status') or payload.get('Status') or 'Received'; comment=payload.get('comment') or payload.get('Comment') or ''
    with conn() as c:
        action_row=c.execute("SELECT * FROM carrier_actions WHERE request_id=? ORDER BY id DESC LIMIT 1",(reqid,)).fetchone() if reqid else None
        if action_row:
            c.execute("UPDATE carrier_actions SET status=?,response=?,completed_at=? WHERE id=?",(status,json.dumps(payload)[:8000],datetime.now().isoformat(timespec='seconds'),action_row['id']))
            if str(status).lower()=='success':
                if action_row['action']=='suspend': c.execute("UPDATE customers SET service_status='Suspended - Nonpayment',last_suspend_at=? WHERE id=?",(datetime.now().isoformat(timespec='seconds'),action_row['customer_id']))
                elif action_row['action']=='restore': c.execute("UPDATE customers SET service_status='Active',last_restore_at=? WHERE id=?",(datetime.now().isoformat(timespec='seconds'),action_row['customer_id']))
        else:
            return JSONResponse({'received':True,'matched':False})
    return {'received':True,'matched':True}

@app.get('/carrier',response_class=HTMLResponse)
def carrier_center(request:Request):
    require_staff(request)
    with conn() as c:
        rows=c.execute("""SELECT ca.*,c.account_no,c.first_name,c.last_name,s.iccid FROM carrier_actions ca JOIN customers c ON c.id=ca.customer_id LEFT JOIN sims s ON s.id=ca.sim_id ORDER BY ca.id DESC LIMIT 100""").fetchall()
        suspended=c.execute("SELECT id,account_no,first_name,last_name,service_status FROM customers WHERE service_status!='Active' ORDER BY last_name").fetchall()
        vsims=c.execute("""SELECT s.id,s.iccid,s.mdn,s.status,c.id customer_id,c.account_no,c.first_name,c.last_name FROM sims s LEFT JOIN customers c ON c.id=s.customer_id WHERE (lower(trim(COALESCE(s.carrier,''))) IN ('vzw','verizon','verizon wireless') OR lower(COALESCE(s.carrier,'')) LIKE '%verizon%') AND TRIM(COALESCE(s.iccid,''))<>'' ORDER BY COALESCE(c.last_name,''),s.id DESC""").fetchall()
    trs=''.join(f"<tr><td>{x['created_at']}</td><td><a href='/customers/{x['customer_id']}'>{x['account_no']}</a></td><td>{x['action']}</td><td>{x['iccid'] or ''}</td><td>{x['status']}</td><td>{x['request_id'] or ''}</td></tr>" for x in rows) or '<tr><td colspan=6>No carrier actions yet.</td></tr>'
    sus=''.join(f"<tr><td>{x['account_no']}</td><td>{x['first_name']} {x['last_name']}</td><td>{x['service_status']}</td><td><a class='btn ok' href='/carrier/{x['id']}/restore'>Restore</a></td></tr>" for x in suspended) or '<tr><td colspan=4>No suspended accounts.</td></tr>'
    mode='LIVE' if VERIZON_ENABLED and not VERIZON_DRY_RUN else 'DRY RUN / SAFE MODE'
    test_result=request.session.pop('verizon_test_result',None)
    test_html=''
    if test_result:
        cls='notice' if test_result.get('ok') else 'notice danger'
        test_html=f"<div class='{cls}'><b>Verizon Connection Test:</b> {html.escape(test_result.get('message',''))}</div>"
    diag_result=request.session.pop('verizon_diag_result',None)
    diag_html=''
    if diag_result:
        cls='notice' if diag_result.get('ok') else 'notice danger'
        diag_html=f"<div class='{cls}'><b>ThingSpace Inventory Diagnostic:</b> {html.escape(diag_result.get('message',''))}</div>"
    device_result=request.session.pop('verizon_device_result',None)
    device_html=''
    if device_result:
        cls='notice' if device_result.get('ok') else 'notice danger'
        device_html=f"<div class='{cls}'><b>Verizon Device Check:</b> {html.escape(device_result.get('message',''))}</div>"
    vopts=''.join(f"<option value='{x['id']}'>{html.escape((x['account_no'] or 'Unassigned')+' — '+x['iccid']+' — '+((x['first_name'] or '')+' '+(x['last_name'] or '')).strip())}</option>" for x in vsims)
    device_form=(f"<form method='post' action='/carrier/check-device'><label>Assigned Verizon SIM / ICCID</label><select name='sim_id' required><option value=''>Select a Verizon SIM</option>{vopts}</select><button class='btn secondary' type='submit'>Check Verizon Device</button></form>" if vopts else "<p class='muted'>No Verizon SIM/ICCID is currently available in CRM inventory. Add a Verizon SIM or assign one to a customer before running a device check.</p>")
    return page(request,'Carrier Control',f"""<h1>Carrier Control Center</h1>{test_html}{diag_html}{device_html}<div class='notice'><b>Carrier account identity:</b> {VERIZON_ACCOUNT_DISPLAY_NAME}<br><b>Verizon automation:</b> {mode}. Nonpayment suspension threshold: {SUSPEND_AFTER_DAYS} days after due date. Reconnect fee: {money(RECONNECT_FEE)}.</div><div class='card'><div class='actions'><form method='post' action='/carrier/test-verizon' style='display:inline'><button class='btn secondary' type='submit'>Test Verizon Connection</button></form> <a class='btn' href='/carrier/run-suspensions'>Run Past-Due Suspension Check</a></div><p class='muted'>The connection test validates ThingSpace OAuth and the UWS session only. It does not activate, suspend, restore, or modify any Verizon device. Past-due automation skips customers without an assigned Verizon SIM/ICCID.</p></div><div class='section card'><h2>Read-Only Verizon Device Verification</h2><p class='muted'>Looks up the selected ICCID with Verizon and displays provisioning information. This check is read-only and does not activate, suspend, restore, or modify the device.</p>{device_form}</div><div class='section card'><h2>ThingSpace Inventory Sync</h2><p class='muted'>Imports IMEIs and SIM ICCIDs from the configured Verizon account. Existing CRM records and customer equipment assignments are preserved; only missing inventory is created.</p><div class='actions'><form method='post' action='/carrier/diagnose-inventory' style='display:inline'><button class='btn secondary' type='submit'>Diagnose ThingSpace Inventory</button></form> <form method='post' action='/carrier/sync-inventory' style='display:inline' onsubmit="return confirm('Import and sync Verizon ThingSpace device inventory into the CRM? Existing customer assignments will be preserved.');"><button class='btn' type='submit'>Sync Inventory from ThingSpace</button></form></div><p class='muted'>The diagnostic is read-only. It compares all inventory visible to the UWS API user with inventory returned for the configured billing account and does not display device identifiers or credentials.</p></div><div class='section card'><h2>Suspended Accounts</h2><table><tr><th>Account</th><th>Customer</th><th>Status</th><th>Action</th></tr>{sus}</table></div><div class='section card'><h2>Carrier Action History</h2><table><tr><th>Date</th><th>Account</th><th>Action</th><th>ICCID</th><th>Status</th><th>Request ID</th></tr>{trs}</table></div>""")

@app.post('/carrier/diagnose-inventory')
def carrier_diagnose_inventory(request:Request):
    require_admin(request)
    try:
        r=verizon_inventory_diagnostic()
        uws_accounts=', '.join(r['uws_accounts']) if r['uws_accounts'] else 'none returned'
        acct_accounts=', '.join(r['account_accounts']) if r['account_accounts'] else 'none returned'
        more_note=(' UWS result indicates more data is available.' if r['uws_has_more'] else '') + (' Configured-account result indicates more data is available.' if r['account_has_more'] else '')
        msg=(f"UWS session connected. All accessible devices: {r['uws_records']} (IMEIs: {r['uws_imeis']}, ICCIDs: {r['uws_iccids']}); "
             f"account(s) returned: {uws_accounts}. Configured account: {r['configured_account']}; devices in configured account: {r['account_records']} "
             f"(IMEIs: {r['account_imeis']}, ICCIDs: {r['account_iccids']}); account(s) returned for configured-account query: {acct_accounts}.{more_note}")
        request.session['verizon_diag_result']={'ok':True,'message':msg}
        audit(request,'TEST','verizon_inventory_diagnostic',None,json.dumps({k:v for k,v in r.items() if k not in ()},sort_keys=True))
    except Exception as e:
        safe=str(e)
        if 'missing render environment variable' not in safe.lower() and 'http ' not in safe.lower():
            safe='ThingSpace inventory diagnostic could not be completed. Review the ThingSpace/UWS connection and try again.'
        request.session['verizon_diag_result']={'ok':False,'message':safe}
        audit(request,'TEST_FAILED','verizon_inventory_diagnostic',None,safe)
    return RedirectResponse('/carrier',303)

@app.post('/carrier/sync-inventory')
def carrier_sync_inventory(request:Request):
    require_admin(request)
    try:
        result=verizon_import_inventory()
        request.session['verizon_test_result']={'ok':True,'message':f"ThingSpace returned {result['devices']} device record(s) across {result['pages']} page(s): {result['imei_found']} IMEI(s), {result['iccid_found']} ICCID(s). Imported {result['new_modems']} new IMEI(s) and {result['new_sims']} new ICCID(s); preserved {result['existing_modems']} existing IMEI(s) and {result['existing_sims']} existing ICCID(s); skipped {result['skipped']} record(s)."}
        audit(request,'SYNC','verizon_inventory',None,json.dumps(result,sort_keys=True))
    except Exception as e:
        safe=str(e)
        if 'missing render environment variable' not in safe.lower(): safe='Verizon inventory sync could not be completed. Review the ThingSpace/UWS connection and try again.'
        request.session['verizon_test_result']={'ok':False,'message':safe}
        audit(request,'SYNC_FAILED','verizon_inventory',None,safe)
    return RedirectResponse('/carrier',303)

@app.post('/carrier/test-verizon')
def carrier_test_verizon(request:Request):
    require_admin(request)
    try:
        # Force a fresh UWS session so the test validates both credential layers.
        _verizon_cache['access_token']=None; _verizon_cache['access_expires']=0
        _verizon_cache['session_token']=None; _verizon_cache['session_time']=0
        verizon_access_token()
        verizon_session_token(force=True)
        request.session['verizon_test_result']={'ok':True,'message':'Connected successfully. ThingSpace OAuth and UWS authentication both succeeded. No device action was sent.'}
        audit(request,'TEST','verizon_connection',None,'ThingSpace OAuth and UWS authentication succeeded; no device action sent')
        print('Verizon connection test: OAuth and UWS authentication succeeded')
    except urllib.error.HTTPError as e:
        # Do not expose response bodies or credentials in the UI/logs.
        msg=f'Authentication failed with Verizon HTTP {e.code}. No device action was sent. Do not repeatedly retry if this is a credential error.'
        request.session['verizon_test_result']={'ok':False,'message':msg}
        audit(request,'ERROR','verizon_connection',None,f'HTTP {e.code} during Verizon connection test')
        print(f'Verizon connection test failed: HTTP {e.code}')
    except Exception as e:
        safe=str(e)
        # Configuration errors are safe/useful; avoid reflecting unexpected provider payloads.
        if 'missing render environment variable' not in safe.lower() and 'not configured' not in safe.lower(): safe='Verizon authentication could not be completed. Review the configured ThingSpace/UWS credentials and provider settings.'
        request.session['verizon_test_result']={'ok':False,'message':safe+' No device action was sent.'}
        audit(request,'ERROR','verizon_connection',None,safe[:1000])
        print('Verizon connection test failed:',safe)
    return RedirectResponse('/carrier',303)

@app.post('/carrier/check-device')
def carrier_check_device(request:Request,sim_id:int=Form(...)):
    require_admin(request)
    with conn() as c:
        sim=c.execute("SELECT s.*,c.account_no,c.first_name,c.last_name FROM sims s LEFT JOIN customers c ON c.id=s.customer_id WHERE s.id=?",(sim_id,)).fetchone()
    if not sim or not is_verizon_carrier(sim['carrier']) or not str(sim['iccid'] or '').strip():
        request.session['verizon_device_result']={'ok':False,'message':'Select a valid Verizon SIM/ICCID from CRM inventory. No device action was sent.'}
        return RedirectResponse('/carrier',303)
    try:
        info=verizon_lookup_device(sim['iccid'])
        if not info.get('found'):
            msg=f"ICCID ending {str(sim['iccid'])[-4:]} was not found in the Verizon account. No device action was sent."
            ok=False
        else:
            connected='Yes' if info.get('connected') is True else ('No' if info.get('connected') is False else 'Unknown')
            parts=[f"ICCID ending {str(info.get('iccid') or sim['iccid'])[-4:]}",f"State: {info.get('state') or 'Unknown'}",f"Connected: {connected}"]
            if info.get('service_plan'): parts.append(f"Service plan: {info['service_plan']}")
            if info.get('mdn'): parts.append(f"MDN ending {str(info['mdn'])[-4:]}")
            if info.get('imei'): parts.append(f"IMEI ending {str(info['imei'])[-4:]}")
            if info.get('last_connection_date'): parts.append(f"Last connection: {info['last_connection_date']}")
            msg='; '.join(parts)+'. Read-only lookup succeeded; no device action was sent.'
            ok=True
        request.session['verizon_device_result']={'ok':ok,'message':msg}
        audit(request,'TEST','verizon_device_lookup',sim_id,('found' if ok else 'not_found')+'; ICCID ending '+str(sim['iccid'])[-4:])
    except urllib.error.HTTPError as e:
        request.session['verizon_device_result']={'ok':False,'message':f'Verizon device lookup failed with HTTP {e.code}. No device action was sent.'}
        audit(request,'ERROR','verizon_device_lookup',sim_id,f'HTTP {e.code}')
    except Exception as e:
        request.session['verizon_device_result']={'ok':False,'message':'Verizon device lookup could not be completed. No device action was sent.'}
        audit(request,'ERROR','verizon_device_lookup',sim_id,str(e)[:1000])
    return RedirectResponse('/carrier',303)

@app.get('/carrier/run-suspensions')
def carrier_run(request:Request):
    require_admin(request); ok,fail=run_nonpayment_suspensions(); audit(request,'RUN','nonpayment_suspensions',None,f'ok={len(ok)} fail={len(fail)}'); return RedirectResponse('/carrier',303)

@app.get('/carrier/{cid}/suspend')
def carrier_suspend(request:Request,cid:int):
    require_admin(request)
    try: verizon_device_action(cid,'suspend','Manual staff action'); audit(request,'SUSPEND','customer',cid,'manual')
    except Exception as e: audit(request,'ERROR','carrier_suspend',cid,str(e))
    return RedirectResponse('/carrier',303)

@app.get('/carrier/{cid}/restore')
def carrier_restore(request:Request,cid:int):
    require_admin(request)
    try:
        verizon_device_action(cid,'restore','Manual staff action')
        with conn() as c: aid=c.execute("SELECT id FROM carrier_actions WHERE customer_id=? AND action='restore' ORDER BY id DESC LIMIT 1",(cid,)).fetchone()['id']
        queue_reconnect_fee(cid,aid); audit(request,'RESTORE','customer',cid,'manual; reconnect fee queued')
    except Exception as e: audit(request,'ERROR','carrier_restore',cid,str(e))
    return RedirectResponse('/carrier',303)


# ---------------- Service Agreement Automation (v10.3) ----------------
def _docx_set_cell(cell, value):
    cell.text = str(value or '')
    for p in cell.paragraphs:
        for run in p.runs:
            run.font.name = 'Arial'
            run.font.size = None

def generate_customer_service_agreement(cid, woo_order_id=None, signer_name='', signature_text='', accepted_at='', autopay='No'):
    if not SERVICE_AGREEMENT_TEMPLATE.exists():
        raise RuntimeError('Service agreement template is missing from the CRM deployment.')
    with conn() as c:
        cust=c.execute('SELECT * FROM customers WHERE id=?',(cid,)).fetchone()
        if not cust: raise RuntimeError('Customer not found for service agreement generation.')
        plan=c.execute('SELECT p.* FROM subscriptions s JOIN plans p ON p.id=s.plan_id WHERE s.customer_id=?',(cid,)).fetchone()
        modem=c.execute('SELECT * FROM modems WHERE customer_id=? ORDER BY id DESC LIMIT 1',(cid,)).fetchone()
        sim=c.execute('SELECT * FROM sims WHERE customer_id=? ORDER BY id DESC LIMIT 1',(cid,)).fetchone()
    doc=Document(str(SERVICE_AGREEMENT_TEMPLATE))
    full_name=(' '.join(x for x in [cust['first_name'],cust['last_name']] if x)).strip()
    customer_name=(cust['company'] or full_name) if (cust['customer_type'] or '')=='Business' else full_name
    service=', '.join(x for x in [cust['service_address'], ' '.join(x for x in [cust['city'],cust['state'],cust['zip']] if x)] if x)
    billing=cust['billing_address'] or service
    start=cust['contract_start'] or date.today().isoformat()
    try: end=(date.fromisoformat(start).replace(year=date.fromisoformat(start).year+3)-timedelta(days=1)).isoformat()
    except Exception: end=''
    monthly=(float(plan['monthly_price'] or 0)+float(plan['modem_lease'] or 0)) if plan else 0
    t=doc.tables[1]
    values={
      (0,1):customer_name,(0,3):cust['account_no'],(1,1):service,(1,3):billing,
      (2,1):cust['phone'],(2,3):cust['email'],(3,1):start,(3,3):end,
      (4,1):(plan['name'] if plan else ''),(4,3):f'$ {monthly:,.2f}',(5,1):'$ 0.00',(5,3):f'$ {float(plan["modem_lease"] or 0):,.2f}' if plan else '$ 0.00',
      (6,1):(modem['model'] if modem else 'To be assigned'),(6,3):(modem['imei'] if modem else 'To be assigned'),
      (7,1):(sim['iccid'] if sim else 'To be assigned'),(7,3):('Yes' if str(autopay).lower() in ('1','yes','true','on') else 'No'),
      (8,1):'Online / WooCommerce' if woo_order_id else '',(8,3):(f'WC-{woo_order_id}' if woo_order_id else '')}
    for pos,val in values.items(): _docx_set_cell(t.cell(*pos),val)
    sig=doc.tables[5]
    _docx_set_cell(sig.cell(0,1),customer_name)
    _docx_set_cell(sig.cell(1,1),signer_name or full_name)
    _docx_set_cell(sig.cell(2,1),signature_text or signer_name or full_name)
    _docx_set_cell(sig.cell(3,1),(accepted_at or start)[:10])
    _docx_set_cell(sig.cell(4,1),'Entire Wireless - Online Order System')
    _docx_set_cell(sig.cell(5,1),f'Electronically accepted {accepted_at or start}')
    customer_dir=DOCUMENTS / str(cid); customer_dir.mkdir(parents=True,exist_ok=True)
    stored=f'service_order_customer_information_{woo_order_id or datetime.now().strftime("%Y%m%d%H%M%S")}.docx'
    out=customer_dir/stored; doc.save(str(out))
    original='Service Order-Customer Information.docx'
    with conn() as c:
        old=c.execute("SELECT id FROM customer_documents WHERE customer_id=? AND document_type='Service Order/Customer Information' AND notes LIKE ? ORDER BY id DESC LIMIT 1",(cid,f'%WooCommerce order #{woo_order_id}%')).fetchone() if woo_order_id else None
        if old: return old['id']
        cur=c.execute("INSERT INTO customer_documents(customer_id,original_name,stored_name,document_type,notes,content_type,size_bytes,uploaded_by) VALUES (?,?,?,?,?,?,?,?)",(cid,original,stored,'Service Order/Customer Information',f'Auto-generated from WooCommerce order #{woo_order_id}. Customer electronically acknowledged and signed during checkout.' if woo_order_id else 'Auto-generated from CRM customer information.','application/vnd.openxmlformats-officedocument.wordprocessingml.document',out.stat().st_size,'woocommerce' if woo_order_id else 'system'))
        return cur.lastrowid

def archive_customer_aup(cid, woo_order_id, accepted_at='', viewed_at='', version='Entire Wireless Acceptable Use Policy - Effective 09/15/2026', pdf_sha256=''):
    """Copy the exact accepted AUP PDF into the customer's CRM Document Center."""
    source=BASE_DIR / 'Entire_Wireless_Acceptable_Use_Policy_09-15-2026.pdf'
    if not source.exists():
        raise RuntimeError('Bundled Acceptable Use Policy PDF is missing from the CRM package.')
    actual_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    if pdf_sha256 and str(pdf_sha256).strip().lower()!=actual_hash.lower():
        raise RuntimeError('AUP PDF hash from WooCommerce does not match the CRM bundled AUP.')
    customer_dir=DOCUMENTS / str(cid); customer_dir.mkdir(parents=True,exist_ok=True)
    stored=f'acceptable_use_policy_{woo_order_id}.pdf'
    out=customer_dir/stored
    if not out.exists(): shutil.copy2(source,out)
    original='Entire Wireless Acceptable Use Policy - 09-15-2026.pdf'
    notes=f'Accepted electronically during WooCommerce order #{woo_order_id}. Accepted: {accepted_at or "recorded at checkout"}; Viewed: {viewed_at or "recorded at checkout"}; Version: {version}; SHA-256: {actual_hash}'
    with conn() as c:
        old=c.execute("SELECT id FROM customer_documents WHERE customer_id=? AND document_type='Acceptable Use Policy' AND notes LIKE ? ORDER BY id DESC LIMIT 1",(cid,f'%WooCommerce order #{woo_order_id}%')).fetchone()
        if old: return old['id']
        cur=c.execute("INSERT INTO customer_documents(customer_id,original_name,stored_name,document_type,notes,content_type,size_bytes,uploaded_by) VALUES (?,?,?,?,?,?,?,?)",(cid,original,stored,'Acceptable Use Policy',notes,'application/pdf',out.stat().st_size,'woocommerce'))
        return cur.lastrowid


# v10.11 canonical current 5G plan catalog
EW_CURRENT_PLANS={
 "59142":{"name":"5G Internet 100 Mbps","customer_type":"Residential","price":85.00,"speed_mbps":100,"unlimited":True},
 "59145":{"name":"5G Internet 200 Mbps","customer_type":"Residential","price":105.00,"speed_mbps":200,"unlimited":True},
 "59143":{"name":"5G Internet 100 Mbps","customer_type":"Business","price":95.00,"speed_mbps":100,"unlimited":True},
 "59146":{"name":"5G Internet 200 Mbps","customer_type":"Business","price":115.00,"speed_mbps":200,"unlimited":True}
}
EW_PLAN_DISCLOSURE='Availability depends on the service address, approved router, and network capacity. This is a data plan. Voice, text, and multimedia messaging are not included and are prohibited. Emergency or service calls to 911 may be supported where available. Unauthorized use of those services can lead to additional charges or termination under applicable agreements. Service is limited to eligible 5G C-Band addresses and compatible 5G C-Band routers. Domestic and international roaming are unavailable. The monthly fee may be prorated when a plan changes during a billing cycle. The stated speed is a maximum, and congestion can lower it; upload speeds may be lower than download speeds. Prices do not include applicable taxes or other fees.'

# ---------------- WooCommerce Storefront Integration (v10.3) ----------------
def _woo_meta(order, key, default=''):
    for item in (order.get('meta_data') or []):
        if str(item.get('key','')) == key:
            return item.get('value', default)
    return default

def ew_v1011_order_tax_fees(order):
    raw=_woo_meta(order,'ew_sales_tax_other_fees','')
    try:
        if str(raw).strip(): return round(float(raw),2)
    except Exception: pass
    total=0.0
    for fee in (order.get('fee_lines') or []):
        if str(fee.get('name') or '').strip().lower()=='sales tax & other fees':
            try: total += float(fee.get('total') or 0)
            except Exception: pass
    return round(total,2)


def _woo_order_type_and_plan(order):
    requested=str(_woo_meta(order,'ew_customer_type','')).strip().title()
    skus=[str(x.get('sku') or '').upper() for x in (order.get('line_items') or [])]
    names=[str(x.get('name') or '').lower() for x in (order.get('line_items') or [])]
    if requested=='Tablet' or 'EW-TABLET' in skus or any('tablet' in n or 'ipad' in n for n in names):
        raise RuntimeError('Tablet/iPad service has been retired and is no longer supported by the CRM.')
    if requested not in ('Residential','Business'):
        requested='Business' if ('EW-BUSINESS' in skus or any('business' in n for n in names)) else 'Residential'
    return requested,('Business Internet' if requested=='Business' else 'Unlimited Internet')

def _woo_paid(order):
    return str(order.get('status') or '').lower() in ('processing','completed') or bool(order.get('date_paid'))

def _woo_basic_request(path):
    if not (WOOCOMMERCE_CONSUMER_KEY and WOOCOMMERCE_CONSUMER_SECRET):
        raise RuntimeError('WooCommerce REST API credentials are not configured.')
    url=WOOCOMMERCE_STORE_URL + path
    req=urllib.request.Request(url,headers={'User-Agent':f'{APP_NAME} WooCommerce Sync'})
    token=base64.b64encode(f'{WOOCOMMERCE_CONSUMER_KEY}:{WOOCOMMERCE_CONSUMER_SECRET}'.encode()).decode()
    req.add_header('Authorization','Basic '+token)
    with urllib.request.urlopen(req,timeout=45) as resp:
        return json.loads(resp.read().decode())

ONBOARDING_STAGES=['Order Received','Payment Confirmed','Agreement Pending','Agreement Signed','Equipment Assignment','Provisioning','Ready for Service','Active']

def ensure_onboarding(customer_id,woo_order_id=None,stage='Order Received'):
    now=datetime.now().isoformat(timespec='seconds')
    stage=stage if stage in ONBOARDING_STAGES else 'Order Received'
    cols={'Order Received':'order_received_at','Payment Confirmed':'payment_confirmed_at','Agreement Signed':'agreement_signed_at','Equipment Assignment':'equipment_assigned_at','Provisioning':'provisioning_started_at','Ready for Service':'ready_for_service_at','Active':'activated_at'}
    with conn() as c:
        row=c.execute('SELECT * FROM customer_onboarding WHERE customer_id=?',(customer_id,)).fetchone()
        if not row:
            c.execute('INSERT INTO customer_onboarding(customer_id,woo_order_id,stage,order_received_at,updated_at) VALUES (?,?,?,?,?)',(customer_id,woo_order_id,stage,now,now))
        elif woo_order_id and not row['woo_order_id']:
            c.execute('UPDATE customer_onboarding SET woo_order_id=?,updated_at=? WHERE customer_id=?',(woo_order_id,now,customer_id))
        if stage in cols:
            c.execute(f"UPDATE customer_onboarding SET {cols[stage]}=COALESCE({cols[stage]},?),updated_at=? WHERE customer_id=?",(now,now,customer_id))

def onboarding_progress_html(ob,customer_view=False):
    current=(ob['stage'] if ob else 'Order Received')
    try: idx=ONBOARDING_STAGES.index(current)
    except ValueError: idx=0
    parts=[]
    for i,st in enumerate(ONBOARDING_STAGES):
        state='✓' if i<idx else ('●' if i==idx else '○')
        parts.append(f"<div style='padding:10px 12px;border-left:4px solid {'#2b9f69' if i<idx else '#2596be' if i==idx else '#d8e2e6'};background:{'#f2fbf6' if i<idx else '#eef8fc' if i==idx else '#fafcfd'};margin:5px 0;border-radius:6px'><b>{state} {html.escape(st)}</b>{'<div class=muted>Current step</div>' if i==idx else ''}</div>")
    return ''.join(parts)

def _woo_import_order(order):
    oid=int(order.get('id') or 0)
    if not oid: raise RuntimeError('WooCommerce order ID is missing.')
    customer_type,plan_name=_woo_order_type_and_plan(order)
    status=str(order.get('status') or '')
    total=float(order.get('total') or 0)
    payment_method=str(order.get('payment_method_title') or order.get('payment_method') or 'WooCommerce')
    transaction_id=str(order.get('transaction_id') or '')
    signer_name=str(_woo_meta(order,'ew_authorized_signer','')).strip()
    signature_text=str(_woo_meta(order,'ew_customer_signature','')).strip()
    agreement_accepted=str(_woo_meta(order,'ew_agreement_accepted','')).strip()
    agreement_accepted_at=str(_woo_meta(order,'ew_agreement_accepted_at','') or order.get('date_paid') or order.get('date_created') or '').strip()
    aup_viewed=str(_woo_meta(order,'ew_aup_viewed','')).strip()
    aup_viewed_at=str(_woo_meta(order,'ew_aup_viewed_at','')).strip()
    aup_accepted=str(_woo_meta(order,'ew_aup_accepted','')).strip()
    aup_accepted_at=str(_woo_meta(order,'ew_aup_accepted_at','') or order.get('date_paid') or order.get('date_created') or '').strip()
    aup_version=str(_woo_meta(order,'ew_aup_version','Entire Wireless Acceptable Use Policy - Effective 09/15/2026')).strip()
    aup_pdf_sha256=str(_woo_meta(order,'ew_aup_pdf_sha256','')).strip()
    autopay=str(_woo_meta(order,'ew_autopay','No')).strip()
    tablet_imei=re.sub(r'\D+','',str(_woo_meta(order,'ew_tablet_imei','')).strip())
    tablet_sim_type=str(_woo_meta(order,'ew_tablet_sim_type','')).strip().lower()
    is_tablet=False
    if aup_accepted.lower() not in ('yes','1','true','accepted'):
        raise RuntimeError('WooCommerce order is missing required Acceptable Use Policy acceptance.')
    if aup_viewed.lower() not in ('yes','1','true','viewed'):
        raise RuntimeError('WooCommerce order is missing required Acceptable Use Policy review confirmation.')
    if is_tablet:
        if not re.fullmatch(r'[0-9]{15}',tablet_imei): raise RuntimeError('Tablet/iPad order is missing a valid 15-digit IMEI.')
        if tablet_sim_type not in ('physical','esim'): raise RuntimeError('Tablet/iPad order is missing a valid SIM option.')

    payload=json.dumps(order,separators=(',',':'))[:1000000]
    with conn() as c:
        existing=c.execute('SELECT * FROM woocommerce_orders WHERE woo_order_id=?',(oid,)).fetchone()
        if existing and existing['payment_id']:
            c.execute("UPDATE woocommerce_orders SET order_status=?,order_total=?,transaction_id=?,payload_json=?,updated_at=CURRENT_TIMESTAMP WHERE woo_order_id=?",(status,total,transaction_id,payload,oid))
            return dict(existing) | {'duplicate':True}
        c.execute("INSERT INTO woocommerce_orders(woo_order_id,customer_type,plan_name,order_status,payment_method,order_total,transaction_id,sync_status,payload_json) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(woo_order_id) DO UPDATE SET customer_type=excluded.customer_type,plan_name=excluded.plan_name,order_status=excluded.order_status,payment_method=excluded.payment_method,order_total=excluded.order_total,transaction_id=excluded.transaction_id,payload_json=excluded.payload_json,updated_at=CURRENT_TIMESTAMP",(oid,customer_type,plan_name,status,payment_method,total,transaction_id,'Awaiting Payment' if not _woo_paid(order) else 'Processing',payload))
    if not _woo_paid(order): return {'woo_order_id':oid,'status':'Awaiting Payment'}

    billing=order.get('billing') or {}; shipping=order.get('shipping') or {}
    first=str(billing.get('first_name') or shipping.get('first_name') or 'Online').strip()
    last=str(billing.get('last_name') or shipping.get('last_name') or 'Customer').strip()
    company=str(billing.get('company') or shipping.get('company') or '').strip()
    email=str(billing.get('email') or '').strip().lower()
    phone=str(billing.get('phone') or '').strip()
    service_address=str(_woo_meta(order,'ew_service_address','') or shipping.get('address_1') or billing.get('address_1') or '').strip()
    service_address2=str(_woo_meta(order,'ew_service_address_2','') or shipping.get('address_2') or billing.get('address_2') or '').strip()
    if service_address2: service_address=(service_address+' '+service_address2).strip()
    city=str(_woo_meta(order,'ew_service_city','') or shipping.get('city') or billing.get('city') or '').strip()
    state=str(_woo_meta(order,'ew_service_state','') or shipping.get('state') or billing.get('state') or '').strip()
    zipcode=str(_woo_meta(order,'ew_service_zip','') or shipping.get('postcode') or billing.get('postcode') or '').strip()
    billing_address=' '.join(x for x in [str(billing.get('address_1') or '').strip(),str(billing.get('address_2') or '').strip()] if x)
    order_date=str(order.get('date_paid') or order.get('date_created') or date.today().isoformat())[:10]
    try: contract_start=date.fromisoformat(order_date).isoformat()
    except Exception: contract_start=date.today().isoformat()

    with conn() as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT * FROM woocommerce_orders WHERE woo_order_id=?',(oid,)).fetchone()
        cid=int(row['customer_id']) if row and row['customer_id'] else 0
        if not cid and email:
            found=c.execute("SELECT id FROM customers WHERE lower(email)=lower(?) ORDER BY id DESC LIMIT 1",(email,)).fetchone()
            cid=int(found['id']) if found else 0
        if not cid:
            account_no=generate_account_number(c,customer_type)
            cur=c.execute("INSERT INTO customers(account_no,first_name,last_name,customer_type,company,email,phone,service_address,billing_address,city,state,zip,billing_day,contract_start,contract_months,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(account_no,first,last,account_customer_type,company,email,phone,service_address,billing_address,city,state,zipcode,min(date.today().day,28),contract_start,36,f'Created automatically from WooCommerce order #{oid}'))
            cid=cur.lastrowid
        else:
            c.execute("UPDATE customers SET customer_type=CASE WHEN ?='Tablet' THEN customer_type ELSE ? END,company=CASE WHEN ?!='' THEN ? ELSE company END,phone=CASE WHEN ?!='' THEN ? ELSE phone END,service_address=CASE WHEN ?!='' THEN ? ELSE service_address END,billing_address=CASE WHEN ?!='' THEN ? ELSE billing_address END,city=CASE WHEN ?!='' THEN ? ELSE city END,state=CASE WHEN ?!='' THEN ? ELSE state END,zip=CASE WHEN ?!='' THEN ? ELSE zip END WHERE id=?",(customer_type,customer_type,company,company,phone,phone,service_address,service_address,billing_address,billing_address,city,city,state,state,zipcode,zipcode,cid))
        plan=c.execute('SELECT * FROM plans WHERE name=? AND active=1',(plan_name,)).fetchone()
        if not plan: raise RuntimeError(f'CRM service plan not found: {plan_name}')
        if is_tablet:
            # Preserve any existing Residential/Business subscription. Tablet service is an additional service record.
            c.execute("""INSERT INTO tablet_services(customer_id,plan_id,woo_order_id,imei,sim_type,monthly_price,activation_fee,physical_sim_fee,start_date,contract_months,status)
                VALUES (?,?,?,?,?,?,?,?,?,36,'Active')
                ON CONFLICT(woo_order_id) DO UPDATE SET customer_id=excluded.customer_id,plan_id=excluded.plan_id,imei=excluded.imei,sim_type=excluded.sim_type,status='Active'""",
                (cid,plan['id'],oid,tablet_imei,tablet_sim_type,45.0,15.0,5.0 if tablet_sim_type=='physical' else 0.0,contract_start))
            device=c.execute('SELECT * FROM modems WHERE imei=?',(tablet_imei,)).fetchone()
            if device and device['customer_id'] not in (None,cid):
                raise RuntimeError('Tablet/iPad IMEI is already assigned to another CRM customer.')
            if device:
                c.execute("UPDATE modems SET customer_id=?,status='Assigned',model=CASE WHEN COALESCE(model,'')='' THEN 'Tablet/iPad (Customer-Owned)' ELSE model END,notes=? WHERE id=?",
                          (cid,f'Tablet/iPad plan from WooCommerce order #{oid}; SIM={tablet_sim_type}',device['id']))
                device_id=device['id']
            else:
                cur=c.execute("INSERT INTO modems(imei,manufacturer,model,status,customer_id,acquired_date,notes) VALUES (?,?,?,'Assigned',?,?,?)",
                              (tablet_imei,'','Tablet/iPad (Customer-Owned)',cid,contract_start,f'Tablet/iPad plan from WooCommerce order #{oid}; SIM={tablet_sim_type}'))
                device_id=cur.lastrowid
            c.execute("INSERT INTO equipment_history(kind,equipment_id,customer_id,action,details) VALUES ('tablet',?,?,?,?)",
                      (device_id,cid,'ASSIGNED',f'Customer-owned Tablet/iPad IMEI {tablet_imei}; SIM={tablet_sim_type}; WooCommerce order #{oid}'))
        else:
            sub=c.execute('SELECT id FROM subscriptions WHERE customer_id=?',(cid,)).fetchone()
            if sub: c.execute("UPDATE subscriptions SET plan_id=?,start_date=?,status='Active' WHERE customer_id=?",(plan['id'],contract_start,cid))
            else: c.execute("INSERT INTO subscriptions(customer_id,plan_id,start_date,status) VALUES (?,?,?,'Active')",(cid,plan['id'],contract_start))
        c.execute("UPDATE woocommerce_orders SET customer_id=?,sync_status='Customer Created',sync_error=NULL,updated_at=CURRENT_TIMESTAMP WHERE woo_order_id=?",(cid,oid))

    ensure_onboarding(cid,oid,'Payment Confirmed')

    # Build the CRM invoice from the CRM plan, not from website pricing labels.
    with conn() as c:
        row=c.execute('SELECT invoice_id FROM woocommerce_orders WHERE woo_order_id=?',(oid,)).fetchone()
        iid=int(row['invoice_id']) if row and row['invoice_id'] else 0
        plan=c.execute('SELECT * FROM plans WHERE name=?',(plan_name,)).fetchone()
    if not iid:
        items=[(plan['name'],1,float(plan['monthly_price']))]
        if is_tablet:
            items.append(('Tablet / iPad Activation Fee',1,15.00))
            if tablet_sim_type=='physical': items.append(('Physical SIM Card',1,5.00))
        else:
            if float(plan['modem_lease'] or 0)>0: items.append(('Monthly Modem Device Lease',1,float(plan['modem_lease'])))
            if WOOCOMMERCE_ACTIVATION_FEE>0: items.append(('Activation Fee',1,WOOCOMMERCE_ACTIVATION_FEE))
        expected=round(sum(q*p for _,q,p in items),2)
        # Preserve the actual Woo paid total if discounts/tax changed it by adding a reconciliation line.
        if abs(total-expected)>.009: items.append(('WooCommerce Order Adjustment',1,round(total-expected,2)))
        iid=create_invoice(cid,items,date.fromisoformat(contract_start),date.fromisoformat(contract_start)+timedelta(days=15),'WEB')
        with conn() as c: c.execute("UPDATE woocommerce_orders SET invoice_id=?,sync_status='Invoice Created',updated_at=CURRENT_TIMESTAMP WHERE woo_order_id=?",(iid,oid))
        accounting_try('customer',cid); accounting_try('invoice',iid)

    with conn() as c:
        row=c.execute('SELECT payment_id FROM woocommerce_orders WHERE woo_order_id=?',(oid,)).fetchone()
        pid=int(row['payment_id']) if row and row['payment_id'] else 0
        if not pid:
            inv=c.execute('SELECT subtotal,amount_paid,status FROM invoices WHERE id=?',(iid,)).fetchone()
            amount=min(total,max(0,float(inv['subtotal'])-float(inv['amount_paid'] or 0)))
            if amount>0:
                cur=c.execute("INSERT INTO payments(customer_id,invoice_id,amount,payment_date,method,reference,notes) VALUES (?,?,?,?,?,?,?)",(cid,iid,amount,contract_start,'WooCommerce - '+payment_method,transaction_id or f'Woo Order #{oid}',f'Imported from paid WooCommerce order #{oid}'))
                pid=cur.lastrowid
                c.execute('UPDATE invoices SET amount_paid=amount_paid+? WHERE id=?',(amount,iid)); update_invoice_status(c,iid)
            c.execute("UPDATE woocommerce_orders SET payment_id=?,sync_status='Synced',sync_error=NULL,updated_at=CURRENT_TIMESTAMP WHERE woo_order_id=?",(pid or None,oid))
    if pid: accounting_try('payment',pid)
    # Create the signed Service Order/Customer Information agreement in the customer's Files section.
    if agreement_accepted.lower() in ('yes','1','true','accepted'):
        generate_customer_service_agreement(cid,oid,signer_name,signature_text,agreement_accepted_at,autopay)
        archive_customer_aup(cid,oid,aup_accepted_at,aup_viewed_at,aup_version,aup_pdf_sha256)
        ensure_onboarding(cid,oid,'Agreement Signed')
    else:
        with conn() as c: c.execute("UPDATE customer_onboarding SET stage='Agreement Pending',updated_at=CURRENT_TIMESTAMP WHERE customer_id=?",(cid,))
    with conn() as c: c.execute("INSERT INTO audit_log(user_email,action,entity,entity_id,details) VALUES ('woocommerce','IMPORT','woocommerce_order',?,?)",(oid,f'customer={cid}; invoice={iid}; payment={pid or 0}; total={total}'))
    return {'woo_order_id':oid,'customer_id':cid,'invoice_id':iid,'payment_id':pid,'status':'Synced'}

@app.post('/webhooks/woocommerce/order')
async def woocommerce_order_webhook(request:Request):
    if not WOOCOMMERCE_ENABLED: raise HTTPException(503,'WooCommerce integration is disabled.')
    if not WOOCOMMERCE_WEBHOOK_SECRET: raise HTTPException(503,'WooCommerce webhook secret is not configured.')
    raw=await request.body()
    supplied=request.headers.get('x-wc-webhook-signature','')
    expected=base64.b64encode(hmac.new(WOOCOMMERCE_WEBHOOK_SECRET.encode(),raw,hashlib.sha256).digest()).decode()
    if not supplied or not hmac.compare_digest(supplied,expected): raise HTTPException(401,'Invalid WooCommerce webhook signature.')
    try: order=json.loads(raw.decode())
    except Exception: raise HTTPException(400,'Invalid JSON payload.')
    try: result=_woo_import_order(order)
    except Exception as e:
        oid=int(order.get('id') or 0)
        if oid:
            with conn() as c:
                c.execute("INSERT INTO woocommerce_orders(woo_order_id,order_status,order_total,sync_status,sync_error,payload_json) VALUES (?,?,?,?,?,?) ON CONFLICT(woo_order_id) DO UPDATE SET sync_status='Failed',sync_error=excluded.sync_error,payload_json=excluded.payload_json,updated_at=CURRENT_TIMESTAMP",(oid,str(order.get('status') or ''),float(order.get('total') or 0),'Failed',str(e)[:2000],raw.decode(errors='replace')[:1000000]))
        raise HTTPException(500,'WooCommerce order sync failed.')
    return {'ok':True,'result':result}

@app.get('/integrations/woocommerce',response_class=HTMLResponse)
def woocommerce_integration(request:Request):
    require_staff(request)
    with conn() as c:
        rows=c.execute("SELECT w.*,c.account_no,c.first_name,c.last_name FROM woocommerce_orders w LEFT JOIN customers c ON c.id=w.customer_id ORDER BY w.id DESC LIMIT 250").fetchall()
    trs=''.join(f"<tr><td>#{r['woo_order_id']}</td><td>{html.escape(str(r['order_status'] or ''))}</td><td>{html.escape(str(r['customer_type'] or ''))}</td><td>{html.escape(str(r['plan_name'] or ''))}</td><td>{money(r['order_total'] or 0)}</td><td>{html.escape(str(r['account_no'] or ''))} {html.escape(str(r['first_name'] or ''))} {html.escape(str(r['last_name'] or ''))}</td><td>{html.escape(str(r['sync_status'] or ''))}<div class='muted'>{html.escape(str(r['sync_error'] or ''))}</div></td><td><form method='post' action='/integrations/woocommerce/{r['woo_order_id']}/retry'><button class='btn secondary'>Retry</button></form></td></tr>" for r in rows) or "<tr><td colspan='8' class='muted'>No WooCommerce orders received yet.</td></tr>"
    state='Connected / enabled' if WOOCOMMERCE_ENABLED else 'Disabled'
    creds='Configured' if WOOCOMMERCE_CONSUMER_KEY and WOOCOMMERCE_CONSUMER_SECRET else 'Not configured'
    return page(request,'WooCommerce',f"""<h1>WooCommerce Integration</h1><div class='grid'><div class='card'><div class='muted'>Integration</div><b>{state}</b></div><div class='card'><div class='muted'>Store</div><b>{html.escape(WOOCOMMERCE_STORE_URL)}</b></div><div class='card'><div class='muted'>REST API</div><b>{creds}</b></div><div class='card'><div class='muted'>Webhook Endpoint</div><b>/webhooks/woocommerce/order</b></div></div><div class='section card'><h2>Order Sync</h2><p class='muted'>Paid WooCommerce service orders create or match the CRM customer, assign the Residential or Business CRM service, create the first CRM invoice, record the WooCommerce payment, and then sync the resulting records to the active accounting provider. CRM plan prices remain authoritative.</p><table><tr><th>Order</th><th>Woo Status</th><th>Type</th><th>CRM Plan</th><th>Total</th><th>Customer</th><th>Sync</th><th></th></tr>{trs}</table></div>""")

@app.post('/integrations/woocommerce/{order_id}/retry')
def woocommerce_retry(request:Request,order_id:int):
    require_staff(request)
    try:
        order=_woo_basic_request(f'/wp-json/wc/v3/orders/{order_id}')
        _woo_import_order(order)
    except Exception as e:
        with conn() as c: c.execute("UPDATE woocommerce_orders SET sync_status='Failed',sync_error=?,updated_at=CURRENT_TIMESTAMP WHERE woo_order_id=?",(str(e)[:2000],order_id))
    return RedirectResponse('/integrations/woocommerce',303)

# ---------------- Customer Portal Messaging (v10.1) ----------------
@app.get('/messages',response_class=HTMLResponse)
def admin_customer_messages(request:Request,status:str='',customer_id:int=0):
    require_staff(request)
    with conn() as c:
        sql="""SELECT t.*,c.account_no,c.first_name,c.last_name,c.company,
                     SUM(CASE WHEN m.sender_type='customer' AND m.read_by_staff=0 THEN 1 ELSE 0 END) AS unread_count,
                     MAX(m.created_at) AS last_message_at
              FROM customer_message_threads t
              JOIN customers c ON c.id=t.customer_id
              LEFT JOIN customer_messages m ON m.thread_id=t.id"""
        params=[]
        where=[]
        if status in ('Open','Closed'):
            where.append("t.status=?")
            params.append(status)
        if customer_id:
            where.append("t.customer_id=?")
            params.append(customer_id)
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " GROUP BY t.id ORDER BY COALESCE(MAX(m.created_at),t.updated_at) DESC,t.id DESC"
        rows=c.execute(sql,params).fetchall()
    tabs=f"<a class='btn {'ok' if not status else 'secondary'}' href='/messages'>All</a> <a class='btn {'ok' if status=='Open' else 'secondary'}' href='/messages?status=Open'>Open</a> <a class='btn {'ok' if status=='Closed' else 'secondary'}' href='/messages?status=Closed'>Closed</a>"
    trs=''.join(
        f"<tr><td>{'<span class=badge>'+str(r['unread_count'])+' new</span>' if int(r['unread_count'] or 0) else ''}</td>"
        f"<td><a href='/messages/{r['id']}'>{html.escape(str(r['subject'] or 'No subject'))}</a></td>"
        f"<td><a href='/customers/{r['customer_id']}'>{html.escape(str(r['company'] or (str(r['first_name'])+' '+str(r['last_name']))))}</a><div class='muted'>{html.escape(str(r['account_no'] or ''))}</div></td>"
        f"<td>{html.escape(str(r['status'] or 'Open'))}</td><td>{html.escape(str(r['last_message_at'] or r['updated_at'] or ''))}</td></tr>"
        for r in rows
    ) or "<tr><td colspan='5' class='muted'>No customer messages have been received.</td></tr>"
    return page(request,'Customer Messages',f"""<div class="actions right">{tabs}</div><h1>Customer Messages</h1>
    <p class="muted">Messages submitted from the customer portal appear here and remain tied to the customer's CRM account.</p>
    <table><tr><th></th><th>Subject</th><th>Customer</th><th>Status</th><th>Last Activity</th></tr>{trs}</table>""")

@app.get('/messages/{thread_id}',response_class=HTMLResponse)
def admin_customer_message_thread(request:Request,thread_id:int):
    require_staff(request)
    with conn() as c:
        t=c.execute("""SELECT t.*,c.account_no,c.first_name,c.last_name,c.company,c.email,c.phone
                       FROM customer_message_threads t JOIN customers c ON c.id=t.customer_id
                       WHERE t.id=?""",(thread_id,)).fetchone()
        if not t: raise HTTPException(404)
        c.execute("UPDATE customer_messages SET read_by_staff=1 WHERE thread_id=? AND sender_type='customer'",(thread_id,))
        msgs=c.execute("SELECT * FROM customer_messages WHERE thread_id=? ORDER BY id",(thread_id,)).fetchall()
    parts=[]
    for m in msgs:
        who='Customer' if m['sender_type']=='customer' else (m['sender_name'] or 'Entire Wireless')
        side='border-left:5px solid var(--blue)' if m['sender_type']=='customer' else 'border-left:5px solid var(--ok)'
        parts.append(f"<div class='card' style='margin:10px 0;{side}'><div><b>{html.escape(str(who))}</b> <span class='muted'>{html.escape(str(m['created_at'] or ''))}</span></div><div style='white-space:pre-wrap;margin-top:8px'>{html.escape(str(m['body'] or ''))}</div></div>")
    conversation=''.join(parts)
    customer_name=html.escape(str(t['company'] or f"{t['first_name']} {t['last_name']}"))
    return page(request,'Customer Message',f"""<div class="actions right"><a class="btn secondary" href="/messages">Back to Messages</a><a class="btn secondary" href="/customers/{t['customer_id']}">Customer Profile</a></div>
    <h1>{html.escape(str(t['subject']))}</h1>
    <div class="card"><b>{customer_name}</b> · Account {html.escape(str(t['account_no']))}<br><span class="muted">{html.escape(str(t['email'] or ''))} · {html.escape(str(t['phone'] or ''))}</span><br>Status: <b>{html.escape(str(t['status']))}</b></div>
    <div class="section">{conversation}</div>
    <div class="section card"><h2>Reply to Customer</h2><form method="post" action="/messages/{thread_id}/reply"><label>Message</label><textarea name="body" rows="6" required></textarea><button class="btn" type="submit">Send Reply</button></form></div>
    <div class="section"><form method="post" action="/messages/{thread_id}/status"><input type="hidden" name="status" value="{'Open' if t['status']=='Closed' else 'Closed'}"><button class="btn secondary" type="submit">{'Reopen Conversation' if t['status']=='Closed' else 'Close Conversation'}</button></form></div>""")

@app.post('/messages/{thread_id}/reply')
def admin_customer_message_reply(request:Request,thread_id:int,body:str=Form(...)):
    require_staff(request)
    body=body.strip()
    if not body: raise HTTPException(400,'Message is required')
    uid=request.session.get('user_id')
    uname=request.session.get('user_name') or request.session.get('user_email') or 'Entire Wireless'
    with conn() as c:
        t=c.execute("SELECT * FROM customer_message_threads WHERE id=?",(thread_id,)).fetchone()
        if not t: raise HTTPException(404)
        c.execute("""INSERT INTO customer_messages(thread_id,customer_id,sender_type,sender_user_id,sender_name,body,read_by_staff,read_by_customer)
                     VALUES (?,?,?,?,?,?,1,0)""",(thread_id,t['customer_id'],'staff',uid,uname,body))
        c.execute("UPDATE customer_message_threads SET status='Open',updated_at=CURRENT_TIMESTAMP WHERE id=?",(thread_id,))
    audit(request,'CREATE','customer_message_reply',thread_id,f'customer={t["customer_id"]}')
    return RedirectResponse(f'/messages/{thread_id}',303)

@app.post('/messages/{thread_id}/status')
def admin_customer_message_status(request:Request,thread_id:int,status:str=Form(...)):
    require_staff(request)
    status='Closed' if status=='Closed' else 'Open'
    with conn() as c:
        if not c.execute("SELECT 1 FROM customer_message_threads WHERE id=?",(thread_id,)).fetchone(): raise HTTPException(404)
        c.execute("UPDATE customer_message_threads SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(status,thread_id))
    audit(request,'UPDATE','customer_message_thread',thread_id,f'status={status}')
    return RedirectResponse(f'/messages/{thread_id}',303)

@app.get('/portal/messages',response_class=HTMLResponse)
def portal_messages(request:Request):
    cid=require_customer(request)
    with conn() as c:
        cust=c.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone()
        c.execute("UPDATE customer_messages SET read_by_customer=1 WHERE customer_id=? AND sender_type='staff'",(cid,))
        threads=c.execute("""SELECT t.*,
                     SUM(CASE WHEN m.sender_type='staff' AND m.read_by_customer=0 THEN 1 ELSE 0 END) unread_count,
                     MAX(m.created_at) last_message_at
                     FROM customer_message_threads t
                     LEFT JOIN customer_messages m ON m.thread_id=t.id
                     WHERE t.customer_id=? GROUP BY t.id
                     ORDER BY COALESCE(MAX(m.created_at),t.updated_at) DESC,t.id DESC""",(cid,)).fetchall()
    rows=''.join(
        f"<tr><td><a href='/portal/messages/{r['id']}'>{html.escape(str(r['subject'] or 'No subject'))}</a></td><td>{html.escape(str(r['status'] or 'Open'))}</td><td>{html.escape(str(r['last_message_at'] or r['updated_at'] or ''))}</td></tr>"
        for r in threads
    ) or "<tr><td colspan='3' class='muted'>You have no message conversations yet.</td></tr>"
    return portal_page('Messages',f"""<h1>Messages</h1>
    <div class="card"><h2>Send Us a Message</h2><p class="muted">Send a secure message directly to the Entire Wireless customer-service team. Your message will be attached to account <b>{html.escape(str(cust['account_no']))}</b>.</p>
    <form method="post" action="/portal/messages/new"><label>Subject</label><input name="subject" maxlength="160" required><label>Message</label><textarea name="body" rows="7" required></textarea><button class="btn" type="submit">Send Message</button></form></div>
    <div class="section card"><h2>Your Conversations</h2><table><tr><th>Subject</th><th>Status</th><th>Last Activity</th></tr>{rows}</table></div>""")

@app.post('/portal/messages/new')
def portal_message_new(request:Request,subject:str=Form(...),body:str=Form(...)):
    cid=require_customer(request)
    subject=subject.strip()[:160]; body=body.strip()
    if not subject or not body: raise HTTPException(400,'Subject and message are required')
    with conn() as c:
        cust=c.execute("SELECT first_name,last_name FROM customers WHERE id=?",(cid,)).fetchone()
        if not cust: raise HTTPException(404)
        cur=c.execute("INSERT INTO customer_message_threads(customer_id,subject,status) VALUES (?,?, 'Open')",(cid,subject))
        tid=cur.lastrowid
        sender=f"{cust['first_name']} {cust['last_name']}".strip()
        c.execute("""INSERT INTO customer_messages(thread_id,customer_id,sender_type,sender_name,body,read_by_staff,read_by_customer)
                     VALUES (?,?, 'customer',?,?,0,1)""",(tid,cid,sender,body))
        c.execute("UPDATE customer_message_threads SET updated_at=CURRENT_TIMESTAMP WHERE id=?",(tid,))
    return RedirectResponse(f'/portal/messages/{tid}',303)

@app.get('/portal/messages/{thread_id}',response_class=HTMLResponse)
def portal_message_thread(request:Request,thread_id:int):
    cid=require_customer(request)
    with conn() as c:
        t=c.execute("SELECT * FROM customer_message_threads WHERE id=? AND customer_id=?",(thread_id,cid)).fetchone()
        if not t: raise HTTPException(404)
        c.execute("UPDATE customer_messages SET read_by_customer=1 WHERE thread_id=? AND sender_type='staff'",(thread_id,))
        msgs=c.execute("SELECT * FROM customer_messages WHERE thread_id=? ORDER BY id",(thread_id,)).fetchall()
    parts=[]
    for m in msgs:
        who='You' if m['sender_type']=='customer' else (m['sender_name'] or 'Entire Wireless')
        side='border-left:5px solid var(--blue)' if m['sender_type']=='customer' else 'border-left:5px solid var(--ok)'
        parts.append(f"<div class='card' style='margin:10px 0;{side}'><div><b>{html.escape(str(who))}</b> <span class='muted'>{html.escape(str(m['created_at'] or ''))}</span></div><div style='white-space:pre-wrap;margin-top:8px'>{html.escape(str(m['body'] or ''))}</div></div>")
    conversation=''.join(parts)
    reply_form="" if t['status']=='Closed' else f"""<div class="section card"><h2>Reply</h2><form method="post" action="/portal/messages/{thread_id}/reply"><textarea name="body" rows="6" required></textarea><button class="btn" type="submit">Send Reply</button></form></div>"""
    closed="<div class='notice'>This conversation is closed. Start a new message if you need additional help.</div>" if t['status']=='Closed' else ''
    return portal_page('Message',f"""<div class="actions right"><a class="btn secondary" href="/portal/messages">Back to Messages</a></div><h1>{html.escape(str(t['subject']))}</h1>{closed}<div class="section">{conversation}</div>{reply_form}""")

@app.post('/portal/messages/{thread_id}/reply')
def portal_message_reply(request:Request,thread_id:int,body:str=Form(...)):
    cid=require_customer(request)
    body=body.strip()
    if not body: raise HTTPException(400,'Message is required')
    with conn() as c:
        t=c.execute("SELECT * FROM customer_message_threads WHERE id=? AND customer_id=?",(thread_id,cid)).fetchone()
        if not t: raise HTTPException(404)
        if t['status']=='Closed': raise HTTPException(409,'This conversation is closed.')
        cust=c.execute("SELECT first_name,last_name FROM customers WHERE id=?",(cid,)).fetchone()
        sender=f"{cust['first_name']} {cust['last_name']}".strip()
        c.execute("""INSERT INTO customer_messages(thread_id,customer_id,sender_type,sender_name,body,read_by_staff,read_by_customer)
                     VALUES (?,?, 'customer',?,?,0,1)""",(thread_id,cid,sender,body))
        c.execute("UPDATE customer_message_threads SET updated_at=CURRENT_TIMESTAMP WHERE id=?",(thread_id,))
    return RedirectResponse(f'/portal/messages/{thread_id}',303)

@app.get('/portal',response_class=HTMLResponse)
def portal_login_form(request:Request):
    if request.session.get('customer_id'): return RedirectResponse('/portal/home',303)
    return HTMLResponse(f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Customer Portal</title><style>{CSS}</style></head><body><div class="login"><div class="card"><div class="kicker">{COMPANY_NAME}</div><h1>Customer Portal</h1><form method="post"><label>Account Number</label><input name="account_no" required><label>Password</label><input type="password" name="password" required><button class="btn">Sign in</button></form><p class="muted">Need help? {SUPPORT_EMAIL}</p></div></div></body></html>''')
@app.post('/portal')
def portal_login(request:Request,account_no:str=Form(...),password:str=Form(...)):
    with conn() as c: x=c.execute("SELECT * FROM customers WHERE account_no=? AND portal_enabled=1",(account_no,)).fetchone()
    if not x or not x['portal_password_hash'] or not pcheck(password,x['portal_password_hash']): return RedirectResponse('/portal?error=1',303)
    request.session['customer_id']=x['id']; return RedirectResponse('/portal/home',303)
@app.get('/portal/logout')
def portal_logout(request:Request): request.session.pop('customer_id',None); return RedirectResponse('/portal',303)
def require_customer(request):
    cid=request.session.get('customer_id')
    if not cid: raise HTTPException(401)
    return cid
@app.get('/portal/home',response_class=HTMLResponse)
def portal_home(request:Request):
    cid=require_customer(request)
    with conn() as c:
        cust=c.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone()
        inv=c.execute("SELECT * FROM invoices WHERE customer_id=? ORDER BY id DESC",(cid,)).fetchall()
        ms=c.execute("SELECT * FROM modems WHERE customer_id=?",(cid,)).fetchall()
        ss=c.execute("SELECT * FROM sims WHERE customer_id=?",(cid,)).fetchall()
        msg_unread=c.execute("SELECT COUNT(*) n FROM customer_messages WHERE customer_id=? AND sender_type='staff' AND read_by_customer=0",(cid,)).fetchone()['n']
        msg_threads=c.execute("SELECT COUNT(*) n FROM customer_message_threads WHERE customer_id=?",(cid,)).fetchone()['n']
        onboarding=c.execute("SELECT * FROM customer_onboarding WHERE customer_id=?",(cid,)).fetchone()
    bal=sum(x['subtotal']-x['amount_paid'] for x in inv if x['status']!='Void'); rows=''.join(f"<tr><td>{x['invoice_no']}</td><td>{x['issue_date']}</td><td>{money(x['subtotal'])}</td><td>{money(0 if x['status']=='Void' else x['subtotal']-x['amount_paid'])}</td><td>{x['status']}</td><td><a href='/portal/invoices/{x['id']}/statement'>PDF</a>{' · <a href=/portal/invoices/'+str(x['id'])+'/pay>Pay</a>' if STRIPE_SECRET_KEY and x['status'] not in ('Paid','Void') else ''}</td></tr>" for x in inv) or '<tr><td colspan=6>No invoices.</td></tr>'
    eq=''.join([f"<div>Modem IMEI: <b>{x['imei']}</b> — {x['model'] or ''}</div>" for x in ms]+[f"<div>SIM ICCID: <b>{x['iccid']}</b> — {x['carrier'] or ''}</div>" for x in ss]) or 'No equipment assigned.'
    return portal_page('Portal',f'''<h1>Hello, {cust['first_name']}</h1><div class="grid"><div class="card"><div class="muted">Account</div><b>{cust['account_no']}</b></div><div class="card"><div class="muted">Status</div><b>{cust['status']}</b></div><div class="card"><div class="muted">Balance</div><div class="metric">{money(bal)}</div></div><div class="card"><div class="muted">Support</div><a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></div><div class="card"><div class="muted">Messages</div><b>{msg_unread} unread</b><div><a href="/portal/messages">{msg_threads} conversation(s) · Send a message</a></div></div></div><div class="section card"><h2>Getting Your Service Ready</h2><p><b>{html.escape(onboarding['stage'] if onboarding else 'Account Created')}</b></p>{onboarding_progress_html(onboarding,True) if onboarding else '<p class=muted>Your onboarding status will appear here as we prepare your service.</p>'}<p class="muted">You do not need to contact us for routine status checks. This page updates as your order moves through setup.</p></div><div class="section card"><h2>Assigned Equipment</h2>{eq}</div><div class="section card"><h2>Invoices & Statements</h2><table><tr><th>Invoice</th><th>Date</th><th>Total</th><th>Balance</th><th>Status</th><th></th></tr>{rows}</table></div>''')
@app.get('/portal/invoices/{iid}/statement')
def portal_statement(request:Request,iid:int):
    cid=require_customer(request)
    with conn() as c:
        if not c.execute("SELECT 1 FROM invoices WHERE id=? AND customer_id=?",(iid,cid)).fetchone(): raise HTTPException(404)
    return FileResponse(generate_statement(iid),media_type='application/pdf',filename=f'statement-{iid}.pdf')
@app.get('/portal/invoices/{iid}/pay')
def portal_pay(request:Request,iid:int):
    cid=require_customer(request)
    with conn() as c:
        if not c.execute("SELECT 1 FROM invoices WHERE id=? AND customer_id=?",(iid,cid)).fetchone(): raise HTTPException(404)
    session=stripe_checkout_for_invoice(iid,f'{PUBLIC_URL}/portal/payment-success?session_id={{CHECKOUT_SESSION_ID}}',f'{PUBLIC_URL}/portal/home',context='portal_invoice')
    if not session: return RedirectResponse('/portal/home',303)
    return RedirectResponse(session['url'],303)
@app.get('/portal/payment-success')
def portal_success(request:Request,session_id:str=''):
    require_customer(request); return portal_page('Payment',f'''<div class="card"><h1>Payment submitted</h1><p>Thank you. Your payment will appear after confirmation from the payment processor.</p><a class="btn" href="/portal/home">Return to Portal</a></div>''')

@app.post('/stripe/webhook')
async def stripe_webhook(request:Request):
    secret=os.getenv('STRIPE_WEBHOOK_SECRET',''); payload=await request.body(); sig=request.headers.get('stripe-signature','')
    if not secret: return JSONResponse({'ok':False,'error':'webhook secret not configured'},400)
    try:
        parts=dict(x.split('=',1) for x in sig.split(',') if '=' in x); ts=parts.get('t',''); v1=parts.get('v1','')
        expected=hmac.new(secret.encode(),ts.encode()+b'.'+payload,hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected,v1) or abs(time.time()-int(ts))>300: raise ValueError('invalid signature')
        event=json.loads(payload.decode())
    except Exception: return JSONResponse({'ok':False},400)
    if event.get('type')=='checkout.session.completed':
        sess=event['data']['object']; meta=sess.get('metadata',{}); iid=int(meta.get('invoice_id','0') or 0); cid=int(meta.get('customer_id','0') or 0); amount=float(sess.get('amount_total',0))/100
        # For card Checkout, only a paid session is allowed to post a CRM payment.
        if iid and cid and sess.get('payment_status','paid')=='paid':
            pid=None
            with conn() as c:
                exists=c.execute("SELECT 1 FROM payments WHERE method='Stripe' AND reference=?",(sess['id'],)).fetchone()
                target=c.execute("SELECT status FROM invoices WHERE id=? AND customer_id=?",(iid,cid)).fetchone()
                if not exists and target and target['status']!='Void':
                    cur=c.execute("INSERT INTO payments(customer_id,invoice_id,amount,payment_date,method,reference) VALUES (?,?,?,?,?,?)",(cid,iid,amount,date.today().isoformat(),'Stripe',sess['id'])); pid=cur.lastrowid
                    c.execute("UPDATE invoices SET amount_paid=amount_paid+? WHERE id=?",(amount,iid)); update_invoice_status(c,iid)
                    if meta.get('payment_context')=='customer_signup':
                        paid_on=date.today(); anchor_day=min(paid_on.day,28)
                        c.execute("UPDATE customers SET billing_hold_until_first_payment=0,billing_started_at=?,first_stripe_payment_at=?,contract_start=?,billing_day=? WHERE id=?",(paid_on.isoformat(),datetime.now().isoformat(timespec='seconds'),paid_on.isoformat(),anchor_day,cid))
            if pid:
                try: accounting_try('payment',pid)
                except Exception as e: print('accounting payment sync error:',e)
                try: email_payment_confirmation(pid)
                except Exception as e: print('payment confirmation email error:',e)
                try: maybe_restore_after_payment(cid)
                except Exception as e: print('auto restore error:',e)
    return {'received':True}

# lightweight built-in scheduler for an always-on web service
def _get_setting(key):
    with conn() as c:
        r=c.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone(); return r['value'] if r else None
def _set_setting(key,value):
    with conn() as c: c.execute('INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,value))

async def scheduler_loop():
    while True:
        try:
            sync_growth()
            now=business_now(); today=now.date().isoformat()
            if now.hour>=7 and _get_setting('last_daily_run')!=today:
                run_daily_tasks(); run_monthly_billing(True); _set_setting('last_daily_run',today)
            if now.hour>=BUSINESS_CLOSE_HOUR and _get_setting('last_eod_notice_run')!=today:
                run_eod_due_notices(); _set_setting('last_eod_notice_run',today)
        except Exception as e:
            print('scheduler error:',e)
        await asyncio.sleep(300)

# Additive Sales & Growth module; preserves the customer, billing, inventory,
# accounting, Stripe, reporting, and customer-classification features.
from growth import install as install_growth
install_growth(globals())

@app.on_event('startup')
async def start_scheduler():
    asyncio.create_task(scheduler_loop())
