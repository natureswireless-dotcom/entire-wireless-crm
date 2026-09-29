# Upgrade to v10.13.1

Deploy normally through the existing GitHub/Render workflow. No database migration or environment-variable changes are required. Preserve the existing persistent database at `/var/data/isp_crm_v2.db`. Keep `VERIZON_DRY_RUN=1` until read-only device verification is confirmed.
