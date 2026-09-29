# Entire Wireless ISP CRM v10.2 — WooCommerce Ordering Integration

- Adds a dedicated WooCommerce integration dashboard in the admin CRM.
- Adds signed WooCommerce order webhook endpoint: `/webhooks/woocommerce/order`.
- Verifies `X-WC-Webhook-Signature` using HMAC-SHA256 and `WOOCOMMERCE_WEBHOOK_SECRET`.
- Paid Residential orders map to CRM `Unlimited Internet`; paid Business orders map to CRM `Business Internet`.
- Creates the CRM customer with the correct account-number suffix: Residential `-0001`, Business `-0002`.
- Uses checkout billing/service address, email, phone, and company data.
- Creates/updates the active CRM subscription from the CRM plan table.
- Creates a first CRM invoice from live CRM plan pricing plus modem lease and the configured activation fee.
- Records the WooCommerce payment against the CRM invoice.
- Syncs customer/invoice/payment to the active accounting provider (Zoho when configured).
- Stores WooCommerce order ID, transaction ID, status, sync status, payload, CRM customer/invoice/payment links, and errors.
- Idempotent processing prevents duplicate payments when WooCommerce retries a webhook.
- Adds manual Retry from the WooCommerce integration screen using WooCommerce REST API credentials.
- Preserves Customer Messages, Sales & Growth, Stripe, Zoho, invoice design, inventory, and all prior CRM features.
