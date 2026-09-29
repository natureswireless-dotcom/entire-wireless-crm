# Entire Wireless ISP CRM v10.1 — Customer Portal Messaging

Added secure CRM-native customer messaging.

Customer Portal:
- New Messages link in the portal header.
- Customers can start a new message conversation with a subject and message.
- Messages are automatically tied to the authenticated customer's CRM customer ID/account.
- Customers can view complete conversation history and replies from staff.
- Customers can reply to open conversations.
- Closed conversations remain visible but cannot be replied to.

Admin CRM:
- New Customer Messages menu.
- Inbox shows all portal conversations, customer/account, status, last activity, and unread customer-message count.
- Staff can open a thread, review the full conversation, reply from the CRM, close it, or reopen it.
- Staff replies immediately appear in that customer's portal.
- Customer profiles include a shortcut to Customer Messages.

Data:
- Adds customer_message_threads and customer_messages tables plus indexes.
- Additive database migration only; existing CRM data is preserved.
- Sales & Growth, invoice design, Stripe, Zoho, customer classifications, account suffixes, CSV export, and all v10.0 features are retained.
