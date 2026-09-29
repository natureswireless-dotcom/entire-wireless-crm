# Entire Wireless ISP CRM v10.16

- Added administrator-only Verizon ThingSpace inventory synchronization.
- Imports IMEIs into Modem Inventory and ICCIDs into SIM Inventory from the configured Verizon account.
- Uses the existing ThingSpace OAuth/UWS credentials and official paginated device-list workflow.
- Preserves existing CRM inventory records and customer equipment assignments; duplicate IMEIs/ICCIDs are not created.
- Imports Verizon MDN/carrier information where available.
- Added administrator invoice credits with a required reason and audit-log entry.
- Added administrator permanent deletion for test/duplicate invoices with explicit `DELETE INVOICE` confirmation.
- Updated permanent test-customer deletion to clean up newer CRM module records, including messages, onboarding, collections, tablet services, and WooCommerce records.
- Preserves v10.15.2 collection disclosure, v10.15.1 account-number editing, and all prior functionality.
