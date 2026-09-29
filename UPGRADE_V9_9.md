# Upgrade to v9.9

Deploy this ZIP over the same Render web service and keep the same persistent database.

No new environment variables are required.

The Sales & Growth database objects are additive SQLite tables created automatically by growth.py. Existing CRM customer, invoice, payment, equipment, accounting, and portal data are not replaced.

Do not delete or reset /var/data/isp_crm_v2.db.

After deployment, confirm that the left navigation shows Sales & Growth and that /growth opens normally.
