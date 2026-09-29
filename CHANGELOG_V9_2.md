# Entire Wireless ISP CRM v9.2

## Zoho Books historical synchronization
- Adds **Sync Existing CRM Records** to the Zoho Books Integration Center.
- Preview eligible historical customers, invoices, and payments before sending anything.
- Filter migration by all records, date range, or one customer.
- Existing Zoho-linked records are skipped.
- Existing invoice numbers are checked in Zoho before creation to reduce duplicate risk.
- Historical payments retain the stable `EWCRM-PAY-{id}` reference used by the live sync.
- Original CRM invoice issue date, due date, line items, invoice number, amounts, and payment dates are preserved through the existing Zoho sync functions.
- Void invoices are excluded.
- Runs use controlled batches of 10, 25, or 50 records to reduce web-request timeout risk.
- Historical runs are logged in `zoho_history_runs` and the CRM Audit Log.
- The migration can be resumed safely; successfully linked records disappear from subsequent previews.

## Data safety
- Additive database migration only.
- Existing Zoho OAuth connection and Zoho IDs are preserved.
- Existing QuickBooks integration and IDs are preserved.
- Existing `/var/data/isp_crm_v2.db` remains the database.
