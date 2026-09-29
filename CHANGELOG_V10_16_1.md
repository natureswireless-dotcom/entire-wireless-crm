# v10.16.1 — ThingSpace Inventory Sync Diagnostics

- Uses a simple account-scoped ThingSpace device-list request for the initial inventory retrieval.
- Retains documented DeviceId pagination when Verizon reports more than one page.
- Reports the number of Verizon device records, IMEIs, ICCIDs, and pages returned before summarizing imports.
- Distinguishes an actual empty device list from malformed/unexpected Verizon responses and HTTP failures.
- Preserves existing CRM inventory and customer assignments.
- No database migration and no new environment variables.
