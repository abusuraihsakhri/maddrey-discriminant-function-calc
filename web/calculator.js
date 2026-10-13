/* Standalone, offline clinical arithmetic. No network requests or persistence. */
(function (root) {
  "use strict";

  function finiteInRange(name, input, minimum, maximum) {
    if (typeof input === "boolean" || input === null || String(input).trim() === "") {
      throw new RangeError(name + " is required.");
    }
    const value = Number(input);
    if (!Number.isFinite(value) || value < minimum || value > maximum) {
      throw new RangeError(name + " must be between " + minimum + " and " + maximum + ".");
    }
    return value;
  }

  function round(value, digits) {
    return Math.round((value + Number.EPSILON) * Math.pow(10, digits)) / Math.pow(10, digits);
  }

  function mdf(ptPatient, ptControl, bilirubin) {
    const pt = finiteInRange("Patient PT", ptPatient, 5, 120);
    const control = finiteInRange("Control PT", ptControl, 5, 120);
    const bili = finiteInRange("Bilirubin", bilirubin, 0, 75);
    const raw = 4.6 * (pt - control) + bili;
    return { score: round(raw, 2), severeByMdf: raw >= 32 };
  }

  function abic(age, bilirubin, inr, creatinine) {
    const years = finiteInRange("Age", age, 0, 120);
    const bili = finiteInRange("Bilirubin", bilirubin, 0, 75);
    const ratio = finiteInRange("INR", inr, 0.5, 15);
    const creat = finiteInRange("Creatinine", creatinine, 0.1, 30);
    const raw = years * 0.1 + bili * 0.08 + ratio * 0.8 + creat * 0.3;
    return { score: round(raw, 2), risk: raw < 6.71 ? "Low" : raw < 9 ? "Intermediate" : "High" };
  }

  function meldClassic(bilirubin, inr, creatinine) {
    const bili = Math.max(finiteInRange("Bilirubin", bilirubin, 0, 75), 1);
    const ratio = Math.max(finiteInRange("INR", inr, 0.5, 15), 1);
    const creat = Math.min(Math.max(finiteInRange("Creatinine", creatinine, 0.1, 30), 1), 4);
    const raw = 3.78 * Math.log(bili) + 11.2 * Math.log(ratio) + 9.57 * Math.log(creat) + 6.43;
    return { score: round(raw, 1) };
  }

  const api = Object.freeze({ mdf, abic, meldClassic });
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.MaddreyCalculator = api;
})(typeof window === "undefined" ? null : window);
