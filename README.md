# Entire Wireless ISP CRM v5

Version 5 retains the reusable equipment workflow and adds DBA/legal-name consistency plus end-of-business past-due notice generation and delivery.

## Included

- Customer/subscriber accounts and service plans
- Modem IMEI and SIM ICCID inventory with unique assignment controls
- Equipment assignment and unassignment history
- One-click **Unassign & Reuse** controls on customer and inventory screens
- **Release All Equipment to Inventory** workflow for departing customers
- Released equipment automatically returns to `Available` inventory for reassignment
- Recurring invoicing, payments, A/R aging, statements and customer portal
- Statements identify the provider as Natures Wireless LLC d/b/a Entire Wireless
- Automatic formal PDF past-due notice at close of business on the invoice due date
- Configurable America/Chicago business close time and recurring follow-up reminder interval
- Stripe Checkout and signed webhook payment posting
- Telecom-style 3-page PDF statements modeled on the supplied Entire Wireless bill
- Verizon ThingSpace Connectivity Management integration scaffold
- Automatic nonpayment suspension after a configurable grace period (default: 3 days after due date)
- Automatic service restore after the customer's full open balance is paid
- Automatic $25 reconnect fee queued for the next statement after restoration
- Suspension exemptions and payment-arrangement holds
- Manual suspend/restore controls for staff
- Carrier action log with Verizon request IDs
- Safe dry-run mode enabled by default
- Staff roles, audit log and browser-based customer portal

## Verizon safety model

The package ships with `VERIZON_ENABLED=0` and `VERIZON_DRY_RUN=1`. In that state, no live carrier provisioning request is sent. The CRM simulates the action and records it in Carrier Control so the workflow can be tested first.

Before enabling live carrier automation, verify your assigned SIMs are Verizon lines, confirm the Verizon billing account name, obtain ThingSpace application key/secret and UWS credentials, and test with non-production lines.

Live mode requires:

- `VERIZON_ENABLED=1`
- `VERIZON_DRY_RUN=0`
- `VERIZON_ACCOUNT_NAME`
- `VERIZON_APP_KEY`
- `VERIZON_APP_SECRET`
- `VERIZON_UWS_USERNAME`
- `VERIZON_UWS_PASSWORD`

## Billing automation

v5 evaluates billing deadlines in the configured business timezone (default `America/Chicago`). At the configured close of business (default 5:00 PM), any invoice still unpaid on its due date is marked Past Due, a formal PDF notice is generated, and the notice is emailed once to the customer. Daily automation also sends later eligible past-due reminders and checks accounts for nonpayment suspension. The default threshold is 3 days after the invoice due date. Accounts marked as a suspension exemption or payment arrangement are skipped.

When a suspended customer's total open invoice balance reaches $0 after a posted payment or Stripe confirmation, the CRM requests Verizon restore service and queues a reconnect fee. The reconnect fee is included on the next automatically generated statement.

## Upgrade from v4

v5 intentionally continues to use the existing `isp_crm_v2.db` filename so your existing Render persistent disk can be upgraded in place. No destructive database migration is required for the new equipment release workflow.

Back up `/var/data/isp_crm_v2.db` before deploying a new version.

## Run locally

Windows: double-click `start_windows.bat`.

Mac/Linux: `./start_mac_linux.sh`

Then open `http://127.0.0.1:8000`.

## Verizon callback endpoint

v4 includes a callback receiver at `/verizon/callback/{VERIZON_CALLBACK_TOKEN}`. Set `VERIZON_CALLBACK_TOKEN` to a long random value in Render and use that callback URL when registering a Verizon CarrierService callback. Callback payloads with a matching Verizon request ID update the carrier action log to the final callback status.

## Customer documents and cancellations (v5.1)
Each Customer page now includes **Customer Documents** for signed agreements/contracts and related records. Uploaded files are stored under `DATA_DIR/customer_documents/<customer-id>/`; make sure `DATA_DIR` is backed by a persistent Render disk in production.

The **Customer Status** section can deactivate a cancelled subscriber without deleting history. Deactivation stops recurring billing by changing the customer/subscription to inactive/cancelled, disables customer portal access, records the cancellation reason/date, and can return assigned modem/SIM inventory to Available. Open invoices remain on the account for collection/payment history. Admins can reactivate an account if needed.

## Cancellation and SIM replacement billing (v5.3)
When an active customer is deactivated, staff can generate an Early Termination Fee invoice based on $20.00 for each whole month remaining in the customer's configured contract term. The calculation uses `contract_start` (or the subscription start date as a fallback) and `contract_months`, which defaults to 36. Staff can also indicate that equipment was not returned; this generates a separate $700.00 Unreturned Equipment Charge invoice and leaves assigned equipment tied to the cancelled customer with status `Unreturned`. If equipment was returned, it can instead be released to Available inventory during deactivation.

Active customer records also include an **Add $5.00 SIM Replacement Fee** action. Each use creates a pending charge that is automatically added as a line item on that customer's next normal monthly invoice. Pending SIM replacement fees are not invoiced separately and may be queued more than once when multiple replacement events occur.

Cancellation invoices are generated as normal CRM PDF statements and the CRM attempts to email them immediately using the configured SMTP settings. Open cancellation invoices remain in accounts receivable and continue through the normal past-due notice workflow even though the service account itself is inactive.

The fee defaults can be changed with `UNRETURNED_EQUIPMENT_FEE`, `EARLY_TERMINATION_MONTHLY_FEE`, and `SIM_REPLACEMENT_FEE` environment variables.

## v5.3 invoice controls
Administrators can edit an invoice from the invoice detail page. Issue date, due date, descriptions, quantities, and unit prices can be changed, and the CRM recalculates the total and regenerates the PDF statement.

Administrators can also void an unpaid invoice with a required reason. A void invoice is preserved in history but no longer contributes to accounts receivable, customer balances, past-due notices, suspension logic, or portal payment options. Invoices with posted payments must have those payments corrected before the invoice can be voided.


## v5.4 Charge Reversals
Administrators can reverse all or part of a billed charge from the invoice detail page. The original line remains on the invoice and a negative Charge Reversal adjustment is added with a required reason and audit trail. Pending charges that have not yet been billed can also be reversed from the customer page.

## v5.5 Employee Password Controls
Administrators can reset employee passwords from **Employees**. The administrator assigns a temporary password and the employee is required to replace it at the next login. New employee accounts are also required to change their initial password at first login.

Non-admin employee passwords expire after 90 days by default. Employees cannot reuse any of their last three passwords. These defaults can be configured with `PASSWORD_MAX_AGE_DAYS` and `PASSWORD_HISTORY_COUNT`. Administrator-role accounts are exempt from password expiration, but a manual administrator-issued reset still requires a password change on the next login.

## Employee credential lifecycle (v5.6)
Administrators can deactivate employee credentials when employment ends. Deactivation blocks future logins and is enforced on every protected CRM request, so an existing session cannot continue using the CRM after the account is disabled. The employee record is retained for audit history, together with the deactivation date, administrator, and reason. The current signed-in administrator and the last active administrator are protected from accidental deactivation. Reactivated employees must change their password at next login.

## v7.0 iOS companion app
The `iOS/EntireWirelessCRM` folder contains a native SwiftUI iPhone project. The website CRM remains the system of record. Deploy this v6.0 backend to the same Render service/persistent database, then configure the iOS app with that public HTTPS URL. Employee login/deactivation and password policies are enforced server-side for both web and iOS access.


## Version 7 additions
See `CHANGELOG_V7.md` for printable inventory/customer reports, permanent retired-equipment deletion, and time-stamped employee-attributed customer support notes.

## QuickBooks Online — v8.0
Administrators can connect the CRM to QuickBooks Online from **QuickBooks** in the CRM navigation. The integration uses Intuit OAuth 2.0 and the QuickBooks Online Accounting API. New subscribers, invoices, and payments synchronize automatically after connection. Sync failures are recorded and can be retried from the integration center. See `UPGRADE_V8.md` for sandbox-first deployment instructions.
