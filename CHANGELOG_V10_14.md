# v10.14 - CRM UI Cleanup / Tablet Service Retirement

- Removed the retired Tablet / iPad Services section from customer profiles.
- Removed Tablet/iPad services from customer API output.
- Retired Tablet/iPad WooCommerce service ingestion so obsolete tablet orders cannot recreate the removed service in CRM.
- Updated WooCommerce integration copy to list only Residential and Business service ordering.
- Preserved legacy tablet database tables/records non-destructively for historical compatibility; no database deletion or migration is performed.
- Preserves Verizon v10.13.2 functionality and all existing CRM data.
