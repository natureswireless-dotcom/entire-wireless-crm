# Entire Wireless ISP CRM v6.0

## Native iOS companion support
- Added `/api/v1` mobile API backed by the same CRM SQLite database and business logic as the website.
- Added secure employee API login with 30-day bearer tokens stored server-side only as SHA-256 hashes.
- Every protected mobile request re-validates the employee's active status, so terminated/deactivated employees immediately lose mobile access.
- Mobile authentication honors first-login forced password changes, non-admin 90-day password expiration, and last-3-password reuse prevention.
- Added mobile endpoints for dashboard metrics, customers, customer details, invoices, modem/SIM inventory, current employee profile, admin employee list, password changes, and logout.
- Added API-aware 401 and 428 JSON responses while preserving existing browser redirects for the website CRM.

## iOS project
- Added a native SwiftUI iPhone project under `iOS/EntireWirelessCRM`.
- Dashboard, Customers, Invoices, Inventory, Account, secure login, password-change flow, pull-to-refresh, CRM server configuration, and Keychain token storage.
- The iPhone app stores no independent CRM database; live data comes from the website CRM API.
