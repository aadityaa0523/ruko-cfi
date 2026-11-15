// Shared by the landing page, the guard app and the family screen.
const $ = (id) => document.getElementById(id);
const store = {
  get(k, d) { try { return localStorage.getItem(k) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch {} },
};

// ---------- language. Elements carry data-i18n="key". English and Hindi live per page in window.STRINGS;
// the other languages load from /i18n/<code>.json (this page's section plus the shared one).
const UI_LANGS = { en: "English", hi: "हिन्दी", ta: "தமிழ்", te: "తెలుగు", kn: "ಕನ್ನಡ", mr: "मराठी", bn: "বাংলা" };
const I18N_PAGE = { "/": "landing", "/app/": "app", "/check/": "check", "/account/": "account" }[location.pathname];
let LANG = store.get("ruko.ui", "en");
if (!UI_LANGS[LANG]) LANG = "en";
function t(key) { return (window.STRINGS?.[LANG]?.[key]) ?? (window.STRINGS?.en?.[key]) ?? key; }
async function loadLang(lang) {
  window.STRINGS ??= {};
  if (lang === "en" || lang === "hi" || window.STRINGS[lang]?.__loaded) return;
  try {
    const d = await (await fetch(`/i18n/${lang}.json?v=1`)).json();
    window.STRINGS[lang] = { ...(d.shared || {}), ...(d[I18N_PAGE] || {}), __loaded: true };
  } catch { window.STRINGS[lang] = { __loaded: true }; }  // offline: English stays
}
function applyLang(lang) {
  lang = UI_LANGS[lang] ? lang : "en";
  if (lang !== "en" && lang !== "hi" && !window.STRINGS?.[lang]?.__loaded) return loadLang(lang).then(() => applyLang(lang));
  LANG = lang;
  store.set("ruko.ui", LANG);
  document.documentElement.lang = LANG;
  for (const el of document.querySelectorAll("[data-i18n]")) el.textContent = t(el.dataset.i18n);
  for (const el of document.querySelectorAll("[data-i18n-ph]")) {
    const k = el.dataset.i18nPh;
    if (window.STRINGS?.en && !(k in window.STRINGS.en)) window.STRINGS.en[k] = el.placeholder;  // English comes from the HTML
    el.placeholder = t(k);
  }
  for (const s of document.querySelectorAll(".lang-toggle select")) s.value = LANG;
  document.dispatchEvent(new Event("langchange"));
}
// The language picker: every .lang-toggle becomes one select listing the languages in their own script.
for (const box of document.querySelectorAll(".lang-toggle")) {
  const sel = document.createElement("select");
  sel.setAttribute("aria-label", "Language / भाषा");
  for (const [code, name] of Object.entries(UI_LANGS)) sel.append(new Option(name, code));
  sel.value = LANG;
  sel.onchange = () => applyLang(sel.value);
  box.replaceChildren(sel);
}

// ---------- signs
const STAGES = [
  { key: "pose", en: "Pretends to be someone you trust", hi: "भरोसेमंद होने का नाटक" },
  { key: "fear", en: "Scares you or rushes you", hi: "डराता या जल्दी करवाता है" },
  { key: "isolate", en: "Cuts you off from family", hi: "परिवार से अलग करता है" },
  { key: "ask", en: "Asks for OTP, money or your phone", hi: "OTP, पैसे या फ़ोन माँगता है" },
];
const GLYPHS = {
  // badge: a peaked cap over a face (impersonation of an official)
  pose: '<path class="glyph" d="M36 52h28l-3-8H39z"/><circle class="glyph" cx="50" cy="62" r="7"/><path class="glyph" d="M38 78c2-6 7-9 12-9s10 3 12 9z"/>',
  // exclamation (threat)
  fear: '<rect class="glyph" x="45" y="38" width="10" height="26" rx="2"/><circle class="glyph" cx="50" cy="72" r="5.5"/>',
  // finger to lips: a person and a "hush" bar (secrecy)
  isolate: '<circle class="glyph" cx="44" cy="54" r="7"/><path class="glyph" d="M32 78c2-7 7-10 12-10s10 3 12 10z"/><rect class="glyph" x="60" y="44" width="5" height="24" rx="2"/>',
  // keypad (OTP / PIN)
  ask: '<g class="glyph"><circle cx="40" cy="50" r="4"/><circle cx="50" cy="50" r="4"/><circle cx="60" cy="50" r="4"/><circle cx="40" cy="61" r="4"/><circle cx="50" cy="61" r="4"/><circle cx="60" cy="61" r="4"/><circle cx="40" cy="72" r="4"/><circle cx="50" cy="72" r="4"/><circle cx="60" cy="72" r="4"/></g>',
};
const TRI = '<circle class="tri-fill" cx="50" cy="58" r="42"/><circle class="tri-edge" cx="50" cy="58" r="42"/>';
function signSVG(key) { return `<svg viewBox="0 12 100 92" aria-hidden="true">${TRI}${GLYPHS[key]}</svg>`; }
function octagonSVG(word = "RUKO") {
  return `<svg class="octagon" viewBox="0 0 100 100" role="img" aria-label="${word}"><path d="M30 2h40l28 28v40L70 98H30L2 70V30z" fill="#c8102e"/><path d="M31.7 6h36.6L94 31.7v36.6L68.3 94H31.7L6 68.3V31.7z" fill="none" stroke="#fff" stroke-width="3"/><text x="50" y="59" text-anchor="middle" font-family="Overpass, sans-serif" font-weight="900" font-size="25" fill="#fff" letter-spacing="1">${word}</text></svg>`;
}

function renderStages(el, playbook) {
  const done = new Set((playbook?.stages || []).filter((s) => s.done).map((s) => s.key));
  el.innerHTML = "";
  for (const s of STAGES) {
    const li = document.createElement("li");
    if (done.has(s.key)) li.className = "done";
    li.innerHTML = signSVG(s.key);
    const span = document.createElement("span");
    span.textContent = s[LANG] || window.STRINGS?.[LANG]?.["stage_" + s.key] || s.en;
    li.append(span);
    el.append(li);
  }
}

// Highlight the phrases that raised a flag (best effort: speech recognition's punctuation may differ).
function addCaption(el, text, risk, prefix) {
  const li = document.createElement("li");
  if (prefix) { const b = document.createElement("b"); b.textContent = prefix; li.append(b); }
  const lower = text.toLowerCase();
  const hits = [];
  for (const f of risk?.flags || []) {
    const i = f.phrase.length > 1 ? lower.indexOf(f.phrase) : -1;
    if (i >= 0) hits.push([i, i + f.phrase.length]);
  }
  hits.sort((a, b) => a[0] - b[0]);
  let pos = 0;
  for (const [a, b] of hits) {
    if (a < pos) continue;
    li.append(text.slice(pos, a));
    const m = document.createElement("mark"); m.textContent = text.slice(a, b); li.append(m);
    pos = b;
  }
  li.append(text.slice(pos));
  if (risk?.new?.length) li.className = "flagged";
  el.append(li);
  el.scrollTop = el.scrollHeight;
}

const LEVEL = { en: { safe: "Safe", watch: "Watching", high: "Likely scam", critical: "Scam" },
                hi: { safe: "सुरक्षित", watch: "नज़र है", high: "शायद धोखा", critical: "धोखा" } };
function setLevel(el, risk) {
  el.dataset.level = risk.level;
  el.textContent = `${LEVEL[LANG]?.[risk.level] ?? window.STRINGS?.[LANG]?.["level_" + risk.level] ?? LEVEL.en[risk.level]} – ${risk.score}/100`;
}

const AHEAD_ICON = '<svg viewBox="0 0 26 26" aria-hidden="true"><path d="M13 2 25 23H1z" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/><rect x="11.8" y="9" width="2.4" height="8" fill="currentColor"/><circle cx="13" cy="19.6" r="1.4" fill="currentColor"/></svg>';

// ---------- one-tap number reports (Supabase number_reports)
function guessCategory(flags) {
  const c = new Set((flags || []).map((f) => f.category || f));
  if (c.has("bill")) return "electricity";
  if (c.has("parcel")) return "parcel";
  if (c.has("refund_trick") || c.has("upi_collect")) return "refund";
  if (c.has("job")) return "job";
  if (c.has("prize")) return "prize";
  if (c.has("loan")) return "loan";
  if (c.has("relative")) return "relative";
  if (c.has("threat") && c.has("authority") && !c.has("risky_link")) return "digital_arrest";
  if (c.has("link_bait") || c.has("risky_link") || c.has("apk") || (c.has("payment") && c.has("authority"))) return "bank_kyc";
  return "other";
}
const CATEGORY_LABEL = { digital_arrest: "fake police / CBI", bank_kyc: "bank or KYC scam", electricity: "electricity cut-off scam",
  parcel: "parcel or customs scam", refund: "\u201csent by mistake\u201d refund scam", relative: "relative-in-trouble scam", job: "job or task scam",
  prize: "prize or lottery scam", loan: "loan scam", other: "scam" };
function reportError(e) {
  const m = String(e && e.message);
  if (m.includes("already_reported")) return "You already reported this number. Thank you.";
  if (m.includes("too_many_reports") || m.includes("number_flooded")) return "Too many reports right now. Please try again in an hour.";
  return "Couldn't save the report. Please try again.";
}
// Chakshu (DoT, Sanchar Saathi) has no public API and needs an OTP, so we hand over a ready report:
// copy the details, open the official form. The person submits it themselves.
const CHAKSHU_URL = "https://sancharsaathi.gov.in/sfc/";
async function chakshuReport(number, category, channel, message) {
  const via = { call: "Call", sms: "SMS", whatsapp: "WhatsApp" }[channel] || "Call";
  const text = [`Suspected fraud ${via} from: +91 ${number}`, `Date: ${new Date().toLocaleString("en-IN")}`,
    `Type: ${CATEGORY_LABEL[category] || "scam"}`, message ? `What they said: ${message.slice(0, 500)}` : ""].filter(Boolean).join("\n");
  try { await navigator.clipboard.writeText(text); } catch {}
  window.open(CHAKSHU_URL, "_blank", "noopener");
  return text;
}
async function reportNumber(number, category, channel) {
  const n = String(number).replace(/\D/g, "").slice(-10);
  if (n.length < 6 || typeof sbInsert !== "function") throw new Error("bad number");
  await sbInsert("number_reports", { number: n, category, channel, language: LANG });
  if (typeof track === "function") track("number_report", { level: category });
  return n;
}
