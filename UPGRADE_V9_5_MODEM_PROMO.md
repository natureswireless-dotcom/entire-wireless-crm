# Upgrade — v9.5 Modem Rental Promotion Update

Deploy this package over the existing Entire Wireless CRM service.

- Keep the same Render service.
- Keep the same persistent disk/database (`/var/data/isp_crm_v2.db`).
- Do not reset or replace the database.
- No new Render environment variables are required.
- No Zoho Books reconnection is required.

The database migration is additive. Existing customers default to no modem-rental promotion and keep all current billing/accounting data.
