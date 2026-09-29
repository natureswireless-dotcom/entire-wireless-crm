# Upgrade to v10.15

Deploy normally through the existing GitHub/Render workflow. No new environment variables are required. The existing persistent database remains in place; v10.15 creates only the additive `collection_letters` table. Existing SMTP settings are reused for collection-letter email delivery.
