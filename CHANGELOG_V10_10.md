# v10.10 — Service Plans Catalog Repair
This release fixes the live Service Plans screen.
- Shows exactly four active current plans:
  - Residential 5G Internet 100 Mbps — $85 — Plan 59142
  - Residential 5G Internet 200 Mbps — $105 — Plan 59145
  - Business 5G Internet 100 Mbps — $95 — Plan 59143
  - Business 5G Internet 200 Mbps — $115 — Plan 59146
- All four include unlimited data.
- Removes Tablet/iPad and old generic Unlimited Internet / Business Internet from the visible active catalog.
- Obsolete rows are deactivated instead of physically deleted so historical subscriptions/invoices remain referentially safe.
- Stops obsolete Tablet/iPad plans from being seeded again on startup.
- Service Plans screen now lists active plans only.
- Preserves v10.9/v10.8 invoice redesign, customers, documents, billing, lead API, and history.
