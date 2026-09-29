# Entire Wireless ISP CRM v9.5 — Modem Rental Promotion Update

## Added
- Customer-level **6 Months Free Modem Rental** promotion.
- Promotion can be selected when creating a subscriber or later from Edit Customer.
- Tracks free modem-rental billing cycles used and remaining.
- Recurring invoices during the promotion show the normal modem device lease and an equal promotional credit, producing a $0 device-rental charge.
- After six promotional billing cycles, the normal service-plan modem lease automatically begins on cycle 7.
- Customer page displays promotion status and remaining free billing cycles.
- Promotion progress is preserved when customer details or service plans are edited.
- Removing a promotion stops it; removing and later re-adding it intentionally starts a fresh six-cycle promotion.
- Zoho invoice synchronization converts the promotional lease/credit pair to a $0 device-lease line with the promotion noted, preserving the CRM invoice total while avoiding negative-rate compatibility issues.

## Billing behavior
For the standard Unlimited Internet plan ($85 service + $10 modem lease):
- Billing cycles 1–6: $85 total ($10 lease + $10 promotional credit).
- Billing cycle 7 onward: $95 total ($85 service + $10 modem lease).

The promotion counts successful recurring billing cycles, not merely elapsed calendar months, so the customer receives all six free lease billing cycles.
