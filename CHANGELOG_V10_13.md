# Entire Wireless ISP CRM v10.13 — Verizon Device Verification

- Adds read-only Verizon device verification to Carrier Control.
- Uses the official Connectivity Management `POST /devices/actions/list` endpoint for a selected Verizon ICCID.
- Displays provisioning state, connectivity, service plan, and masked device identifiers when returned.
- Sends no activate, suspend, restore, deactivate, or other device-changing request.
- Preserves the v10.12.1 Verizon connection test and no-ICCID suspension protection.
- No database migration. Existing `/var/data/isp_crm_v2.db` remains unchanged.
