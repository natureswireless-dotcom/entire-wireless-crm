# Entire Wireless ISP CRM v5.5

## Employee Password Security
- Administrators can reset an employee password from the Employees section by assigning a temporary password.
- Admin password resets force the employee to choose a new password at the next login.
- Newly created employee accounts are forced to change the temporary/initial password at first login.
- Non-admin employee passwords expire every 90 days by default and access is blocked until the password is changed.
- The 90-day expiration check is enforced on login and on authenticated CRM requests, so a long-running session cannot bypass expiration.
- Administrator-role accounts are exempt from the 90-day expiration requirement.
- Employees cannot reuse any of their last three passwords.
- Password changes and administrator resets are recorded in the audit log.
- Password history stores only password hashes, never plaintext passwords.

## Configuration
- `PASSWORD_MAX_AGE_DAYS=90`
- `PASSWORD_HISTORY_COUNT=3`
