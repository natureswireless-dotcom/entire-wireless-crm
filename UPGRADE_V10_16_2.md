# Upgrade to v10.16.2

1. Deploy this package over v10.16.1 using the existing Render service/repository workflow.
2. Keep the existing persistent database path `/var/data/isp_crm_v2.db` unchanged.
3. Keep `VERIZON_DRY_RUN=1` while diagnosing the ThingSpace inventory issue.
4. No new environment variables are required.
5. Open **Carrier Control** and click **Diagnose ThingSpace Inventory**.
6. Compare **All accessible devices** with **Devices in configured account**. This identifies whether the UWS user can see the inventory and whether `VERIZON_ACCOUNT_NAME` matches the billing account containing it.
