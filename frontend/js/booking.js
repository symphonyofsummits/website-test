/* =========================================================
   Symphony of Summits — booking + UPI QR payment flow
   This is a self-contained module. Call openBookingFlow({tripSlug, batchId})
   to kick off the full flow.
   ========================================================= */

async function openBookingFlow({ tripSlug, batchId, trippedCount = 1 }) {
  // Requires login
  if (!window.SOS.authStore.get()) {
    toast("Please login first to book a trek");
    openLoginModal();
    return;
  }
  try {
    const payload = {
      batch_id: batchId,
      travellers: [{
        is_lead: true,
        full_name: prompt("Lead traveller name") || "Guest",
        age: parseInt(prompt("Age") || "25", 10),
      }],
    };
    const booking = await window.SOS.Bookings.create(payload);
    toast(`Booking created: ${booking.booking_code}`);
    openPaymentQR(booking);
  } catch (err) {
    toast("Booking failed: " + err.message);
  }
}
window.openBookingFlow = openBookingFlow;

/* ---------- PAYMENT QR MODAL ---------- */
async function openPaymentQR(booking) {
  try {
    const qr = await window.SOS.Payments.initiate({
      booking_id: booking.id,
      amount: booking.total_amount,
      is_advance: true,
      method: "upi_qr",
    });

    const html = `
      <div class="modal open" id="qrModal">
        <div class="modal-card qr-modal">
          <button class="close" onclick="document.getElementById('qrModal').remove()">×</button>
          <div class="kicker">Scan to pay via UPI</div>
          <div class="qr-amount">₹${Number(qr.amount).toLocaleString("en-IN")}</div>
          <img class="qr-img" src="data:image/png;base64,${qr.qr_png_base64}" alt="UPI QR">
          <div class="vpa">${qr.upi_vpa}</div>
          <div class="instructions">
            <b>How to pay:</b><br>
            1. Open any UPI app (GPay, PhonePe, Paytm, BHIM)<br>
            2. Scan the QR code above<br>
            3. Pay ₹${Number(qr.amount).toLocaleString("en-IN")}<br>
            4. Enter the 12-digit UTR / Transaction ID below<br>
            5. We'll verify and confirm within 2 hours
          </div>
          <input class="utr-input" id="utrInput" placeholder="Enter 12-digit UTR number" maxlength="22">
          <button class="btn blue" style="width:100%;margin-top:14px"
                  onclick="submitUTR('${qr.payment_id}')">Confirm Payment</button>
          <p style="font-size:11px;color:var(--muted);margin-top:16px">
            Transaction ref: ${qr.txn_ref} · Expires in 15 minutes
          </p>
        </div>
      </div>`;
    document.body.insertAdjacentHTML("beforeend", html);
  } catch (err) {
    toast("Could not generate QR: " + err.message);
  }
}
window.openPaymentQR = openPaymentQR;

async function submitUTR(paymentId) {
  const utr = document.getElementById("utrInput").value.trim();
  if (utr.length < 6) {
    toast("Please enter a valid UTR");
    return;
  }
  try {
    await window.SOS.Payments.verify({ payment_id: paymentId, upi_txn_ref: utr });
    document.getElementById("qrModal").remove();
    toast("Payment submitted. We'll confirm within 2 hours via WhatsApp.");
  } catch (err) {
    toast("Verification failed: " + err.message);
  }
}
window.submitUTR = submitUTR;

/* ---------- SIMPLE LOGIN MODAL ---------- */
function openLoginModal() {
  const html = `
    <div class="modal open" id="loginModal">
      <div class="modal-card">
        <button class="close" onclick="document.getElementById('loginModal').remove()">×</button>
        <div class="kicker">Welcome back</div>
        <h2>Login or Sign Up</h2>
        <p style="color:var(--muted);margin:10px 0 20px">Quick 30-second signup to book your trek.</p>
        <form class="form" onsubmit="return submitLogin(event)">
          <input class="full" name="full_name" placeholder="Full name (new users only)" style="grid-column:1/-1">
          <input class="full" type="email" name="email" placeholder="Email" required style="grid-column:1/-1">
          <input class="full" name="phone" placeholder="Phone (+91)" style="grid-column:1/-1">
          <input class="full" type="password" name="password" placeholder="Password" required style="grid-column:1/-1">
          <button class="btn full">Continue</button>
        </form>
      </div>
    </div>`;
  document.body.insertAdjacentHTML("beforeend", html);
}
window.openLoginModal = openLoginModal;

async function submitLogin(e) {
  e.preventDefault();
  const f = e.target;
  const email = f.email.value;
  const password = f.password.value;
  try {
    // try login first
    let tokens;
    try {
      tokens = await window.SOS.Auth.login({ email, password });
    } catch {
      // fallback to signup
      tokens = await window.SOS.Auth.signup({
        email,
        password,
        full_name: f.full_name.value || email.split("@")[0],
        phone: f.phone.value || "+919999999999",
      });
    }
    window.SOS.authStore.set(tokens.access_token);
    document.getElementById("loginModal").remove();
    toast("Logged in successfully");
  } catch (err) {
    toast("Login failed: " + err.message);
  }
  return false;
}
window.submitLogin = submitLogin;
