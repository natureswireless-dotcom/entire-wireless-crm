# Entire Wireless ISP CRM v9.4

- Added admin-only permanent customer deletion for test, duplicate, and mistakenly-created CRM customers.
- Requires typing DELETE plus a deletion reason and browser confirmation.
- Deletes customer-linked CRM invoices, invoice items, payments, notes, documents, subscriptions, pending charges, carrier history, equipment history, and accounting sync-log entries.
- Returns assigned modems and SIMs to Available inventory before deletion.
- Preserves an audit-log tombstone containing the deleted account number/name/reason.
- Does not delete transactions already created in Zoho Books or QuickBooks; those accounting records remain under the accounting provider's control.
- Updated application version to v9.4.
