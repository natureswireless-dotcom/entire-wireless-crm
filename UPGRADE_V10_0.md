# Upgrade to v10.0

Deploy over the existing Render service and keep the existing persistent database. No new environment variables are required.

Existing invoices do not need to be recreated in the database. When an invoice PDF is opened, emailed, edited, or otherwise regenerated, the CRM uses the new v10.0 invoice layout and live customer/account/plan data.
