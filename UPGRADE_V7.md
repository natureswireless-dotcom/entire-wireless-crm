# Upgrade Entire Wireless ISP CRM v6.0 to v7.0

1. Back up the production Render persistent-disk database (`/var/data/isp_crm_v2.db`) before deploying.
2. Replace the application files in the existing GitHub repository with the contents of this v7 package. Do not create a new Render service.
3. Commit and push to the same branch Render currently deploys.
4. Allow Render to redeploy the existing service.
5. Sign in as an administrator and verify Reports, Modems / IMEI, SIM Cards / ICCID, and a customer record.
6. The `customer_notes` table is created automatically. No new Render environment variables are required for these v7 features.

Permanent deletion is administrator-only and only works on unassigned equipment. Use Unassign & Reuse first if an IMEI/ICCID is still assigned to a customer.
