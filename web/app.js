(function () {
  "use strict";
  const form = document.getElementById("calculator-form");
  const results = document.getElementById("results");
  const message = document.getElementById("message");
  const output = document.getElementById("score-output");

  function value(id) {
    return document.getElementById(id).value.trim();
  }

  function addResult(label, score, interpretation) {
    const card = document.createElement("div");
    card.className = "result-item";
    const heading = document.createElement("h3");
    heading.textContent = label;
    const number = document.createElement("strong");
    number.textContent = String(score);
    const description = document.createElement("p");
    description.textContent = interpretation;
    card.append(heading, number, description);
    output.appendChild(card);
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    message.textContent = "";
    results.hidden = true;
    output.replaceChildren();

    try {
      const pt = value("pt-patient");
      const control = value("pt-control");
      const bilirubin = value("bilirubin");
      const age = value("age");
      const inr = value("inr");
      const creatinine = value("creatinine");
      const supplemental = [age, inr, creatinine];
      const hasSupplemental = supplemental.some(Boolean);
      if (hasSupplemental && !supplemental.every(Boolean)) {
        throw new Error("For additional scores, enter all of age, INR and creatinine, or leave all three blank.");
      }

      const m = window.MaddreyCalculator.mdf(pt, control, bilirubin);
      const other = hasSupplemental
        ? {
            abic: window.MaddreyCalculator.abic(age, bilirubin, inr, creatinine),
            meld: window.MaddreyCalculator.meldClassic(bilirubin, inr, creatinine)
          }
        : null;

      addResult(
        "Modified Maddrey Discriminant Function",
        m.score.toFixed(2),
        m.severeByMdf ? "At or above the historical severe threshold (32)." : "Below the historical severe threshold (32)."
      );
      if (other) {
        addResult("ABIC prognostic score", other.abic.score.toFixed(2), other.abic.risk + " risk stratum in the original ABIC cohort.");
        addResult("Classic MELD (historical three-variable formula)", other.meld.score.toFixed(1), "Not MELD 3.0 and not a transplant allocation score.");
      }
      results.hidden = false;
      results.focus();
    } catch (error) {
      message.textContent = error.message;
    }
  });

  form.addEventListener("reset", function () {
    results.hidden = true;
    message.textContent = "";
    output.replaceChildren();
  });
})();
