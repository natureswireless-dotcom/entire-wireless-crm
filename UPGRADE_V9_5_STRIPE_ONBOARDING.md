# Upgrade — v9.5 Stripe Onboarding & Contract Billing Update

Deploy over the same Render service and persistent database. Database changes are additive and are applied automatically at startup.

No new Stripe credentials are required if invoice Stripe Checkout already works. Keep the existing `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` values in Render.

The Stripe webhook endpoint remains:

`https://crm.natureswireless.org/stripe/webhook`

For the new-customer workflow, select a service plan and choose **Create first monthly invoice and open secure Stripe Checkout**. After Stripe confirms payment, the CRM releases recurring billing and emails the payment confirmation using the existing SMTP configuration.
