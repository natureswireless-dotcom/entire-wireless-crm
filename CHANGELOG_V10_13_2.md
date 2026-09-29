# v10.13.2 — Verizon Inventory Recognition Fix

- Corrected the remaining Carrier Control read-only device verification inventory query so CRM carrier value `VZW` is recognized as Verizon.
- Corrected the remaining past-due suspension eligibility query to recognize `VZW`, `Verizon`, and `Verizon Wireless`.
- Preserves the existing shared Verizon carrier helper and suspend/restore lookup behavior.
- No database migration. No new environment variables.
- Keep `VERIZON_DRY_RUN=1` while validating device lookup.
