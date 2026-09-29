# Entire Wireless ISP CRM v9.5 — Stripe Onboarding & Contract Billing Update

- Adds an optional **Initial Online Card Payment** workflow to New Subscriber creation.
- When selected, the CRM creates the customer's first recurring invoice and redirects to the existing secure Stripe Checkout integration.
- Card details remain on Stripe-hosted Checkout and are not stored in the CRM.
- Successful signed Stripe webhook confirmation posts the payment to the CRM, updates the invoice, synchronizes the payment to the active accounting provider, and sends the customer a payment-confirmation email with the updated statement attached when SMTP is configured.
- The first successful Stripe onboarding payment becomes the recurring billing anchor. Future invoices are generated monthly on that billing day (capped at day 28), emailed automatically, and stop when a fixed contract term ends (for example, after 36 months).
- Future recurring billing is held if the initial Stripe Checkout is not successfully paid.
- Existing invoice pages now include **Take Online Card Payment** for unpaid invoices when Stripe is configured.
- Monthly auto-generated invoices are now synchronized to the active accounting provider before email delivery.
- Preserves modem-rental promotion billing, including six free modem-rental billing cycles followed by the normal lease fee.
- Stripe webhook posting remains idempotent by Stripe Checkout Session ID.
