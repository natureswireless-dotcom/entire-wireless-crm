# Entire Wireless ISP CRM v9.0

## Zoho Books integration
- Added Zoho Books as a full accounting synchronization provider while preserving QuickBooks Online.
- Added provider selection through `ACCOUNTING_PROVIDER=zoho|quickbooks|none`.
- Added OAuth 2.0 server-side authorization with offline access and automatic refresh-token handling.
- Added automatic Zoho Books organization discovery after OAuth connection.
- Added `/integrations/zoho` Integration Center with connection status, organization, Test Connection, Disconnect, failed-sync retry, and recent sync activity.
- Added automatic CRM customer -> Zoho Books contact synchronization.
- Added automatic CRM invoice -> Zoho Books invoice synchronization using the CRM invoice number.
- Added automatic CRM payment -> Zoho Books customer-payment synchronization, including partial payments applied to the correct invoice.
- Added Zoho service-item discovery/creation for `Entire Wireless Services`.
- Added duplicate protection by matching contacts, matching invoices by invoice number, and assigning every CRM payment a stable `EWCRM-PAY-<id>` reference.
- Added controlled API retry and configurable timeouts.
- Added separate Zoho linkage/status/error fields so QuickBooks linkage is never overwritten.
- Added separate `zoho_oauth` and `zoho_sync_log` tables.

## Data safety
- All database changes are additive migrations against the existing `isp_crm_v2.db`.
- Existing customers, invoices, payments, inventory, contracts, documents, Verizon settings/history, QuickBooks links, Stripe data, employees, and audit records are preserved.
- QuickBooks remains available but normal new-record synchronization follows only the selected accounting provider.
