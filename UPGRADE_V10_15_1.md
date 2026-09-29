# Upgrade to v10.15.1

Deploy normally through the existing GitHub/Render workflow. No new environment variables or database migrations are required. Keep the existing persistent database at `/var/data/isp_crm_v2.db`.

After deployment, an administrator can open Customers > customer profile > Edit Customer and change Account Number. Duplicate account numbers are rejected.
