# Symphony of Summits — Full Stack

**Backend:** FastAPI + Supabase Postgres + UPI QR + WhatsApp
**Frontend:** Static HTML/CSS/JS site in `frontend/` — see `frontend/README.md`

---

# Backend

Production FastAPI backend for a Himalayan trek + expedition booking site.

## Stack
- **FastAPI** + async SQLAlchemy 2.0
- **PostgreSQL** on Supabase (schema in `schema.sql`)
- **UPI QR** payments (direct VPA; PayU webhook ready)
- **WhatsApp Cloud API** (Meta) for lead alerts + booking notifications
- **Brevo** for transactional email
- **Supabase Storage** (or Cloudflare R2) for media
- **Redis** for Celery / rate limit (optional)

## Project layout
```
symphonyofsummits/
├── app/
│   ├── main.py              FastAPI entrypoint
│   ├── config.py            pydantic settings from .env
│   ├── database.py          async SQLAlchemy engine
│   ├── security.py          JWT + password + auth deps
│   ├── models/
│   │   ├── enums.py         Python mirrors of PG enums
│   │   └── models.py        ORM classes
│   ├── schemas/
│   │   └── schemas.py       Pydantic DTOs
│   ├── services/
│   │   ├── booking_service.py    atomic seat reserve/confirm/release
│   │   ├── payu_service.py       UPI QR generation + PayU webhook verify
│   │   ├── whatsapp_service.py   Meta Cloud API client
│   │   ├── email_service.py      Brevo client
│   │   └── storage_service.py    Supabase Storage upload
│   └── routers/
│       ├── auth.py          signup/login/refresh/me
│       ├── trips.py         public catalog + batches
│       ├── bookings.py      create/list/cancel bookings
│       ├── payments.py      UPI QR + verify + admin approve
│       ├── leads.py         quote form → WhatsApp admin alert
│       ├── stories.py       blog + Instagram sidebar
│       ├── webhooks.py      WhatsApp inbound webhook
│       └── admin.py         trip/batch CRUD + dashboard
├── scripts/
│   ├── seed_data.py         seeds 8 real treks + batches
│   └── sync_instagram.py    hourly IG cache job
├── schema.sql               (from previous step — run in Supabase SQL editor)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Setup (10 minutes)
1. **Supabase** — create project (Mumbai region), paste `schema.sql` into SQL Editor, run.
2. **Env** — `cp .env.example .env` and fill in Supabase, PayU, WhatsApp credentials.
3. **Install** — `pip install -r requirements.txt`
4. **Seed** — `python -m scripts.seed_data`
5. **Run** — `uvicorn app.main:app --reload`
6. **Docs** — open http://localhost:8000/docs

## Payment flow (UPI QR, no gateway fees)
```
POST /payments/initiate  { booking_id, amount, is_advance:true }
     → returns qr_png_base64 + upi_uri (deep link for mobile)
Frontend shows QR + "Enter UTR after paying"
POST /payments/verify    { payment_id, upi_txn_ref }
     → status = processing, admin WhatsApp alert fires
Admin reviews bank statement
POST /payments/admin/{id}/approve
     → status = success, booking confirmed, user WhatsApp + email fire
```

## WhatsApp setup (Meta Cloud API — free up to 1k conversations/month)
1. Meta Business Suite → add WhatsApp Business
2. Approve 3 templates: `lead_received`, `booking_confirmed`, `payment_received`
3. Set webhook URL to `https://api.symphonyofsummits.com/api/v1/webhooks/whatsapp`
4. Put phone-number-id + token in `.env`

## Deploy
Vercel for the frontend (your `index.html` → Next.js later), Railway/Render/Fly.io for this API, Supabase for DB/Auth/Storage. Zero cost until you cross their free tiers.
