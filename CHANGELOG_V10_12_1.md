# v10.12.1 – Verizon Environment Read Fix

- Reads Verizon credentials from the process environment at test/request time instead of relying only on module-import values.
- Trims accidental surrounding whitespace.
- Reports the exact missing environment variable name without exposing any secret value.
- Preserves v10.12 safe connection test and no-ICCID skip behavior.
- No database migration.
