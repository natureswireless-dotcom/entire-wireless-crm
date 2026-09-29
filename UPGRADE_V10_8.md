# Upgrade to Entire Wireless ISP CRM v10.8

1. Deploy this package over the existing v10.7 application code.
2. Keep the existing persistent database at `/var/data/isp_crm_v2.db` unchanged.
3. Keep all existing Render environment variables and persistent-disk settings.
4. No database reset or migration is required for the invoice redesign.
5. After deployment, open the CRM and confirm the top-left header displays `v10.8`.
6. Open an existing invoice and generate/download its PDF to verify the new Entire Wireless statement format.

All v10.7 Website Lead API behavior is preserved.
