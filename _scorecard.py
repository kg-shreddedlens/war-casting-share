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


def risk_clearance(risk_norm: int) -> int:
    """Higher = cleaner. Inverse of red-flag normalized risk."""
    return clamp(100 - int(risk_norm), 0, 100)


def norm100(subtotal: float, max_pts: float) -> int:
    """Map a weighted subtotal onto 0–100 (higher better)."""
    if max_pts <= 0:
        return 0
    return int(round(max(0.0, min(100.0, (float(subtotal) / float(max_pts)) * 100.0))))


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


def _is_prompt_echo(comment: str, prompt: str) -> bool:
    c = re.sub(r"\s+", " ", (comment or "").strip().lower().rstrip("?"))
    p = re.sub(r"\s+", " ", (prompt or "").strip().lower().rstrip("?"))
    if not c:
        return True
    if c == p:
        return True
    # Shred tables often paste the rubric question into Comments
    return c.startswith("does the actor") or c.startswith("charisma,") or c.startswith("fit with")


def _flags(row: dict) -> str:
    return (row.get("Flags") or "").lower()


def _fee(row: dict) -> str:
    return (row.get("Fee band") or "").lower()


def _fit(row: dict) -> int | None:
    return score_num(str(row.get("Fit", "")))


def _notes(row: dict) -> str:
    return re.sub(r"\s+", " ", (row.get("Notes") or "").strip())


def justify_section1(
    name: str,
    score: int,
    row: dict,
    *,
    prompt: str = "",
    comment: str | None = None,
) -> str:
    """Answer: why this category scored N/10."""
    if comment and not _is_prompt_echo(comment, prompt):
        return comment.strip()

    fit = _fit(row)
    flags = _flags(row)
    fee = _fee(row)
    notes = _notes(row)
    note_bit = f" Shortlist note: {notes}." if notes and len(notes) < 90 else ""

    if name == "Character Alignment":
        if score >= 9:
            return (
                f"Locks the role’s physical/emotional/tonal read"
                f"{f' (shortlist Fit {fit}/10)' if fit else ''}; "
                f"little daylight between actor and character brief.{note_bit}"
            )
        if score >= 7:
            return (
                f"Mostly on-brief for look and tone"
                f"{f' (Fit {fit}/10)' if fit else ''}, with a small stretch on age, "
                f"heritage, or emotional register that keeps it under a 9.{note_bit}"
            )
        if score >= 5:
            return (
                "Partial alignment — usable, but look, age, or tone would need "
                f"intentional justifying in the room.{note_bit}"
            )
        return (
            "Material mismatch to the locked brief; would require rewriting the "
            f"character or accepting a visible stretch.{note_bit}"
        )

    if name == "On-Screen Presence":
        if "presence" in flags and score >= 8:
            return "Flagged for presence; holds the frame without forcing volume — camera authority is a casting reason here."
        if score >= 9:
            return "Commands attention in stillness and in spike moments; presence is a primary reason to pursue."
        if score >= 7:
            return "Credible screen magnetism for the role size; not a blank, but not a can’t-look-away 9/10 either."
        if score >= 5:
            return "Functional presence; may need direction/coverage to feel like a lead-adjacent force."
        return "Presence reads thin for this lane — risk of disappearing next to stronger scene partners."

    if name == "Chemistry Potential":
        if score >= 9:
            return "High confidence opposite the marriage/ensemble must-pairs; prior rapport or proven two-hander craft."
        if score >= 7:
            return "Likely chemistry with the prestige-pair / sister / workplace geometry; still wants a chemistry read before lock."
        if score >= 5:
            return "Chemistry is plausible but unproven for these specific pairings — do not package on vibes alone."
        return "Hard to see the required relational voltage; pair risk is a real reason the score is low."

    if name == "Commercial Viability":
        if score >= 9:
            return (
                "Buyer/audience recognition is doing real work for sales and awareness"
                f"{' at a ' + (row.get('Fee band') or 'premium') + ' fee band' if fee else ''}."
            )
        if score >= 7:
            return "Solid commercial usefulness without needing tentpole heat; helps the conversation more than it closes it alone."
        if score >= 5:
            return "Limited marquee pull — package must sell concept/craft harder than the name."
        return "Little measurable draw for this fee/role size; commercial case is weak."

    if name == "Strategic Value":
        if "press" in flags and score >= 7:
            return "Press/PR leverage is part of the cast thesis — awards adjacency or financing optics justify the points."
        if score >= 9:
            return "Meaningful funding, awards, or packaging leverage beyond the performance itself."
        if score >= 7:
            return "Helpful strategic upside (credibility, PR, or soft financing) without being a deal-making hammer."
        if score >= 5:
            return "Strategic upside is secondary; attach for the role fit, not for desk fireworks."
        return "Adds little packaging or financing leverage; treat as a pure performance hire."

    if name == "Artistic Contribution":
        if "artistic" in flags or "restraint" in flags:
            return (
                f"Flagged for {'artistic elevation' if 'artistic' in flags else 'restraint'}; "
                f"expected to deepen the role through interpretation, not just hit marks. Score {score}/10 reflects that bet."
            )
        if score >= 9:
            return "Likely to elevate the part — specificity, improvisation, or tonal daring beyond competent coverage."
        if score >= 7:
            return "Will deliver a sharp, authored take; elevation is probable but not the whole reason to cast."
        if score >= 5:
            return "Competent interpretive range; unlikely to redefine the role without strong direction."
        return "Artistic upside looks limited for this material — risk of a flat or generic read."

    if name == "Availability & Cost Fit":
        if score >= 9:
            return (
                f"Fee/availability sit cleanly in lane"
                f"{f' ({row.get('Fee band')})' if row.get('Fee band') else ''}; "
                f"access risk is low for the role size."
            )
        if score >= 7:
            return "Mostly affordable/accessible with manageable quote or schedule friction."
        if score >= 5:
            return "Cost or access friction is material — workable only with discipline on quote and dates."
        return "Fee and/or access likely fight the budget model; score is low because the hire can break the lane."

    return f"Scored {score}/10 against the rubric for this category."


def justify_section2(name: str, score: int, row: dict, *, clearance: int | None = None) -> str:
    """Risk clearance display: higher is better. `score` is the raw red-flag (lower better)."""
    avail = (row.get("Avail risk") or "").lower()
    flags = _flags(row)
    fee = _fee(row)
    clear = 10 - int(score) if clearance is None else int(clearance)

    if score <= 1:
        return (
            f"Clearance {clear}/10 — no material {name.lower()} signal on the current shortlist read."
        )
    if score == 2:
        return (
            f"Clearance {clear}/10 — minor {name.lower()} watch only; logged for diligence, not a block."
        )
    if name == "Scheduling Conflicts":
        if "high" in avail:
            return f"Clearance {clear}/10 — avail risk flagged High; schedule reliability needs buffers."
        if "med" in avail:
            return f"Clearance {clear}/10 — medium availability risk; dates may need alternate holds."
        return f"Clearance {clear}/10 — some schedule friction until calendars clear."
    if name == "Public Image / PR Risk" or name == "Press Volatility":
        if "press" in flags:
            return f"Clearance {clear}/10 — press flag on the shortlist; PR screening before soft-offer."
        return f"Clearance {clear}/10 — elevated press/image sensitivity for this profile."
    if name == "Typecasting / Mismatch":
        if "familiarity" in flags:
            return (
                f"Clearance {clear}/10 — familiarity helps sales but can typecast if the brand is too loud."
            )
        return f"Clearance {clear}/10 — some incongruence with tone or prior roles until materials prove the pivot."
    if name == "Market Decline":
        if "extremely" in fee or ("high" in fee and "med" not in fee.replace(" ", "")):
            return f"Clearance {clear}/10 — high fee against uncertain heat; market fatigue is priced in."
        return f"Clearance {clear}/10 — mild relevance/fatigue concern."
    if name == "Representation Issues":
        return f"Clearance {clear}/10 — negotiation/access friction possible; plan for slower paper."
    return f"Clearance {clear}/10 — {name.lower()} needs mitigation before lock."


def justify_section3_cost(name: str, score: int, row: dict) -> str:
    """Cost dimensions: 10 = easy/cheap — explain the score."""
    fee = row.get("Fee band") or "unbanded"
    if score >= 9:
        return f"Easy on this axis relative to {fee} — low pain for the production model."
    if score >= 7:
        return f"Mostly manageable under a {fee} posture; not free, not punishing."
    if score >= 5:
        return f"Material cost/friction on {name.lower()}; only works with quote discipline."
    return f"Painful on {name.lower()} for this fee lane ({fee}) — a primary reason the cost score is low."


def justify_section3_value(name: str, score: int, row: dict) -> str:
    """Value dimensions: 10 = extremely valuable."""
    flags = _flags(row)
    if score >= 9:
        return f"Strong {name.lower()} contribution — this is part of why the attach is worth chasing."
    if score >= 7:
        return f"Clear {name.lower()} upside without needing it to carry the whole package."
    if score >= 5:
        return f"Moderate {name.lower()}; helpful but not a financing hammer."
    if "press" in flags and "Press" in name:
        return "Press flag exists, but measurable buzz value still looks limited for this role size."
    return f"Limited {name.lower()} add — do not oversell this dimension in the room."


def build_full_scorecard(
    row: dict,
    attrs: list[tuple[str, str]] | None = None,
    note: str = "",
    existing: dict | None = None,
    comments: dict[str, str] | None = None,
) -> dict:
    s1 = synthesize_section1(row, attrs)
    s2 = synthesize_section2(row)
    cost, value = synthesize_section3(row, s1)
    comments = comments or {}

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

    s1_why = [
        justify_section1(
            name,
            score,
            row,
            prompt=prompt,
            comment=comments.get(name) or comments.get(name.lower()),
        )
        for (name, _w, prompt), score in zip(SECTION1, s1)
    ]
    s2_why = [
        justify_section2(name, score, row, clearance=10 - score)
        for (name, _p), score in zip(SECTION2, s2)
    ]
    cost_why = [
        justify_section3_cost(name, score, row)
        for (name, _w, _p), score in zip(SECTION3_COST, cost)
    ]
    value_why = [
        justify_section3_value(name, score, row)
        for (name, _w, _p), score in zip(SECTION3_VALUE, value)
    ]
    clearance = risk_clearance(risk_norm)
    cost_100 = norm100(cost_sub, 35)
    value_100 = norm100(value_sub, 65)

    return {
        "creative": creative,
        "risk_raw": raw_risk,
        "risk_norm": risk_norm,
        "risk_clearance": clearance,
        "risk_level": level,
        "roi": roi,
        "cost_sub": cost_sub,
        "value_sub": value_sub,
        "cost_100": cost_100,
        "value_100": value_100,
        "verdict": verdict,
        "note": note,
        "section1": s1,
        "section2": s2,
        "section3_cost": cost,
        "section3_value": value,
        "section1_why": s1_why,
        "section2_why": s2_why,
        "section3_cost_why": cost_why,
        "section3_value_why": value_why,
        "fee_mid": mid,
        "roi_delta_usd": delta,
        "roi_uplift_pct": uplift_pct,
        "composite": (
            f"Creative {creative}/100 · Risk clearance {clearance}/100 ({level} residual) · ROI {roi}/100"
        ),
    }


def sc_row(
    title: str,
    prompt: str,
    score: int | str,
    *,
    meta: str = "",
    denom: str = "10",
    why: str = "",
) -> str:
    meta_html = f'<p class="sc-meta">{escape(meta)}</p>' if meta else ""
    why_html = (
        f'<div class="sc-why"><span class="sc-why-label">Why this score</span>'
        f'<p>{escape(why)}</p></div>'
        if why
        else '<div class="sc-why"></div>'
    )
    return f"""<li class="sc-row">
  <div class="sc-row-copy">
    <h4 class="sc-cat">{escape(title)}</h4>
    <p class="sc-prompt">{escape(prompt)}</p>
    {meta_html}
  </div>
  {why_html}
  <div class="sc-score" aria-label="Score {escape(str(score))} of {escape(denom)}">
    <span class="sc-score-n">{escape(str(score))}</span>
    <span class="sc-score-den">/{escape(denom)}</span>
  </div>
</li>"""


def section1_rows_html(scores: list[int], whys: list[str] | None = None) -> str:
    rows = []
    whys = whys or []
    for i, ((name, weight, prompt), score) in enumerate(zip(SECTION1, scores)):
        wscore = weighted(score, weight)
        rows.append(
            sc_row(
                name,
                prompt,
                score,
                meta=f"Weight {weight} · Weighted {wscore:g}",
                why=whys[i] if i < len(whys) else "",
            )
        )
    return "\n".join(rows)


def section2_rows_html(scores: list[int], whys: list[str] | None = None) -> str:
    """Display risk as clearance (10 − raw) so higher is better."""
    rows = []
    whys = whys or []
    for i, ((name, prompt), score) in enumerate(zip(SECTION2, scores)):
        clearance = 10 - int(score)
        rows.append(
            sc_row(
                name,
                prompt,
                clearance,
                why=whys[i] if i < len(whys) else "",
            )
        )
    return "\n".join(rows)


def section3_rows_html(
    items: list[tuple[str, int, str]],
    scores: list[int],
    whys: list[str] | None = None,
) -> str:
    rows = []
    whys = whys or []
    for i, ((name, weight, prompt), score) in enumerate(zip(items, scores)):
        rows.append(
            sc_row(
                name,
                prompt,
                score,
                meta=f"Weight {weight}",
                why=whys[i] if i < len(whys) else "",
            )
        )
    return "\n".join(rows)


def sc_panel(
    title: str,
    note: str,
    rows_html: str,
    foot_label: str,
    foot_value: str,
    *,
    badge: str = "",
) -> str:
    badge_html = f'<div class="sc-badge">{badge}</div>' if badge else ""
    return f"""<article class="sc-panel">
  <header class="sc-panel-head">
    <div class="sc-panel-titles">
      <h3 class="sc-h">{escape(title)}</h3>
      <p class="sc-note">{escape(note)}</p>
    </div>
    {badge_html}
  </header>
  <ol class="sc-rows">
    {rows_html}
  </ol>
  <footer class="sc-panel-foot">
    <span class="sc-foot-label">{escape(foot_label)}</span>
    <span class="sc-foot-value">{foot_value}</span>
  </footer>
</article>"""


def full_scorecard_html(card: dict) -> str:
    s1 = section1_rows_html(card["section1"], card.get("section1_why"))
    s2 = section2_rows_html(card["section2"], card.get("section2_why"))
    c3 = section3_rows_html(SECTION3_COST, card["section3_cost"], card.get("section3_cost_why"))
    v3 = section3_rows_html(SECTION3_VALUE, card["section3_value"], card.get("section3_value_why"))

    cost_100 = card.get("cost_100", norm100(card["cost_sub"], 35))
    value_100 = card.get("value_100", norm100(card["value_sub"], 65))
    clearance = card.get("risk_clearance", risk_clearance(card["risk_norm"]))

    p1 = sc_panel(
        "Section 1 · Creative + Commercial Fit",
        "Normalized /100. Higher is better. Row scores /10 · Weighted = Score × Weight ÷ 10.",
        s1,
        "Creative total",
        f"<strong>{card['creative']}</strong><span class='sc-foot-den'>/100</span>",
        badge=f"<span class='sc-badge-n'>{card['creative']}</span><span class='sc-badge-den'>/100</span>",
    )
    p2 = sc_panel(
        "Section 2 · Risk Clearance",
        "Normalized /100. Higher is better (cleaner attach). Row scores are clearance /10.",
        s2,
        "Risk clearance",
        (
            f"<strong>{clearance}</strong><span class='sc-foot-den'>/100</span>"
            f"<span class='sc-foot-extra'> · {escape(card['risk_level'])} residual risk</span>"
        ),
        badge=(
            f"<span class='sc-badge-n'>{clearance}</span>"
            f"<span class='sc-badge-den'>/100</span>"
        ),
    )
    p3a = sc_panel(
        "Section 3a · Cost Efficiency",
        "Normalized /100. Higher is better (cheaper / easier). Row scores /10 · easy = 10.",
        c3,
        "Cost efficiency",
        f"<strong>{cost_100}</strong><span class='sc-foot-den'>/100</span>",
        badge=f"<span class='sc-badge-n'>{cost_100}</span><span class='sc-badge-den'>/100</span>",
    )
    p3b = sc_panel(
        "Section 3b · Value Index",
        "Normalized /100. Higher is better. Row scores /10 · valuable = 10.",
        v3,
        "Value index",
        f"<strong>{value_100}</strong><span class='sc-foot-den'>/100</span>",
        badge=f"<span class='sc-badge-n'>{value_100}</span><span class='sc-badge-den'>/100</span>",
    )

    return f"""
<div class="scorecard-full">
  <header class="section-head" style="margin-top:0">
    <p class="eyebrow">SLS Casting Scorecard Rubric V1</p>
    <h2>{escape(card['verdict'])}</h2>
    <p class="lede">{escape(card['composite'])}</p>
  </header>
  {p1}
  {p2}
  {p3a}
  {p3b}
</div>
"""