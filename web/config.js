// Public browser config. The Supabase publishable key is meant to be public; row-level security protects the data.
window.RUKO_CONFIG = {
  supabaseUrl: "https://izxqlbipvrtnsvpwekaw.supabase.co",
  supabaseKey: "sb_publishable_M8we6sPJuWsmIZOZuKQbrQ_pivd7C1I",
};

// Insert a row through Supabase's REST API (used by pages that don't load the full SDK).
async function sbInsert(table, row) {
  const c = window.RUKO_CONFIG;
  const r = await fetch(`${c.supabaseUrl}/rest/v1/${table}`, {
    method: "POST",
    headers: { apikey: c.supabaseKey, Authorization: `Bearer ${c.supabaseKey}`, "Content-Type": "application/json", Prefer: "return=minimal" },
    body: JSON.stringify(row),
  });
  if (!r.ok) { let m = ""; try { m = (await r.json()).message || ""; } catch {} throw new Error(m || `save failed (${r.status})`); }
}

// ---------- anonymous impact counting, shown publicly at /impact/
// Sends only: a random id made on this device, what happened (kind), the language, a level and (quiz) a score.
// Never sends message text, phone numbers or names. Our own testing is never counted: nothing is sent from
// localhost, or from a browser that once opened any Ruko page with ?test=1 (undo with ?test=0).
try {
  const q = new URLSearchParams(location.search).get("test");
  if (q === "1") localStorage.setItem("ruko.test", "1");
  if (q === "0") localStorage.removeItem("ruko.test");
} catch {}

function rukoDevice() {
  try {
    let d = localStorage.getItem("ruko.device");
    if (!/^[a-z0-9]{20}$/.test(d || "")) {
      d = Array.from(crypto.getRandomValues(new Uint8Array(20)), (b) => "abcdefghijklmnopqrstuvwxyz0123456789"[b % 36]).join("");
      localStorage.setItem("ruko.device", d);
    }
    return d;
  } catch { return null; }  // storage blocked: count nothing rather than count wrongly
}

function trackingOff() {
  try { return /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname) || localStorage.getItem("ruko.test") === "1"; }
  catch { return true; }
}

function track(kind, extra = {}) {
  try {
    const device = rukoDevice();
    if (!device || trackingOff()) return;
    const lang = extra.lang ?? (typeof LANG === "string" ? LANG : null);
    sbInsert("impact_events", { device, kind, lang, level: extra.level ?? null, score: extra.score ?? null }).catch(() => {});
  } catch {}  // counting must never break the app
}

// One short, honest question after a warning: did it change what the person was about to do?
function askOutcome(box, question, yes, no, yesLevel, noLevel) {
  box.hidden = false;
  box.innerHTML = '<p class="oq"></p><div class="row"><button type="button" class="btn btn-plain" data-a="y"></button><button type="button" class="btn btn-plain" data-a="n"></button></div><p class="small muted">Anonymous: only your answer is counted, for Ruko\'s public results page.</p>';
  box.querySelector(".oq").textContent = question;
  const [by, bn] = box.querySelectorAll("button");
  by.textContent = yes; bn.textContent = no;
  const answer = (level) => { track("outcome", { level }); box.innerHTML = '<p class="small">Thank you. Your answer is counted.</p>'; };
  by.onclick = () => answer(yesLevel);
  bn.onclick = () => answer(noLevel);
}
