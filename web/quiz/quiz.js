// Spot-the-scam test: a before round, the four signs, then an after round on different messages.
// Which set comes first is random per device, so a harder set can't fake an improvement.
let SETS, order, round = 0, picks = [], before = 0;
const shuffle = (a) => a.map((x) => [Math.random(), x]).sort((p, q) => p[0] - q[0]).map((p) => p[1]);

function show(id) { for (const s of ["intro", "round", "lesson", "done"]) $(s).hidden = s !== id; window.scrollTo(0, 0); }

function renderRound() {
  const set = SETS[order[round]];
  picks = new Array(set.length).fill(null);
  $("roundTitle").textContent = round === 0 ? "Round 1 of 2: scam or real?" : "Round 2 of 2: six new messages";
  $("msgs").innerHTML = "";
  set.forEach((m, i) => {
    const div = document.createElement("div");
    div.className = "msg";
    div.innerHTML = '<p></p><div class="row"><button type="button" class="btn btn-danger" aria-pressed="false">Scam</button><button type="button" class="btn btn-plain" aria-pressed="false">Real</button></div>';
    div.querySelector("p").textContent = m.text;
    const [bs, br] = div.querySelectorAll("button");
    const pick = (v) => {
      picks[i] = v;
      bs.setAttribute("aria-pressed", String(v === true)); br.setAttribute("aria-pressed", String(v === false));
      const left = picks.filter((p) => p === null).length;
      $("submit").disabled = left > 0;
      $("left").textContent = left ? `${left} left` : "";
    };
    bs.onclick = () => pick(true); br.onclick = () => pick(false);
    $("msgs").append(div);
  });
  $("submit").disabled = true;
  $("left").textContent = `${set.length} left`;
  show("round");
}

function score() { return SETS[order[round]].reduce((n, m, i) => n + (picks[i] === m.scam ? 1 : 0), 0); }

$("start").onclick = async () => {
  const raw = await (await fetch("quiz.json")).json();
  SETS = { A: shuffle(raw.A), B: shuffle(raw.B) };
  order = Math.random() < 0.5 ? ["A", "B"] : ["B", "A"];
  round = 0;
  renderRound();
};

$("submit").onclick = () => {
  const s = score();
  if (round === 0) {
    before = s;
    track("quiz_before", { score: s, level: order.join("") });
    $("score1").textContent = `${s} of 6`;
    $("review").innerHTML = "";
    SETS[order[0]].forEach((m, i) => {
      const div = document.createElement("div");
      div.className = "msg " + (picks[i] === m.scam ? "right" : "wrong");
      div.innerHTML = "<p></p><b></b><p class='why'></p>";
      div.querySelector("p").textContent = m.text;
      div.querySelector("b").textContent = (m.scam ? "Scam. " : "Real. ") + (picks[i] === m.scam ? "You got it right." : "You missed this one.");
      div.querySelector(".why").textContent = m.why;
      $("review").append(div);
    });
    show("lesson");
  } else {
    track("quiz_after", { score: s, level: order.join("") });
    $("b").textContent = before; $("a").textContent = s;
    $("verdictLine").textContent = s > before ? "You spotted more scams after learning the four signs."
      : s === 6 ? "A perfect score. Share this with someone who might not know the signs."
      : "Scammers are good at this. Keep the four signs in mind, and check any message with Ruko.";
    $("shareQuiz").href = "https://wa.me/?text=" + encodeURIComponent(`Can you spot the scam? A 2-minute test from Ruko: ${location.origin}/quiz/`);
    show("done");
  }
};

$("next").onclick = () => { round = 1; renderRound(); };
