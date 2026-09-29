# Upgrade to v10.4
Deploy this build over the existing Render service. Keep the existing persistent database at `/var/data/isp_crm_v2.db` and all current environment variables. No database reset is required. The `customer_onboarding` table and index are created automatically at startup.
