# Upgrade v8.0 -> v8.1

1. Keep the existing Render service and persistent disk.
2. Back up `/var/data/isp_crm_v2.db` before deployment.
3. Deploy this code to the same GitHub repository/Render service.
4. Keep all current QuickBooks production credentials and environment values.
5. Optional Render variables: `QUICKBOOKS_API_TIMEOUT=90`, `QUICKBOOKS_API_RETRIES=2` (these are already the defaults).
6. After deployment, use QuickBooks > Test Connection once.
7. Then use Retry Failed Syncs once. Invoice recovery checks `DocNumber` before creating, and create calls use stable Intuit request IDs to reduce duplicate risk.
