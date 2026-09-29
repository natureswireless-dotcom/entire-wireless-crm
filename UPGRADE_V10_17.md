# Upgrade to v10.17

Deploy normally over the existing CRM application. Keep the existing persistent database at `/var/data/isp_crm_v2.db`.

The database update is additive. On startup the CRM creates the referral tables, adds the nullable `customers.referral_code` column if needed, and assigns referral codes to existing customers. No existing customer, invoice, equipment, payment, collection, WooCommerce, or Verizon data is reset.

No new Render environment variables are required.

Referral rewards are intentionally staff-qualified. Recording a referral does not award a free month until staff selects **Qualify & Award 1 Month**. During recurring billing, the existing modem-rental promotion is consumed first. Referral rewards begin automatically afterward.
