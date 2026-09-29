# Entire Wireless ISP CRM v10.7

- Adds authenticated `POST /api/website-leads` JSON endpoint for the WordPress availability funnel.
- Returns a confirmed CRM lead ID before the website reports success.
- Preserves duplicate detection, contact consent, lead tasks, and source attribution.
- Supports `WEBSITE_LEAD_API_KEY` environment override; packaged private key remains compatible with WordPress v3.4.9.
