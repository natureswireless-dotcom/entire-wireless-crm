# Entire Wireless ISP CRM v5.3

## Invoice editing
- Added an administrator-only **Edit Invoice** screen.
- Edit invoice issue date and due date.
- Edit existing line-item descriptions, quantities, and unit prices.
- Add additional line items while editing.
- Invoice subtotal is recalculated automatically from the saved line items.
- Invoice status is recalculated after an edit.
- The PDF statement is regenerated after an edit.
- Past-due notice state is reset after a material invoice edit so an outdated notice is not reused.
- Invoice edits are recorded in the audit log with the prior and new invoice summary.
- An edited invoice cannot be reduced below payments already posted to it.

## Invoice voiding
- Added administrator-only **Void Invoice** workflow with a required reason.
- Voiding is non-destructive: the invoice and line items remain in the CRM for audit/history purposes.
- Void invoices have a $0 collectible balance and are excluded from:
  - customer open balance calculations,
  - dashboard accounts receivable,
  - end-of-business past-due notices,
  - follow-up reminders,
  - nonpayment suspension calculations,
  - customer portal payment options.
- PDF statements for void invoices display a prominent **VOID** marking.
- Void date, user, and reason are stored on the invoice.
- Invoices with posted payments cannot be voided until the payment is corrected/reversed, preventing an inconsistent accounting record.
- Staff cannot post a new payment to a void invoice.

## Database upgrade
The upgrade is non-destructive. v5.3 automatically adds these invoice fields when missing:
- `voided_at`
- `voided_by`
- `void_reason`
- `edited_at`
- `edited_by`
