# Entire Wireless ISP CRM v5

## Legal / DBA identity
- Entire Wireless is now presented as `Natures Wireless LLC d/b/a Entire Wireless` throughout generated billing documents and relevant CRM/carrier screens.
- Added `COMPANY_DBA` and `COMPANY_DISPLAY_LEGAL` configuration values.
- Added `VERIZON_ACCOUNT_DISPLAY_NAME` for the business identity shown inside Carrier Control.
- `VERIZON_ACCOUNT_NAME` remains the exact Verizon-assigned API/billing account name and should not be changed unless Verizon confirms the account name change.

## Billing and collections automation
- Added automatic end-of-business past-due processing.
- Default business timezone: `America/Chicago`.
- Default business close: 5:00 PM (`BUSINESS_CLOSE_HOUR=17`).
- If an invoice remains unpaid at/after close of business on its due date, v5 marks it Past Due, generates a formal PDF Past Due Notice, and emails it to the customer's account email.
- Each invoice receives the initial EOD past-due notice only once (`eod_notice_at`).
- Follow-up past-due reminders remain separate and default to every 7 days.
- Added a Billing Center control to manually run due-date notices when needed.
- Existing configurable nonpayment suspension, payment-arrangement exemptions, restore workflow, and reconnect-fee workflow are retained.

## Database upgrade
v5 automatically adds these non-destructive columns to the existing invoices table:
- `eod_notice_at`
- `eod_notice_pdf`

The package intentionally continues to use `isp_crm_v2.db` so an existing Render persistent disk can be upgraded in place. Back up the database before deployment.

## v5.1 customer records enhancement
- Added a Customer Documents section to each subscriber record.
- Upload/download PDF, DOC, DOCX, PNG, JPG, and JPEG customer agreements and supporting documents.
- Files are stored under the configured persistent DATA_DIR and indexed in the CRM database.
- Added document type, notes, upload timestamp, uploader, and audit history.
- Added customer deactivation with cancellation reason and timestamp.
- Deactivation disables portal access and cancels the active subscription so recurring billing stops.
- Optional equipment release during deactivation returns assigned modems and SIMs to Available inventory while preserving assignment history.
- Existing invoices, payments, documents, and account history remain intact after deactivation.
- Added admin reactivation for accidental/temporary deactivation; equipment must be reassigned separately.
