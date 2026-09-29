# Entire Wireless ISP CRM v10.4 — Customer Onboarding

- Added customer onboarding workflow: Order Received → Payment Confirmed → Agreement Pending/Signed → Equipment Assignment → Provisioning → Ready for Service → Active.
- WooCommerce paid orders automatically start onboarding and advance based on payment/agreement state.
- Added staff onboarding manager to each customer record with internal notes and stage controls.
- Added customer-facing onboarding progress to the customer portal.
- Preserved v10.3 automatic Service Order/Customer Information agreement generation.
- Additive SQLite schema only; existing `/var/data/isp_crm_v2.db` remains in place.
- Updated visible CRM version to v10.4 in the top-left header.
