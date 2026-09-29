# Entire Wireless ISP CRM v5.4

- Added admin-only full and partial charge reversals for invoice line items.
- Reversals post a negative adjustment instead of deleting the original charge.
- Reversal amount, reason, user, timestamp, original item, and reversal item are retained.
- Invoice totals, balances, statuses, PDFs, and collection calculations update after reversal.
- Added reversal/removal of queued pending charges before they reach the next monthly invoice.
- Added accounting protections against over-reversing or reducing an invoice below posted payments.
