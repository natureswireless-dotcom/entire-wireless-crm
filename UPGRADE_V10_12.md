# Upgrade to v10.12

1. Deploy this package over v10.11 using the existing Render service.
2. Keep `DATA_DIR=/var/data` (or your existing persistent data path) unchanged. Do not replace or delete `isp_crm_v2.db`.
3. Keep `VERIZON_DRY_RUN=1` while validating the Verizon integration.
4. Confirm the existing Verizon environment variables remain configured in Render.
5. After deployment, open **Carrier Control** and click **Test Verizon Connection** once.
6. A successful test confirms ThingSpace OAuth and UWS authentication without changing any Verizon device.

No database migration or new environment variable is required for v10.12.
