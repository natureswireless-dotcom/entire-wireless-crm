# Entire Wireless ISP CRM v10.12 — Verizon Connection Test

- Added a safe **Test Verizon Connection** button to Carrier Control.
- The test validates both ThingSpace OAuth (App Key/Secret) and the UWS session (UWS Username/Password).
- The connection test never sends an activate, suspend, restore, or other device-changing request.
- Added safe success/failure feedback in Carrier Control and concise Render log output without credentials/tokens.
- Past-due suspension automation now skips customers that do not have an assigned Verizon SIM with an ICCID, preventing test customers without equipment from generating misleading failed carrier actions.
- Preserves v10.11 tax/fee functionality, billing, customer data, equipment, portal, WooCommerce, accounting integrations, and the existing persistent SQLite database.
