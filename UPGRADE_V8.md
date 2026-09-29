# Upgrade to Entire Wireless ISP CRM v8.0

1. Back up `/var/data/isp_crm_v2.db` before deployment.
2. Replace the application files in the existing GitHub repository with the v8.0 files. Do not create a new Render service or database.
3. In Render > existing CRM Web Service > Environment, add:
   - `QUICKBOOKS_ENABLED=1`
   - `QUICKBOOKS_ENVIRONMENT=sandbox`
   - `QUICKBOOKS_CLIENT_ID=<Intuit Development Client ID>`
   - `QUICKBOOKS_CLIENT_SECRET=<Intuit Development Client Secret>`
   - `QUICKBOOKS_REDIRECT_URI=https://crm.natureswireless.org/quickbooks/callback`
4. Ensure the exact same redirect URI is registered under Intuit Developer > Settings > Redirect URIs > Development.
5. Save, rebuild, and deploy in Render.
6. Log in as an administrator and open **QuickBooks** in the CRM navigation.
7. Click **Connect QuickBooks**, authorize the Intuit sandbox company, and return to the CRM.
8. Use **Test Connection**.
9. Create a test subscriber, test invoice, partial payment, and final payment. Verify all records in the QuickBooks sandbox.
10. Only after sandbox testing, configure Intuit Production credentials/redirect URI, change Render to `QUICKBOOKS_ENVIRONMENT=production`, replace Client ID/Secret with Production credentials, redeploy, and connect the real QuickBooks Online company.

Never commit the QuickBooks Client Secret to GitHub.
