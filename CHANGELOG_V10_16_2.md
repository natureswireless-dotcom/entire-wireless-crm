# v10.16.2 — ThingSpace Account Diagnostic

- Adds a read-only **Diagnose ThingSpace Inventory** action to Carrier Control.
- Compares an unfiltered `/devices/actions/list` request (all devices visible to the authenticated UWS user) with the configured `VERIZON_ACCOUNT_NAME` request.
- Displays aggregate device/IMEI/ICCID counts and billing account names returned by Verizon.
- Does not expose IMEIs, ICCIDs, credentials, bearer tokens, or VZ-M2M session tokens in the diagnostic UI.
- Keeps the existing v10.16.1 inventory importer unchanged.
- Preserves Dry Run behavior and all existing CRM data/features.
