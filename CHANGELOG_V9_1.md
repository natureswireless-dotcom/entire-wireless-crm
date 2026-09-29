# Entire Wireless ISP CRM v9.1

## Accounting integration cleanup and safety

- Updates the visible CRM version label to v9.1.
- Adds a centralized **Accounting Integrations** dashboard for administrators.
- Shows the active accounting provider, connection state, failed-sync count, and last sync activity for Zoho Books and QuickBooks Online.
- Adds an Accounting status card to the main ISP Operations Dashboard.
- Makes the active accounting provider the primary sidebar integration.
- Hides inactive accounting-provider links from the sidebar by default while keeping their integration pages available as a fallback.
- Adds `ACCOUNTING_SHOW_INACTIVE=1` to optionally show both Zoho Books and QuickBooks links in the sidebar.
- Blocks retry actions for inactive accounting providers to reduce the risk of accidental duplicate accounting entries.
- Keeps all existing Zoho Books, QuickBooks, billing, payment, subscriber, inventory, Verizon, portal, and reporting functionality intact.

## Database

No destructive database changes. Continue using the existing persistent database at `/var/data/isp_crm_v2.db` on Render.
