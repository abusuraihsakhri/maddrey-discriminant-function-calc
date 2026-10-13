const test = require("node:test");
const assert = require("node:assert/strict");
const { mdf, abic, meldClassic } = require("../web/calculator.js");

test("mDF published worked example", () => {
  assert.deepEqual(mdf(17, 12, 10), { score: 33, severeByMdf: true });
});
test("mDF threshold based on unrounded value", () => {
  assert.deepEqual(mdf(16, 12, 13.599), { score: 32, severeByMdf: false });
  assert.equal(mdf(17, 12, 9).severeByMdf, true);
});
test("ABIC uses published INR coefficient 0.8", () => {
  assert.deepEqual(abic(50, 10, 1.5, 1), { score: 7.3, risk: "Intermediate" });
});
test("ABIC original risk group cutoffs", () => {
  assert.equal(abic(50, 7.6125, 1, 1).risk, "Low");
  assert.equal(abic(50, 7.625, 1, 1).risk, "Intermediate");
  assert.equal(abic(60, 13.75, 2, 1).risk, "High");
});
test("classic MELD clamps lower values and caps creatinine", () => {
  assert.equal(meldClassic(1, 1, 1).score, 6.4);
  assert.deepEqual(meldClassic(5, 2, 4), meldClassic(5, 2, 8));
});
test("invalid and missing inputs are rejected", () => {
  assert.throws(() => mdf("", 12, 5), /required/);
  assert.throws(() => mdf("abc", 12, 5), /between/);
  assert.throws(() => mdf(17, 12, -1), /between/);
  assert.throws(() => abic(50, 5, Infinity, 1), /between/);
});
