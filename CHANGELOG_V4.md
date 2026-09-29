# Version 4 Changes

- Added clear **Unassign & Reuse** buttons for assigned modems and SIMs on customer records.
- Added unassign controls directly to the Modem/IMEI and SIM/ICCID inventory screens.
- Added **Release All Equipment to Inventory** for customers ending service.
- Individual and bulk release operations preserve `equipment_history` records.
- Released equipment is set to `Available` and can immediately be assigned to another customer.
- IMEI and ICCID records are retained and remain unique; release never deletes inventory.
- Unassignment now validates that the equipment is actually assigned to the selected customer.
- Changed unassignment from a GET link to a POST action with a confirmation prompt.
- Preserved all Version 3 billing, statement, Stripe, Verizon ThingSpace, suspension, restoration, and reconnect-fee functionality.
