# Upgrade to Entire Wireless ISP CRM v9.0

1. Keep the existing Render service and persistent disk. Do not create a new database.
2. Back up `/var/data/isp_crm_v2.db` before deployment.
3. Deploy this code to the same GitHub repository / Render service used by v8.1.
4. In Render add the following environment variables. Never commit secrets to GitHub:

   ACCOUNTING_PROVIDER=zoho
   ZOHO_ENABLED=1
   ZOHO_CLIENT_ID=<from Zoho API Console>
   ZOHO_CLIENT_SECRET=<from Zoho API Console>
   ZOHO_REDIRECT_URI=https://crm.natureswireless.org/zoho/callback

   Optional US defaults:
   ZOHO_ACCOUNTS_BASE=https://accounts.zoho.com
   ZOHO_API_DOMAIN=https://www.zohoapis.com
   ZOHO_API_TIMEOUT=60
   ZOHO_API_RETRIES=2

5. Keep existing QuickBooks environment variables unchanged. `ACCOUNTING_PROVIDER=zoho` prevents normal newly-created CRM billing records from also being pushed to QuickBooks.
6. Redeploy and open Admin -> Zoho Books.
7. Click Connect Zoho Books and approve the requested Zoho Books scopes.
8. After the organization name appears, click Test Connection.
9. Test with a new CRM customer, then a small invoice, then a partial payment, then the remaining payment.

The registered Zoho API Console redirect URI must match exactly:
`https://crm.natureswireless.org/zoho/callback`
