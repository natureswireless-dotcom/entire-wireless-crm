# Upgrade to v9.2

1. Back up the existing persistent database `/var/data/isp_crm_v2.db`.
2. Deploy v9.2 to the same GitHub repository and the same Render web service.
3. Keep the existing persistent disk and all existing environment variables.
4. Keep `ACCOUNTING_PROVIDER=zoho` and the current Zoho credentials/redirect URI.
5. No Zoho reconnect is required.
6. After deployment, open **Zoho Books → Sync Existing CRM Records**.
7. Review the preview before running a historical batch.
