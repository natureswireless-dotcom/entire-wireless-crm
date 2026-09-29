# Entire Wireless ISP CRM v7.0

Built directly from the supplied Entire Wireless ISP CRM v6.0 codebase.

## Reporting upgrades
- Added printable PDF reports for all, available, and assigned modem IMEIs.
- Added printable PDF reports for all, available, and assigned SIM ICCIDs.
- Assigned-equipment reports include the customer/account assignment.
- Added printable all, active, and inactive customer reports.
- Added an individual printable customer report from each customer record.
- Added Print All / Print Available / Print Assigned controls directly on modem and SIM inventory screens.

## Permanent inventory removal
- Administrators can permanently delete modem or SIM inventory records that will never be usable again.
- Assigned equipment cannot be deleted; it must first be unassigned.
- Before deletion, the CRM records a DELETED equipment-history event and an administrator audit-log entry containing the IMEI/ICCID.

## Customer support notes
- Added a dedicated multi-entry customer support-note history.
- Categories: Technical Support, Billing Support, Customer Service, Sales, Installation, Collections, Account Management, and General.
- Every note automatically stores the logged-in employee user ID, employee name, employee email, and database timestamp.
- Notes display newest-first on the customer account and are included in the individual customer PDF report.
- Adding a note creates a CRM audit-log record.

## Compatibility
- Retains the v6.0 database filename (`isp_crm_v2.db`) and applies the new customer_notes table automatically at startup.
- Existing v6.0 customers, billing, equipment, Verizon carrier controls, documents, employee security, and `/api/v1` mobile API remain in place.
