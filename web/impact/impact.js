// Public impact page: reads aggregate numbers from impact_summary(); raw events are never readable.
const T95 = [0, 12.71, 4.30, 3.18, 2.78, 2.57, 2.45, 2.36, 2.31, 2.26, 2.23, 2.20, 2.18, 2.16, 2.14, 2.13, 2.12, 2.11, 2.10,
  2.09, 2.09, 2.08, 2.07, 2.07, 2.06, 2.06, 2.06, 2.05, 2.05, 2.05, 2.04];  // two-sided t, by degrees of freedom
const MIN_N = 5;  // averages over fewer people are not shown

function pairedStats(pairs) {
  const n = pairs.length;
  const mean = (a) => a.reduce((s, x) => s + x, 0) / a.length;
  const b = pairs.map((p) => p[0]), a = pairs.map((p) => p[1]), d = pairs.map((p) => p[1] - p[0]);
  const md = mean(d);
  const sd = Math.sqrt(d.reduce((s, x) => s + (x - md) ** 2, 0) / (n - 1));
  const half = (T95[n - 1] ?? 1.96) * sd / Math.sqrt(n);
  return { n, before: mean(b), after: mean(a), diff: md, lo: md - half, hi: md + half, improved: d.filter((x) => x > 0).length };
}

const fmt = (x) => (x > 0 ? "+" : "") + x.toFixed(2);
const set = (id, v) => ($(id).textContent = v);

async function load() {
  const c = window.RUKO_CONFIG;
  let s;
  try {
    const r = await fetch(`${c.supabaseUrl}/rest/v1/rpc/impact_summary`, { method: "POST",
      headers: { apikey: c.supabaseKey, Authorization: `Bearer ${c.supabaseKey}`, "Content-Type": "application/json" }, body: "{}" });
    if (!r.ok) throw new Error(String(r.status));
    s = await r.json();
  } catch (e) {
    $("status").hidden = false;
    $("status").textContent = "The live counter isn't reachable right now, so no numbers are shown. Nothing here is ever estimated.";
    set("asOf", "Not available");
    return;
  }
  const k = s.by_kind || {}, dk = s.devices_by_kind || {}, v = s.verdicts || {}, o = s.outcomes || {};
  set("asOf", `Live as of ${new Date(s.as_of).toLocaleString("en-IN")}` + (s.since ? ` · counting since ${new Date(s.since).toLocaleDateString("en-IN")}` : " · no real use counted yet"));
  set("devices", s.devices); set("networks", s.networks);
  set("checks", k.message_check || 0); set("guards", k.guard_start || 0); set("families", dk.family_link || 0);
  set("flagged", (v.scam || 0) + (v.suspicious || 0)); set("alerts", k.call_alert || 0); set("reports", k.number_report || 0);
  set("stoppedMsg", o.stopped_message || 0); set("stoppedCall", o.stopped_call || 0); set("lost", o.lost_before_warning || 0);
  set("qStarted", s.quiz_started || 0);
  const pairs = s.quiz || [];
  set("qN", pairs.length);
  if (pairs.length >= MIN_N) {
    const q = pairedStats(pairs);
    set("qBefore", q.before.toFixed(2)); set("qAfter", q.after.toFixed(2));
    set("qDiff", `${fmt(q.diff)} (${fmt(q.lo)} to ${fmt(q.hi)})`);
    set("qImproved", `${q.improved} of ${q.n}`);
    const ab = pairs.filter((p) => p[2] === "AB").length;
    set("qNote", `Paired t-interval. Set A came first for ${ab} people and set B for ${q.n - ab}.`);
  } else {
    for (const id of ["qBefore", "qAfter", "qDiff", "qImproved"]) set(id, "–");
    set("qNote", `Averages appear once at least ${MIN_N} people have finished both rounds.`);
  }
  $("daily").innerHTML = "";
  for (const d of (s.daily || []).slice().reverse()) {
    const tr = document.createElement("tr");
    for (const x of [d.day, d.devices, d.events]) { const td = document.createElement("td"); td.textContent = x; tr.append(td); }
    $("daily").append(tr);
  }
  if (!(s.daily || []).length) $("daily").innerHTML = '<tr><td colspan="3">No real use counted yet.</td></tr>';
  $("dl").onclick = () => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify(s, null, 1)], { type: "application/json" }));
    a.download = `ruko-impact-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
  };
}
load();
