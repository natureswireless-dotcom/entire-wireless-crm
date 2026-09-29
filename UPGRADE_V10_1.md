# Upgrade to v10.1

Deploy over the same Render service and keep the existing persistent database at /var/data/isp_crm_v2.db.

No new environment variables are required. The messaging tables and indexes are created automatically on startup.

After deployment:
1. Confirm Customer Messages appears in the CRM left navigation.
2. Sign in to a test customer portal and send a message.
3. Open Customer Messages in the CRM and reply.
4. Refresh the customer portal and confirm the staff reply appears in the conversation.

Do not reset or replace the persistent database.
