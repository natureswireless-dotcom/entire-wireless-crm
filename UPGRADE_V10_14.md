# Upgrade to v10.14

Deploy normally through GitHub/Render. No database migration or new environment variables are required.

The existing persistent database at /var/data/isp_crm_v2.db must remain unchanged. Legacy Tablet/iPad database records are retained but no longer exposed as an active CRM service or customer-profile UI section.

Keep VERIZON_DRY_RUN=1 while Verizon carrier testing continues.
