# Entire Wireless ISP CRM v10.13.1 — Verizon Carrier Label Compatibility

- Recognizes existing CRM Verizon SIM inventory stored with carrier labels `VZW`, `Verizon`, or `Verizon Wireless`.
- Applies the same recognition to read-only device verification, carrier actions, and past-due suspension eligibility.
- Preserves v10.13 Verizon authentication/device verification and all prior CRM functionality.
- No database migration or new environment variables.
- Keep `VERIZON_DRY_RUN=1` while validating device lookup.
