# Upgrade to v9.1

1. Back up `/var/data/isp_crm_v2.db`.
2. Deploy v9.1 to the same GitHub repository and same Render web service.
3. Keep the existing Render persistent disk and `DATA_DIR` configuration.
4. Keep `ACCOUNTING_PROVIDER=zoho` to continue using Zoho Books as the live accounting sync provider.
5. Optional: set `ACCOUNTING_SHOW_INACTIVE=1` if administrators should see both Zoho Books and QuickBooks in the sidebar. The default is `0`.
6. No Zoho OAuth reconnection is required solely for this upgrade; existing stored tokens and organization linkage are preserved in the database.

Inactive provider pages remain accessible from the Accounting Integrations page, but their failed-sync retry actions are blocked unless that provider is active.
