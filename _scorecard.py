# -*- coding: utf-8 -*-
"""Full SLS Casting Scorecard Rubric V1 helpers for WAR casting share."""
from __future__ import annotations

from html import escape
import re

# Section 1 — Creative + Commercial Fit (weights sum to 100)
SECTION1 = [
    ("Character Alignment", 22, "Does the actor align with physical, emotional, tonal, and regional traits?"),
    ("On-Screen Presence", 17, "Charisma, magnetism, and visual command on screen"),
    ("Chemistry Potential", 11, "Fit with romantic lead or ensemble? Prior co-star rapport?"),
    ("Commercial Viability", 22, "Fanbase, genre appeal, box office/streaming record"),
    ("Strategic Value", 11, "Awards potential, PR value, funding leverage"),
    ("Artistic Contribution", 11, "Will they elevate the role through interpretation or improvisation?"),
    ("Availability & Cost Fit", 6, "Affordability, scheduling fit, and representation access"),
]

# Section 2 — Red Flags Risk Index (0–70 raw; lower is better)
SECTION2 = [
    ("Professional Reliability", "Late, combative, contract volatility?"),
    ("Legal/Criminal Issues", "Active or historical legal liabilities"),
    ("Public Image / PR Risk", "Reputation, cancel potential, polarizing opinions"),
    ("Insurance/Bondability", "Can production insure them? Any exclusions?"),
    ("Scheduling Conflicts", "Availability or reliability issues"),
    ("Representation Issues", "History of difficult negotiations or agent interference"),
    ("Typecasting / Mismatch", "Incongruent with tone or too closely associated with other roles"),
    ("Market Decline", "Relevance fading or fatigued brand?"),
    ("Press Volatility", "Known for saying problematic things in media"),
    ("Cultural Compatibility", "Misalignment with tone or target audience"),
]

# Section 3a — Cost dimensions (0 = expensive/painful, 10 = low-cost/easy)
SECTION3_COST = [
    ("Base Compensation", 15, "Talent fee, buyout, bonuses"),
    ("Perks & Rider Demands", 5, "Travel, accommodations, entourage, special requests"),
    ("Schedule Accommodation", 10, "Lost time, coordination effort, delays"),
    ("Representation Overhead", 5, "Agent/manager negotiations, legal slowdowns"),
]

# Section 3b — Value dimensions
SECTION3_VALUE = [
    ("Box Office/Stream Draw", 20, "Measurable uplift in viewership or presales"),
    ("Audience Reach", 10, "Social media footprint, demographic resonance"),
    ("Funding Leverage", 10, "Attaching them helps secure investors or distributors"),
    ("Press & Buzz Potential", 10, "Talk show magnet, award buzz, trend potential"),
    ("Franchise/Sequel Value", 5, "Can they carry a franchise or return in future roles?"),
    ("Global Market Value", 10, "International recognition, dubbing appeal"),
]

# Fee midpoint estimates for ROI $ narrative (Buffalo 8 bands)
FEE_MIDPOINT_USD = {
    "extremely high": 1_500_000,
    "high": 750_000,
    "med-high": 500_000,
    "med/high": 500_000,
    "med": 300_000,
    "low-med": 100_000,
    "low/med": 100_000,
    "low": 60_000,
}

SHORT_TO_FULL = {
    "alignment": "Character Alignment",
    "presence": "On-Screen Presence",
    "chemistry": "Chemistry Potential",
    "commercial": "Commercial Viability",
    "strategic": "Strategic Value",
    "artistic": "Artistic Contribution",
    "cost fit": "Availability & Cost Fit",
    "character alignment": "Character Alignment",
    "on-screen presence": "On-Screen Presence",
    "chemistry potential": "Chemistry Potential",
    "commercial viability": "Commercial Viability",
    "strategic value": "Strategic Value",
    "artistic contribution": "Artistic Contribution",
    "availability & cost fit": "Availability & Cost Fit",
}


def clamp(n: int, lo: int = 0, hi: int = 10) -> int:
    return max(lo, min(hi, n))


def score_num(text: str) -> int | None:
    m = re.search(r"(\d+)", text or "")
    return int(m.group(1)) if m else None


def fee_key(fee: str) -> str:
    key = (fee or "").lower().replace(" ", "")
    for needle in (
        "extremelyhigh",
        "med-high",
        "med/high",
        "low-med",
        "low/med",
        "high",
        "med",
        "low",
    ):
        if needle.replace(" ", "") in key:
            return needle if needle != "extremelyhigh" else "extremely high"
    return "med"


def fee_midpoint(fee: str) -> int:
    k = fee_key(fee)
    # normalize keys used in FEE_MIDPOINT_USD
    mapping = {
        "extremely high": "extremely high",
        "high": "high",
        "med-high": "med-high",
        "med/high": "med/high",
        "med": "med",
        "low-med": "low-med",
        "low/med": "low/med",
        "low": "low",
    }
    return FEE_MIDPOINT_USD.get(mapping.get(k, "med"), 300_000)


def money(n: int) -> str:
    if n >= 1_000_000:
        v = n / 1_000_000
        return f"${v:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        return f"${n // 1000}K"
    return f"${n}"


def weighted(score: int, weight: int) -> float:
    return round(score * weight / 10, 1)


def creative_total(scores: list[int]) -> int:
    total = 0.0
    for (_, w, _), s in zip(SECTION1, scores):
        total += weighted(s, w)
    return int(round(total))


def risk_level_from_normalized(n: int) -> str:
    if n <= 21:
        return "Low"
    if n <= 42:
        return "Moderate"
    if n <= 71:
        return "High"
    return "Critical"


def risk_normalize(raw: int) -> int:
    return int(round((raw / 70) * 100))


def roi_from_cost_value(cost_scores: list[int], value_scores: list[int]) -> tuple[int, float, float]:
    cost_sub = sum(weighted(s, w) for (_, w, _), s in zip(SECTION3_COST, cost_scores))
    value_sub = sum(weighted(s, w) for (_, w, _), s in zip(SECTION3_VALUE, value_scores))
    # ROI Score = ((Value – Cost + 35) / 100) * 100
    roi = int(round(value_sub - cost_sub + 35))
    roi = clamp(roi, 0, 100)
    return roi, cost_sub, value_sub


def recommendation(creative: int, risk_norm: int, roi: int) -> str:
    if creative >= 75 and risk_norm <= 30 and roi >= 80:
        return "RECOMMEND CASTING"
    if creative >= 65 and risk_norm <= 40 and roi >= 60:
        return "CONSIDER WITH NOTES"
    if creative < 65 or risk_norm > 50 or roi < 40:
        return "NOT RECOMMENDED"
    return "CONSIDER WITH NOTES"


def synthesize_section1(row: dict, attrs: list[tuple[str, str]] | None = None) -> list[int]:
    """Return 7 scores 0–10 for Section 1."""
    by_full: dict[str, int] = {}
    if attrs:
        for label, val in attrs:
            full = SHORT_TO_FULL.get(label.lower().strip(), label.strip())
            n = score_num(val)
            if n is not None:
                by_full[full] = clamp(n)
    if len(by_full) >= 5:
        return [by_full.get(name, 7) for name, _, _ in SECTION1]

    fit = score_num(str(row.get("Fit", ""))) or 7
    fee = (row.get("Fee band") or "").lower()
    flags = (row.get("Flags") or "").lower()
    leverage = (row.get("Leverage") or "").lower()

    cost = 9 if "low" in fee and "high" not in fee else 7 if "med" in fee and "extremely" not in fee else 4 if "extremely" in fee else 5
    if "med-high" in fee.replace(" ", "") or "med/high" in fee.replace(" ", ""):
        cost = 6
    commercial = 9 if "extremely" in fee or ("high" in fee and "med" not in fee) else 7 if "med" in fee else 5
    if "presence" in flags or "press" in flags or "symbolic" in flags:
        commercial = max(commercial, 8)
    strategic = 9 if "press" in flags or "extremely" in leverage else max(1, fit - 1)
    presence = 10 if "presence" in flags else min(10, fit)
    artistic = fit if "restraint" in flags or "artistic" in flags else max(1, fit - 1)
    chemistry = max(1, fit - 1)
    return [
        clamp(fit),
        clamp(presence),
        clamp(chemistry),
        clamp(commercial),
        clamp(strategic),
        clamp(artistic),
        clamp(cost),
    ]


def synthesize_section2(row: dict) -> list[int]:
    """Return 10 risk scores 0–10 (lower better). Defaults stay Low for clean shortlist."""
    avail = (row.get("Avail risk") or "").lower()
    flags = (row.get("Flags") or "").lower()
    fee = (row.get("Fee band") or "").lower()
    base = 1
    sched = 2 if "med" in avail else 4 if "high" in avail else 1
    market = 3 if "extremely" in fee else 1
    typecast = 2 if "familiarity" in flags else 1
    press = 2 if "press" in flags else 1
    return [
        base,  # Professional Reliability
        0,  # Legal
        press,  # Public Image
        1,  # Insurance
        sched,  # Scheduling
        2 if "high" in avail else 1,  # Representation
        typecast,  # Typecasting
        market,  # Market Decline
        press,  # Press Volatility
        1,  # Cultural Compatibility
    ]


def synthesize_section3(row: dict, s1: list[int]) -> tuple[list[int], list[int]]:
    fee = (row.get("Fee band") or "").lower()
    flags = (row.get("Flags") or "").lower()
    avail = (row.get("Avail risk") or "").lower()
    # Cost scores: 10 = easy/cheap
    if "extremely" in fee:
        base_comp = 2
    elif "high" in fee and "med" not in fee.replace(" ", ""):
        base_comp = 4
    elif "med-high" in fee.replace(" ", "") or "med/high" in fee.replace(" ", ""):
        base_comp = 5
    elif "med" in fee:
        base_comp = 7
    else:
        base_comp = 9
    perks = clamp(base_comp + 1)
    schedule = 4 if "high" in avail else 6 if "med" in avail else 8
    rep = clamp(base_comp)
    cost = [base_comp, perks, schedule, rep]

    commercial, strategic, presence = s1[3], s1[4], s1[1]
    draw = commercial
    reach = clamp(commercial - 1)
    funding = strategic
    press = 9 if "press" in flags else clamp(strategic)
    franchise = clamp((commercial + presence) // 2 - 1)
    global_m = clamp(commercial - 1)
    value = [draw, reach, funding, press, franchise, global_m]
    return cost, value


def build_full_scorecard(
    row: dict,
    attrs: list[tuple[str, str]] | None = None,
    note: str = "",
    existing: dict | None = None,
) -> dict:
    s1 = synthesize_section1(row, attrs)
    s2 = synthesize_section2(row)
    cost, value = synthesize_section3(row, s1)

    creative = creative_total(s1)
    raw_risk = sum(s2)
    risk_norm = risk_normalize(raw_risk)
    level = risk_level_from_normalized(risk_norm)
    roi, cost_sub, value_sub = roi_from_cost_value(cost, value)

    # Prefer published composite line when present and close
    if existing:
        c = score_num(existing.get("creative") or "")
        r = score_num(existing.get("risk") or "")
        o = score_num(existing.get("roi") or "")
        if c is not None and abs(c - creative) <= 8:
            creative = c
        if r is not None:
            risk_norm = r
            # back-calc raw for display consistency
            raw_risk = int(round(risk_norm * 70 / 100))
            level = risk_level_from_normalized(risk_norm)
        if o is not None and abs(o - roi) <= 12:
            roi = o
        if existing.get("verdict"):
            verdict = existing["verdict"]
        else:
            verdict = recommendation(creative, risk_norm, roi)
        if existing.get("note"):
            note = existing["note"] or note
    else:
        verdict = recommendation(creative, risk_norm, roi)

    fee = row.get("Fee band") or ""
    mid = fee_midpoint(fee)
    # Rough packaging efficiency: ROI pts vs fee mid — narrative only
    uplift_pct = max(-40, min(80, roi - 50))
    est_value = int(mid * (1 + uplift_pct / 100))
    delta = est_value - mid

    return {
        "creative": creative,
        "risk_raw": raw_risk,
        "risk_norm": risk_norm,
        "risk_level": level,
        "roi": roi,
        "cost_sub": cost_sub,
        "value_sub": value_sub,
        "verdict": verdict,
        "note": note,
        "section1": s1,
        "section2": s2,
        "section3_cost": cost,
        "section3_value": value,
        "fee_mid": mid,
        "roi_delta_usd": delta,
        "roi_uplift_pct": uplift_pct,
        "composite": (
            f"Creative {creative}/100 · Risk {risk_norm}/100 ({level}) · ROI {roi}/100"
        ),
    }


def section1_rows_html(scores: list[int]) -> str:
    rows = []
    for (name, weight, prompt), score in zip(SECTION1, scores):
        wscore = weighted(score, weight)
        rows.append(
            "<tr>"
            f"<td>{escape(name)}</td>"
            f"<td class='num'>{weight}</td>"
            f"<td class='num'><strong>{score}</strong></td>"
            f"<td class='num'>{wscore:g}</td>"
            f"<td>{escape(prompt)}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def section2_rows_html(scores: list[int]) -> str:
    rows = []
    for (name, prompt), score in zip(SECTION2, scores):
        rows.append(
            "<tr>"
            f"<td>{escape(name)}</td>"
            f"<td class='num'><strong>{score}</strong></td>"
            f"<td>{escape(prompt)}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def section3_rows_html(items: list[tuple[str, int, str]], scores: list[int], score_header: str) -> str:
    rows = []
    for (name, weight, prompt), score in zip(items, scores):
        rows.append(
            "<tr>"
            f"<td>{escape(name)}</td>"
            f"<td class='num'>{weight}</td>"
            f"<td class='num'><strong>{score}</strong></td>"
            f"<td>{escape(prompt)}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def full_scorecard_html(card: dict) -> str:
    s1 = section1_rows_html(card["section1"])
    s2 = section2_rows_html(card["section2"])
    c3 = section3_rows_html(SECTION3_COST, card["section3_cost"], "Cost Burden")
    v3 = section3_rows_html(SECTION3_VALUE, card["section3_value"], "Value Potential")

    return f"""
<div class="scorecard-full">
  <header class="section-head" style="margin-top:0">
    <p class="eyebrow">SLS Casting Scorecard Rubric V1</p>
    <h2>{escape(card['verdict'])}</h2>
    <p class="lede">{escape(card['composite'])}</p>
  </header>

  <h3 class="sc-h">Section 1 · Creative + Commercial Fit</h3>
  <p class="sc-note">100 pts total. Weighted = Score × Weight ÷ 10.</p>
  <div class="table-wrap sc-table-wrap">
    <table class="sc-table">
      <thead>
        <tr>
          <th>Category</th><th>Weight</th><th>Score (0–10)</th><th>Weighted</th><th>Comments</th>
        </tr>
      </thead>
      <tbody>
        {s1}
      </tbody>
      <tfoot>
        <tr>
          <td colspan="3"><strong>Total Weighted Score (Creative + Commercial)</strong></td>
          <td class="num"><strong>{card['creative']}/100</strong></td>
          <td></td>
        </tr>
      </tfoot>
    </table>
  </div>

  <h3 class="sc-h">Section 2 · Red Flags Risk Index</h3>
  <p class="sc-note">Lower is better. Raw /70 → normalized /100. High scores require mitigation.</p>
  <div class="table-wrap sc-table-wrap">
    <table class="sc-table">
      <thead>
        <tr>
          <th>Risk Category</th><th>Score (0–10)</th><th>Comments / Evidence</th>
        </tr>
      </thead>
      <tbody>
        {s2}
      </tbody>
      <tfoot>
        <tr>
          <td><strong>Total Red Flag Score</strong></td>
          <td class="num"><strong>{card['risk_raw']}/70</strong></td>
          <td>Normalized <strong>{card['risk_norm']}/100</strong> · <strong>{escape(card['risk_level'])} Risk</strong></td>
        </tr>
      </tfoot>
    </table>
  </div>

  <h3 class="sc-h">Section 3a · Cost Dimensions</h3>
  <p class="sc-note">0 = very expensive/painful · 10 = extremely low-cost/easy. Max subtotal 35.</p>
  <div class="table-wrap sc-table-wrap">
    <table class="sc-table">
      <thead>
        <tr>
          <th>Category</th><th>Weight</th><th>Score (0–10)</th><th>Cost Burden Level</th>
        </tr>
      </thead>
      <tbody>
        {c3}
      </tbody>
      <tfoot>
        <tr>
          <td colspan="2"><strong>Cost Subtotal</strong></td>
          <td class="num"><strong>{card['cost_sub']:g}/35</strong></td>
          <td></td>
        </tr>
      </tfoot>
    </table>
  </div>

  <h3 class="sc-h">Section 3b · Value Dimensions</h3>
  <p class="sc-note">0 = adds no value · 10 = extremely valuable. Max subtotal 65.</p>
  <div class="table-wrap sc-table-wrap">
    <table class="sc-table">
      <thead>
        <tr>
          <th>Category</th><th>Weight</th><th>Score (0–10)</th><th>Value Potential</th>
        </tr>
      </thead>
      <tbody>
        {v3}
      </tbody>
      <tfoot>
        <tr>
          <td colspan="2"><strong>Value Subtotal</strong></td>
          <td class="num"><strong>{card['value_sub']:g}/65</strong></td>
          <td></td>
        </tr>
      </tfoot>
    </table>
  </div>
</div>
"""
