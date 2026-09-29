# Upgrade to v10.2

Deploy over the same Render service and keep `/var/data/isp_crm_v2.db` unchanged.

Add these Render environment variables:
- `WOOCOMMERCE_ENABLED=1`
- `WOOCOMMERCE_STORE_URL=https://natureswireless.org`
- `WOOCOMMERCE_CONSUMER_KEY=<WooCommerce read/write consumer key>`
- `WOOCOMMERCE_CONSUMER_SECRET=<WooCommerce consumer secret>`
- `WOOCOMMERCE_WEBHOOK_SECRET=<your long random webhook secret>`
- `WOOCOMMERCE_ACTIVATION_FEE=25.00`

Create WooCommerce order-created and order-updated webhooks that both deliver to:
`https://crm.natureswireless.org/webhooks/woocommerce/order`

Use the exact same webhook secret value in WooCommerce and Render.

No existing CRM tables are replaced. The `woocommerce_orders` table and indexes are created automatically.
