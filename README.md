
# Family Medical Record App

A secure web app for families to record and view health information. The initial MVP focuses on fast, reliable document storage while keeping the data model intentionally small and portable.

## MVP Scope (Slimmed Down)

### Core capabilities
- **Auth**: email + password sign inss
- **Family members**: add and manage member profiles
- **Documents**: upload PDFs or images (prescriptions/lab reports)
- **Metadata**: treated-for condition + date + uploader
- **Access control**: admin (manage) vs viewer (read-only)

### Reduced data model
- **users**: id, email, password_hash, created_at
- **family_members**: id, full_name, dob, created_by, created_at
- **documents**: id, member_id, uploaded_by, doc_date, condition, description, storage_key, file_name, mime_type, created_at

## Database Portability (Supabase → Postgres or other providers)

To keep switching fast and low-risk:
- **SQLAlchemy + environment-based config** for the DB URL (e.g., `DATABASE_URL`).
- **No Supabase-specific SQL** in data access code.
- **Storage adapter** is separate from DB (Supabase Storage is just one implementation).
- **Provider-agnostic schema** kept minimal and managed directly by SQLAlchemy for the MVP.

This allows swapping from Supabase Postgres to another managed Postgres quickly by changing the connection string and storage adapter configuration.

## Quick Start (Local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

For local development without Supabase, set `STORAGE_BACKEND=local` and `LOCAL_STORAGE_PATH=./uploads`.

## Storage Portability (Supabase → S3/GCS/etc.)

Uploads are stored in object storage, not in the database. The database stores the `storage_key` and metadata only. The app uses a `StorageAdapter` interface so you can switch providers by changing configuration instead of rewriting features.

### MVP default
- Supabase Storage with a private bucket and signed URLs for download.

### Storage configuration (example)
- `STORAGE_BACKEND=supabase` or `local`
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_BUCKET`
- `LOCAL_STORAGE_PATH` (for local/dev)

## Infrastructure (Minimal)

- **App host**: VM or container platform to run Streamlit
- **Database**: Postgres (Supabase or any provider)
- **Storage**: Supabase Storage or another object store (S3/GCS)
- **Config**: environment variables for DB + storage

## Upcoming Releases (Planned Scope)

These are **not** part of MVP but are in the roadmap:

- Member profiles (expanded)
- Prescriptions (treated-for + date range)
- Allergies & reactions
- Vitals (BP, HR, weight, etc.)
- Immunizations
- Document uploads (PDFs/images) — already in MVP, will be expanded
- Fast emergency summary view

Target: support 10–15 family members initially, with room to expand.

## Next Steps (Optional)

If you'd like, we can flesh out any of the following next:
- SQLAlchemy models and migrations
- Streamlit app skeleton (login + docs + upload)
- Supabase Storage adapter implementation
- Access-control rules (admin vs viewer)
