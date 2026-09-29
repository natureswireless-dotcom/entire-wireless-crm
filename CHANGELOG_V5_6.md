# Entire Wireless ISP CRM v5.6

## Employee credential deactivation
- Administrators can deactivate an employee credential from the Employees section and must enter a reason.
- Disabled employees are blocked from login immediately.
- Protected CRM requests re-check the employee active status, so an already signed-in terminated employee is rejected on their next CRM request and their session is cleared.
- The employee record, password history, and audit history are preserved rather than deleted.
- Deactivation stores the timestamp, administrator email, and reason.
- The currently signed-in administrator cannot deactivate their own account.
- The last active administrator account cannot be deactivated.
- Administrators may reactivate a disabled credential; reactivation forces a password change at the employee's next login.
- Password reset controls are unavailable while an employee credential is disabled.
