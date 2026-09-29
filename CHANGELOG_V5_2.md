# Entire Wireless ISP CRM v5.2

- Added cancellation charge generation to customer deactivation.
- Added Early Termination Fee calculation at $20.00 per whole month remaining in the configured contract term (36 months by default).
- Added separate $700.00 Unreturned Equipment Charge invoice option.
- Unreturned equipment is retained on the cancelled customer record and marked `Unreturned` rather than returned to Available inventory.
- Returned equipment can still be released to Available inventory during cancellation.
- Cancellation invoices generate PDF statements and attempt immediate SMTP delivery.
- Added $5.00 SIM Card Replacement Fee action for active customers.
- SIM replacement fees are queued in pending charges and roll into the customer's next monthly recurring invoice.
- Added configurable fee environment variables.
- Bumped application version to v5.2.
