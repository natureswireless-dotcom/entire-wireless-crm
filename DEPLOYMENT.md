# Deploying Entire Wireless ISP CRM v4 to crm.natureswireless.org

## Recommended architecture

Keep the public website at `natureswireless.org` and host the CRM separately at:

**crm.natureswireless.org**

This avoids changing or disrupting the existing public website.

## Step 1 — Create a GitHub repository

1. Create a new private GitHub repository, for example `entire-wireless-crm`.
2. Upload the contents of this CRM folder to the repository root.
3. Do **not** upload a real `.env` file. The included `.gitignore` excludes it.
4. Confirm the repository root contains `main.py`, `Dockerfile`, `requirements.txt`, and `render.yaml`.

## Step 2 — Create the Render service

### Blueprint method

1. Sign in to Render.
2. Choose **New > Blueprint**.
3. Connect the private GitHub repository.
4. Render will detect `render.yaml`.
5. Set the secret values Render asks for, especially `ADMIN_PASSWORD`.
6. Deploy the Blueprint.

The included blueprint creates a Docker web service with a persistent disk mounted at `/var/data`.

### Manual method

If you do not use the Blueprint:

- Service type: Web Service
- Runtime: Docker
- Health check: `/health`
- Persistent disk mount: `/var/data`
- `DATA_DIR=/var/data`
- Set the environment variables from `.env.example`

## Step 3 — Set production environment variables

At minimum configure:

- `PUBLIC_URL=https://crm.natureswireless.org`
- `COOKIE_SECURE=1`
- `ADMIN_EMAIL=admin@natureswireless.org`
- `ADMIN_PASSWORD=<a strong unique password>`
- `SECRET_KEY=<a long random value>` (the Blueprint can generate this)
- `DATA_DIR=/var/data`

Optional email settings:

- `SMTP_HOST`
- `SMTP_PORT=587`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_FROM=support@natureswireless.org`

Optional Stripe settings:

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`

## Step 4 — Test the temporary Render URL

Render gives the service an address similar to:

`https://entire-wireless-isp-crm.onrender.com`

Before connecting your domain, open that address and test:

- `/health`
- Staff login
- Create a test customer
- Create an IMEI and ICCID
- Assign both to the test customer
- Create an invoice
- Download its PDF statement
- Sign into `/portal` as the test customer

## Step 5 — Add crm.natureswireless.org in Render

1. Open the CRM Web Service in Render.
2. Open **Settings**.
3. Find **Custom Domains**.
4. Choose **Add Custom Domain**.
5. Enter `crm.natureswireless.org`.
6. Render will show the DNS target it expects.

## Step 6 — Add the DNS record where natureswireless.org is managed

In the DNS control panel for `natureswireless.org`, add the DNS record Render displays. For a normal CRM subdomain this is typically a CNAME such as:

- Type: `CNAME`
- Name/Host: `crm`
- Target/Value: your Render service hostname (for example `entire-wireless-isp-crm.onrender.com`)

Use the **exact target shown by Render** for your service.

Do not change the records for the root website unless you intentionally want to move the public website too.

## Step 7 — Verify the domain

Return to Render's **Custom Domains** section and click **Verify**. Once DNS verifies, Render provisions TLS/SSL and the CRM should load at:

`https://crm.natureswireless.org`

## Step 8 — Configure Stripe (optional)

1. In Stripe, obtain the production secret key and add it to Render as `STRIPE_SECRET_KEY`.
2. Create a webhook endpoint:
   `https://crm.natureswireless.org/stripe/webhook`
3. Subscribe the webhook to `checkout.session.completed`.
4. Copy its webhook signing secret into Render as `STRIPE_WEBHOOK_SECRET`.
5. Redeploy/restart the CRM.

## Step 9 — Configure statement email (optional)

Enter the SMTP credentials for the email provider that is authorized to send as `support@natureswireless.org`. Once configured, invoice statements and eligible past-due reminders can be sent directly from the CRM.

## Security checklist before real customer use

- Replace the default admin password before first launch.
- Use a private GitHub repository.
- Never put passwords, Stripe keys, or SMTP credentials into source files.
- Confirm HTTPS is working before entering customer information.
- Restrict administrator accounts to people who need them.
- Create separate employee logins instead of sharing one password.
- Keep customer portal passwords unique.
- Keep the persistent disk enabled.
- Establish recurring backups and test restoring them.
- Keep Python package versions updated and review security updates.

## Database growth

Version 4 uses SQLite because it is simple and reliable for a small internal ISP team when stored on a persistent disk. For higher traffic, multiple application instances, or a large subscriber base, the next upgrade should use managed PostgreSQL.

## Version 4 Verizon ThingSpace settings

Keep these safe-mode values while testing:

- `VERIZON_ENABLED=0`
- `VERIZON_DRY_RUN=1`
- `SUSPEND_AFTER_DAYS=3`
- `RECONNECT_FEE=25.00`

When Verizon ThingSpace/UWS credentials are available, add `VERIZON_ACCOUNT_NAME`, `VERIZON_APP_KEY`, `VERIZON_APP_SECRET`, `VERIZON_UWS_USERNAME`, `VERIZON_UWS_PASSWORD`, and a long random `VERIZON_CALLBACK_TOKEN` in Render Environment. Do not put these secrets in GitHub.

After dry-run testing on designated test accounts, live provisioning requires `VERIZON_ENABLED=1` and `VERIZON_DRY_RUN=0`.
