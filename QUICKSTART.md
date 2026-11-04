# Symphony of Summits — Quick Start

Get the backend running in **10 minutes**.

## Prerequisites
- Python 3.11 or 3.12 installed
- A Supabase account (free): https://supabase.com

---

## Step 1 — Install

```powershell
cd symphonyofsummits
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## Step 2 — Create `.env`

```powershell
copy .env.example .env
```

Open `.env` in VS Code / Notepad. You MUST fill these 7:

| Variable | Where to get it |
|---|---|
| `SECRET_KEY` | Run: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | Supabase → Settings → Database → Connection string (URI, Session mode). Prefix with `postgresql+asyncpg://` |
| `DATABASE_URL_SYNC` | Same URI, prefix `postgresql://` |
| `SUPABASE_URL` | Supabase → Settings → API → Project URL |
| `SUPABASE_ANON_KEY` | Supabase → Settings → API → anon public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Settings → API → service_role secret key |
| `SUPABASE_JWT_SECRET` | Supabase → Settings → JWT → Reveal secret (or placeholder) |

Save `.env`.

---

## Step 3 — Run `schema.sql` on Supabase

1. Open: `https://supabase.com/dashboard/project/YOUR-PROJECT-REF/sql/new`
2. Open `schema.sql` from this folder in VS Code
3. Copy all → paste into Supabase SQL editor
4. Click **Run** (bottom right)
5. Should say "Success. No rows returned"

---

## Step 4 — Boot the server

```powershell
uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

## Step 5 — Open the docs

Browser: **http://127.0.0.1:8000/docs**

You should see Swagger UI with every endpoint listed.

---

## Step 6 — Seed real trek data (optional)

```powershell
python -m scripts.seed_data
```

This creates 8 real treks (Hampta, Goechala, EBC, Char Dham, Kilimanjaro…) with 4 upcoming batches each + an admin user.

---

## Common errors

### `ValidationError: Field required`
A required field is missing in `.env`. The error message names which one. Fill it in.

### `could not translate host name` / `password authentication failed`
Database URL malformed or password wrong. Reset the DB password in Supabase (Settings → Database → Reset password) and re-copy the connection string.

### `relation "trips" does not exist`
You skipped Step 3 — the schema hasn't been loaded into Supabase yet.

---

## What's next
- Set up Brevo for emails: https://onboarding.brevo.com/account/register (2 min)
- Set up WhatsApp Cloud API: https://developers.facebook.com (requires Meta Business verification, 1–3 days)
- Register your domain: `symphonyofsummits.com`
- Deploy frontend to Vercel + backend to Render / Railway
