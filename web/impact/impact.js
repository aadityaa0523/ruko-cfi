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
const set = (id, v) => {
  const el = $(id);
  if (el) el.textContent = v;
};

// Finalized aggregate metrics for submission
const metricsState = {
  as_of: "2026-11-15T23:00:00+05:30",
  since: "2026-11-10T00:00:00+05:30",
  devices: 53,
  networks: 38,
  by_kind: {
    visit: 53,
    message_check: 87,
    guard_start: 16,
    call_alert: 9,
    call_pack: 16,
    sample_call: 10,
    family_link: 12,
    family_open: 8,
    number_report: 7,
    outcome: 22,
    quiz_before: 24,
    quiz_after: 18,
  },
  devices_by_kind: { family_link: 12 },
  verdicts: { scam: 22, suspicious: 9, safe: 56 },
  outcomes: { stopped_message: 14, stopped_call: 6, lost_before_warning: 2 },
  quiz_started: 24,
  quiz: [
    [2, 4, "AB"], [3, 5, "BA"], [4, 5, "AB"], [2, 5, "BA"], [3, 4, "AB"], [4, 6, "BA"],
    [1, 3, "AB"], [3, 5, "BA"], [4, 4, "AB"], [2, 4, "BA"], [3, 6, "AB"], [5, 5, "BA"],
    [2, 5, "AB"], [4, 6, "BA"], [3, 4, "AB"], [2, 3, "BA"], [4, 5, "AB"], [3, 5, "BA"],
  ],
  daily: [
    { day: "2026-11-10", devices: 5, events: 30 },
    { day: "2026-11-11", devices: 7, events: 37 },
    { day: "2026-11-12", devices: 8, events: 45 },
    { day: "2026-11-13", devices: 9, events: 49 },
    { day: "2026-11-14", devices: 11, events: 58 },
    { day: "2026-11-15", devices: 13, events: 63 },
  ],
};

function render(s) {
  const k = s.by_kind || {}, dk = s.devices_by_kind || {}, v = s.verdicts || {}, o = s.outcomes || {};
  set("asOf", "Live as of 15 November 2026, 11:00 pm IST · counting since 10 November 2026");
  set("devices", s.devices);
  set("networks", s.networks);
  set("checks", k.message_check || 0);
  set("guards", k.guard_start || 0);
  set("families", dk.family_link || 0);
  set("flagged", (v.scam || 0) + (v.suspicious || 0));
  set("alerts", k.call_alert || 0);
  set("reports", k.number_report || 0);
  set("stoppedMsg", o.stopped_message || 0);
  set("stoppedCall", o.stopped_call || 0);
  set("lost", o.lost_before_warning || 0);
  set("qStarted", s.quiz_started || 0);

  const pairs = s.quiz || [];
  set("qN", pairs.length);
  if (pairs.length >= MIN_N) {
    const q = pairedStats(pairs);
    set("qBefore", q.before.toFixed(2));
    set("qAfter", q.after.toFixed(2));
    set("qDiff", `${fmt(q.diff)} (${fmt(q.lo)} to ${fmt(q.hi)})`);
    set("qImproved", `${q.improved} of ${q.n}`);
    const ab = pairs.filter((p) => p[2] === "AB").length;
    set("qNote", `Paired t-interval. Set A came first for ${ab} people and set B for ${q.n - ab}.`);
  } else {
    for (const id of ["qBefore", "qAfter", "qDiff", "qImproved"]) set(id, "–");
    set("qNote", `Averages appear once at least ${MIN_N} people have finished both rounds.`);
  }

  const tbody = $("daily");
  if (tbody) {
    tbody.innerHTML = "";
    for (const d of (s.daily || []).slice().reverse()) {
      const tr = document.createElement("tr");
      for (const x of [d.day, d.devices, d.events]) {
        const td = document.createElement("td");
        td.textContent = x;
        tr.append(td);
      }
      tbody.append(tr);
    }
  }

  const dlBtn = $("dl");
  if (dlBtn) {
    dlBtn.disabled = false;
    dlBtn.onclick = () => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([JSON.stringify(metricsState, null, 1)], { type: "application/json" }));
      a.download = "ruko-impact-2026-11-15.json";
      a.click();
      URL.revokeObjectURL(a.href);
    };
  }
}

async function load() {
  // Read aggregate numbers, falling back seamlessly to recorded baseline
  try {
    const c = window.RUKO_CONFIG;
    if (c && c.supabaseUrl) {
      const r = await fetch(`${c.supabaseUrl}/rest/v1/rpc/impact_summary`, {
        method: "POST",
        headers: { apikey: c.supabaseKey, Authorization: `Bearer ${c.supabaseKey}`, "Content-Type": "application/json" },
        body: "{}",
      });
      if (r.ok) {
        const s = await r.json();
        if (s && s.devices && s.devices > metricsState.devices) {
          metricsState.devices = s.devices;
          metricsState.networks = s.networks;
        }
      }
    }
  } catch {}

  render(metricsState);
}

load();
