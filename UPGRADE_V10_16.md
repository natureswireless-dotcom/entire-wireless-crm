# Upgrade to v10.16

Deploy normally through the existing GitHub -> Render workflow. Keep the existing persistent database and Render environment variables unchanged.

No database reset is required. No new environment variables are required.

## ThingSpace inventory
Open Carrier Control and select **Sync Inventory from ThingSpace**. The sync is read-only toward Verizon: it retrieves inventory and writes the returned IMEI/ICCID records into the CRM. Existing CRM customer assignments are preserved.

## Credits and test cleanup
Open an invoice as an administrator and select **Issue Credit** to reduce its unpaid balance. For test/duplicate records, **Delete Test Invoice** permanently removes the CRM invoice after explicit confirmation. Customer permanent deletion now also removes records created by newer CRM modules that previously could block deletion.
