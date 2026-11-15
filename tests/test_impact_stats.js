// Self-check for the impact page's paired 95% interval. Run: node tests/test_impact_stats.js
const fs = require("fs"), assert = require("assert");
const src = fs.readFileSync(require("path").join(__dirname, "../web/impact/impact.js"), "utf8").split("const fmt")[0];
const pairedStats = new Function(src + "; return pairedStats;")();
const q = pairedStats([[3, 5], [4, 5], [2, 4], [5, 6], [3, 3]]);
assert.strictEqual(q.n, 5); assert.strictEqual(q.before, 3.4); assert.strictEqual(q.after, 4.6);
assert.ok(Math.abs(q.diff - 1.2) < 1e-9); assert.strictEqual(q.improved, 4);
// sd of diffs [2,1,2,1,0] = 0.8367; half = 2.78*0.8367/sqrt(5) = 1.040
assert.ok(Math.abs(q.lo - 0.160) < 0.01 && Math.abs(q.hi - 2.240) < 0.01, [q.lo, q.hi]);
console.log("paired stats ok", q.lo.toFixed(3), q.hi.toFixed(3));
