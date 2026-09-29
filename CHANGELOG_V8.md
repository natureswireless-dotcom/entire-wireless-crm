# Entire Wireless ISP CRM v8.0

## QuickBooks Online integration
- OAuth 2.0 connection to QuickBooks Online Accounting API.
- Sandbox and production environments.
- New CRM subscribers automatically create/match QuickBooks customers.
- CRM invoices automatically create QuickBooks invoices attached to the linked customer.
- CRM payments automatically create QuickBooks payments and apply them to the corresponding QuickBooks invoice.
- Partial payments are supported.
- QuickBooks IDs and sync status/error timestamps are stored on CRM records.
- QuickBooks Integration Center provides connection status, test connection, disconnect, recent sync activity, and retry of failed syncs.
- Failed QuickBooks calls do not roll back the underlying CRM customer/invoice/payment record.
- OAuth access tokens are refreshed automatically using the stored refresh token.
- Creates/reuses an `Entire Wireless Services` QuickBooks service item for invoice lines.

## Upgrade
- Built directly from Entire Wireless ISP CRM v7.0.
- Existing SQLite database is migrated in place; existing customers, inventory, notes, billing, Verizon integration, and V7 reporting are preserved.
