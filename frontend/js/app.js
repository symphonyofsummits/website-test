/* =========================================================
   Symphony of Summits — site interactions
   ========================================================= */

// Nav scroll state
const nav = document.getElementById("nav");
if (nav) {
  window.addEventListener("scroll", () => nav.classList.toggle("scrolled", scrollY > 40));
}

/* ---------- TOAST ---------- */
function toast(msg) {
  const t = document.getElementById("toast");
  if (!t) return alert(msg);
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 3500);
}
window.toast = toast;

/* ---------- QUOTE MODAL ---------- */
function openQuote(subject) {
  const modal = document.getElementById("modal");
  if (!modal) return;
  modal.classList.add("open");
  if (subject) {
    const ta = modal.querySelector("textarea");
    if (ta) ta.placeholder = `Regarding ${subject} — tell us your dates, group size and requirements`;
  }
  modal.dataset.subject = subject || "";
}
function closeQuote() {
  document.getElementById("modal").classList.remove("open");
}
window.openQuote = openQuote;
window.closeQuote = closeQuote;

/* ---------- QUOTE FORM SUBMIT ---------- */
async function submitQuote(e) {
  e.preventDefault();
  const form = e.target;
  const inputs = form.querySelectorAll("input, select, textarea");
  const payload = {
    full_name: inputs[0].value,
    email: inputs[1].value,
    phone: inputs[2].value,
    city: inputs[3] ? inputs[3].value : null,
    preferred_date: inputs[4] && inputs[4].type === "date" ? inputs[4].value || null : null,
    travellers_count: inputs[5] && inputs[5].type === "number" ? parseInt(inputs[5].value) || null : null,
    message: form.querySelector("textarea").value,
    source: "quote_modal",
  };
  const modal = document.getElementById("modal");
  if (modal && modal.dataset.subject) {
    payload.message = `[${modal.dataset.subject}] ${payload.message}`;
  }
  try {
    await window.SOS.Leads.create(payload);
    form.reset();
    closeQuote();
    toast("Thank you! We'll get back to you on WhatsApp shortly.");
  } catch (err) {
    toast("Sorry — " + err.message);
  }
}
window.submitQuote = submitQuote;

/* ---------- LOCATION BUTTON ---------- */
const locBtn = document.getElementById("locationBtn");
if (locBtn) {
  locBtn.onclick = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        () => toast("Location enabled — we'll personalize recommendations."),
        () => toast("Location permission not granted."),
      );
    } else toast("Location is not supported in this browser.");
  };
}

/* ---------- MODAL BACKDROP CLICK ---------- */
const modal = document.getElementById("modal");
if (modal) {
  modal.addEventListener("click", (e) => { if (e.target.id === "modal") closeQuote(); });
}

/* ---------- LOAD TRIPS FROM API ---------- */
async function loadFeaturedTrips() {
  const grid = document.getElementById("tripsGrid");
  if (!grid) return;
  try {
    const trips = await window.SOS.Trips.list({ featured: true, per_page: 6 });
    if (!trips || !trips.length) return; // keep static fallback
    grid.innerHTML = trips.map(tripCardHTML).join("");
  } catch (err) {
    console.warn("Falling back to static trip cards:", err.message);
  }
}

function tripCardHTML(t) {
  const diff = (t.difficulty || "").toUpperCase();
  const img = t.cover_image || "https://images.unsplash.com/photo-1551632811-561732d1e306?auto=format&fit=crop&w=1000&q=85";
  return `
    <article class="card" data-slug="${t.slug}">
      <div class="trip-img" style="background-image:url('${img}')">
        ${diff ? `<span class="badge">${diff}</span>` : ""}
      </div>
      <div class="card-body">
        <h3>${t.title}</h3>
        <div class="meta">
          <span>${t.region || t.country || ""}</span>
          <span>${t.duration_days} Days</span>
          ${t.max_altitude_m ? `<span>${t.max_altitude_m.toLocaleString()}m</span>` : ""}
        </div>
        <p>${t.subtitle || ""}</p>
        <div class="price">
          <div>
            <strong>From ₹${Number(t.base_price).toLocaleString("en-IN")}</strong>
            <small>per person</small>
          </div>
          <button class="arrow" onclick="openQuote('${t.title.replace(/'/g, "\\'")}')">→</button>
        </div>
      </div>
    </article>`;
}

/* ---------- CATEGORY CHIPS FILTER ---------- */
function wireChips() {
  const chips = document.querySelectorAll(".chip");
  chips.forEach((c) => {
    c.addEventListener("click", async () => {
      chips.forEach((x) => x.classList.remove("active"));
      c.classList.add("active");
      const filter = c.dataset.filter || {};
      const grid = document.getElementById("tripsGrid");
      try {
        const params = {};
        if (c.dataset.category) params.category = c.dataset.category;
        if (c.dataset.difficulty) params.difficulty = c.dataset.difficulty;
        if (c.dataset.scope) params.scope = c.dataset.scope;
        const trips = await window.SOS.Trips.list(params);
        if (!trips.length) {
          grid.innerHTML = `<p style="grid-column:1/-1;text-align:center;color:var(--muted)">No trips found for this filter.</p>`;
        } else {
          grid.innerHTML = trips.map(tripCardHTML).join("");
        }
      } catch (err) {
        console.warn("Filter failed:", err.message);
      }
    });
  });
}

/* ---------- INSTAGRAM FEED ---------- */
async function loadInstagram() {
  const rail = document.getElementById("igRail");
  if (!rail) return;
  try {
    const posts = await window.SOS.Instagram.feed(4);
    if (!posts || !posts.length) {
      rail.style.display = "none";
      return;
    }
    const container = rail.querySelector(".ig-posts");
    container.innerHTML = posts
      .map((p) => `<a href="${p.permalink || "#"}" target="_blank">
        <img class="ig-thumb" src="${p.thumbnail_url || p.media_url}" alt="instagram">
      </a>`)
      .join("");
  } catch {
    rail.style.display = "none";
  }
}

/* ---------- NEWSLETTER FORM (footer) ---------- */
function wireNewsletter() {
  const form = document.getElementById("newsletterForm");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = form.querySelector("input").value.trim();
    if (!email) return;
    try {
      await window.SOS.Leads.subscribeNewsletter(email);
      form.reset();
      toast("Subscribed. Watch your inbox for trail stories.");
    } catch (err) {
      toast("Subscription failed — " + err.message);
    }
  });
}

/* ---------- IG RAIL CLOSE ---------- */
document.addEventListener("click", (e) => {
  if (e.target.classList && e.target.classList.contains("ig-close")) {
    document.getElementById("igRail").style.display = "none";
  }
});

/* ---------- INIT ---------- */
document.addEventListener("DOMContentLoaded", () => {
  loadFeaturedTrips();
  wireChips();
  loadInstagram();
  wireNewsletter();
});
