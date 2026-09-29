# Entire Wireless ISP CRM v8.1

QuickBooks production reliability update:
- Raises QuickBooks API timeout from 35 seconds to configurable `QUICKBOOKS_API_TIMEOUT` (default 90).
- Adds configurable retry count `QUICKBOOKS_API_RETRIES` (default 2).
- Adds stable Intuit `requestid` values to customer, service-item, invoice, and payment create calls so timeout retries are idempotent.
- Before creating an invoice, searches QuickBooks by CRM invoice `DocNumber` and links an existing match. This safely recovers when QuickBooks accepted a prior request but the CRM timed out waiting for the response.
- Adds CRM reference notes to newly created QuickBooks invoices/payments for easier reconciliation.
- Existing database schema and `/var/data/isp_crm_v2.db` remain unchanged.
