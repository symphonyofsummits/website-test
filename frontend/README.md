# Symphony of Summits — Frontend

Static HTML/CSS/JS site that talks to the FastAPI backend.

## Run locally

```bash
# From the frontend/ folder
python -m http.server 5173
# or
npx serve .
```

Open **http://localhost:5173**

The site talks to the backend at `http://127.0.0.1:8000/api/v1` by default (see `window.SOS_CONFIG` in `index.html`).

## Edit before going live

In `index.html`, update the WhatsApp number:

```html
<script>
  window.SOS_CONFIG = {
    apiBase: "https://api.symphonyofsummits.com/api/v1",
    whatsapp: "919XXXXXXXXX"   // ← your actual WhatsApp
  };
</script>
```

Also update the `wa.me/...` link in the floating WhatsApp button and footer.

## Sections included

- **Nav** with Treks, Expeditions, Pilgrimage, Packages, Rent Gear, Stories, About
- **Hero** with cinematic photographic background
- **Quick search bar** below hero
- **Treks grid** with category chips (Indian/International/Easy/Moderate/Difficult/Adventure/Hill Stations)
- **Destinations** (Himachal, Uttarakhand, Sikkim, Ladakh)
- **Expeditions & Peaks** section (Indian + International)
- **Pilgrimage** section (Char Dham, Kailash Mansarovar)
- **Packages** section with filter chips (National/International/Honeymoon/Family/Weekend)
- **Rent Gear** grid (8 common items)
- **Stories** feed
- **Quotation form** (open modal + inline on page)
- **About** with stats
- **Footer** with policies, trust badges, disclaimers (TrekTheHimalayas-style)
- **Instagram right sidebar** rail (fixed, auto-fills from API)
- **Floating WhatsApp button** (bottom-right, pulse animation)
- **UPI QR payment modal** triggered during booking

## Deploy

### Vercel
```bash
# Push this folder to GitHub, then on vercel.com
# → New Project → import repo → set Root Directory to `frontend/`
# → Framework Preset: Other
# → Deploy
```

### Cloudflare Pages
```bash
# Same flow — connect GitHub, set build output to this folder
```

Both are free, and you get HTTPS + custom domain for `symphonyofsummits.com` out of the box.
