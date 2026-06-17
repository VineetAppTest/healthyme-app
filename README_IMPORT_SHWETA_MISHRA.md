# One-time backend import - Shweta Mishra

This build adds a one-time import for the offline LAF PDF and NSP Excel received for Shweta Mishra.

## What it imports

- Member login/authorization record: `shwemish@gmail.com`
- Active member profile
- LAF responses from scanned PDF
- NSP Page 1 responses from Excel blue response column
- NSP Page 2 responses from Excel blue response column
- Admin subforms: Digestive, Intestinal, Immune, Glandular, Musculoskeletal
- Initial assessment instance marked as submitted/review required

## Fastest way to run in deployed Streamlit backend

1. Deploy this build.
2. Login as admin.
3. Open the page: `32_Admin_One_Time_Import_Shweta` from Streamlit pages/sidebar, or direct page URL if available.
4. Click **Run one-time import for Shweta Mishra**.
5. Check Admin Review Queue / Evaluation Status for Shweta Mishra.

## Command-line fallback

From the app root folder:

```bash
python scripts/import_shweta_mishra_backend.py
```

Note: Command-line import will write to Supabase only if `SUPABASE_URL` and service/anon key are available as environment variables. In Streamlit Cloud, using the admin page is safer because app secrets are already available to the runtime.
