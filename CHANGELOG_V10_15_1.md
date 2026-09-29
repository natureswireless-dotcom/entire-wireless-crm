# Entire Wireless ISP CRM v10.15.1 — Account Number Editing

- Administrators can edit an existing customer's account number from Edit Customer.
- Staff users continue to see the account number as read-only and cannot alter it through form submission.
- Validates uniqueness before saving.
- Accepts the standard 9-digit + 4-digit suffix format and legacy 9-digit account numbers.
- Account-number changes are captured by the existing customer-profile Audit Log entry.
- Customer database IDs and all related invoice/payment/document/history records remain unchanged; those records continue to resolve the customer by customer ID.
- Preserves v10.15 Internal Collections and all prior functionality.
