# Upgrade to v9.6

Deploy over the existing Entire Wireless CRM service and keep the same persistent DATA_DIR/database.

The upgrade is additive:
- Adds `customers.customer_type` with a default of `Residential`.
- Existing customers are retained and classified Residential until edited.
- Adds the `Business Internet` plan only if it does not already exist.
- No Zoho, Stripe, QuickBooks, Verizon, or other environment-variable changes are required.

After deployment, review existing company accounts and change Customer Type to Business where appropriate.
