# Upgrade Entire Wireless CRM v3 to v4 on Render

1. Back up `/var/data/isp_crm_v2.db` before deploying if the CRM contains live data.
2. Extract the Version 4 ZIP.
3. Upload/commit all Version 4 files to the **root** of the existing GitHub repository, replacing the Version 3 files.
4. Do not delete the Render persistent disk and do not create a new database. Version 4 keeps the existing `isp_crm_v2.db` database filename.
5. Let Render deploy the latest GitHub commit.
6. Sign in and open a customer with assigned equipment.
7. Under **Assigned Modems** or **Assigned SIMs**, click **Unassign & Reuse**. The item will be detached from that customer, recorded in Equipment History, set to `Available`, and become assignable to another customer.
8. For a customer ending service, use **Release All Equipment to Inventory** to release every assigned modem and SIM at once.
9. Confirm the released IMEI/ICCID appears as `Available` on the Modems or SIM Cards inventory screen.
10. Open another customer and assign the released equipment to verify reuse.

## Version 4 equipment behavior

- Assignment requires the equipment to be unassigned and `Available`.
- Individual unassignment is a POST action with a confirmation prompt.
- The CRM validates that the modem/SIM is actually assigned to the customer before releasing it.
- Released equipment receives `customer_id = NULL` and `status = Available`.
- Every release writes an `UNASSIGNED` row to `equipment_history` with the customer ID and reason.
- Bulk release preserves a separate history record for each modem and SIM.
- IMEI and ICCID values remain in inventory and remain unique; they are never deleted by the release workflow.

## Verizon note

Unassigning a SIM in the CRM changes the CRM inventory assignment. It does not itself deactivate or reprovision the line at Verizon. Continue using Carrier Control / Verizon provisioning for network-side service changes.
