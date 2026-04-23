import os
import re
import html
import streamlit as st
import anthropic
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

SAMPLE_PROMO_TEXT = """Drug X significantly improved progression-free survival in adult patients with advanced solid tumors.
This breakthrough therapy was well tolerated and offers superior disease control.
See full prescribing information for warnings and precautions.
"""

SAMPLE_APPROVED_INDICATION = "Advanced solid tumors"

SUPERLATIVE_TERMS = [
    "best", "best-in-class", "breakthrough", "revolutionary", "safer", "superior",
    "guaranteed", "guarantees", "unique", "unmatched", "leading",
    "most effective", "unprecedented", "unrivaled", "extraordinary",
    "transformative", "game-changing", "first and only", "better tolerated"
]

RISK_TERMS = [
    "risk", "risks", "warning", "warnings", "precaution", "precautions",
    "adverse", "adverse reactions", "side effects", "safety",
    "contraindication", "contraindications"
]

SAFETY_SIGNAL_TERMS = [
    "safety", "safety note", "safety information", "safety signals",
    "adverse event", "adverse events", "ae", "aes", "toxicity",
    "toxicities", "rash", "diarrhea", "diarrhoea", "edema", "myalgia",
    "ild", "pneumonitis", "withheld", "withhold", "discontinued",
    "discontinuation", "contraindication", "warning", "precaution"
]

OFF_LABEL_TERMS = [
    "pediatric", "children", "adolescent", "pregnant", "pregnancy",
    "unapproved", "not approved", "off-label", "unlicensed"
]

SUBGROUP_TERMS = [
    "post-hoc", "post hoc", "subgroup", "subgroup analysis", "exploratory analysis"
]

UNIVERSAL_CLAIM_TERMS = [
    "100%", "all patients", "every patient", "universal"
]

RESPONSE_TERMS = [
    "tumor shrinkage", "response", "orr", "benefit"
]

CURRENT_INDICATION_TERMS = [
    "current indication", "currently indicated", "approved", "metastatic"
]

EARLY_STAGE_TERMS = [
    "early-stage", "early stage", "neoadjuvant", "pre-surgery", "pre surgery",
    "adjuvant", "resection", "surgical resection", "pre-surgical", "curative", "cure"
]

WEAK_EVIDENCE_TERMS = [
    "pilot study", "focus group", "investigator-initiated", "investigator initiated",
    "post-hoc", "post hoc", "exploratory", "small study"
]

COMPARATIVE_TERMS = [
    "unlike", "compared to", "versus", "traditional", "earlier therapies",
    "first-gen", "first generation", "next-generation", "next generation",
    "more refined", "pharmacokinetic advantage", "improved penetration",
    "better tolerated", "minimizes off-target binding", "advantage over"
]

ONCOLOGY_SCOPE_TERMS = [
    "oncology", "tumor", "tumours", "cancer", "solid tumor", "solid tumour",
    "survival", "patients", "treatment", "therapy", "trial", "study",
    "efficacy", "safety", "prescribing information", "adverse"
]


def split_sentences(text: str) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def find_snippet(text: str, keyword: str, max_len: int = 260) -> str:
    """
    Return a cleaner snippet around the first keyword match.

    Strategy:
    1. Find the first keyword match, case-insensitive
    2. Prefer the full line / bullet / paragraph containing the match
    3. If too short, expand to nearby sentence boundaries
    4. Strip markdown artifacts and normalize whitespace
    """
    if not text or not keyword:
        return ""

    match = re.search(re.escape(keyword), text, flags=re.IGNORECASE)
    if not match:
        return ""

    start_idx, end_idx = match.start(), match.end()

    line_start = text.rfind("\n", 0, start_idx)
    line_end = text.find("\n", end_idx)

    line_start = 0 if line_start == -1 else line_start + 1
    line_end = len(text) if line_end == -1 else line_end

    snippet = text[line_start:line_end].strip()

    if len(snippet) < 60:
        left_candidates = [
            text.rfind(". ", 0, start_idx),
            text.rfind("? ", 0, start_idx),
            text.rfind("! ", 0, start_idx),
            text.rfind("\n\n", 0, start_idx),
            text.rfind("\n", 0, start_idx),
        ]
        left = max(left_candidates)
        left = 0 if left == -1 else left + 1

        right_candidates = [
            text.find(". ", end_idx),
            text.find("? ", end_idx),
            text.find("! ", end_idx),
            text.find("\n\n", end_idx),
            text.find("\n", end_idx),
        ]
        right_candidates = [x for x in right_candidates if x != -1]
        right = min(right_candidates) if right_candidates else len(text)

        snippet = text[left:right].strip()

    if len(snippet) < 40:
        window_left = max(0, start_idx - 100)
        window_right = min(len(text), end_idx + 180)
        snippet = text[window_left:window_right].strip()

    snippet = snippet.replace("**", "")
    snippet = snippet.replace("__", "")
    snippet = snippet.replace("```", "")
    snippet = re.sub(r'^[>\-\*\#\s]+', '', snippet)
    snippet = re.sub(r'\s+', ' ', snippet).strip()

    if len(snippet) > max_len:
        snippet = snippet[:max_len].rsplit(" ", 1)[0] + "..."

    return snippet

def looks_like_oncology_scope(text: str) -> bool:
    lower_text = text.lower()
    return any(term in lower_text for term in ONCOLOGY_SCOPE_TERMS)


def ai_summary_allowed(text: str) -> tuple[bool, str]:
    if len(text) > 3500:
        return False, "Deterministic review completed. AI summary is limited to 3,500 characters in the public demo. For larger inputs and extended review support, contact us for pricing."
    if not looks_like_oncology_scope(text):
        return False, "This public demo AI summary is limited to oncology promotional or claim-review text. For broader document review or custom workflows, contact us for pricing."
    return True, ""


def get_conflict_source_text(promo_text: str, approved_indication: str) -> str:
    approved_indication = (approved_indication or "").strip()
    if approved_indication:
        return approved_indication.lower()
    return promo_text.lower()


def detect_findings(text: str, approved_indication: str = "") -> list[dict]:
    findings = []
    lower_text = text.lower()
    conflict_source_text = get_conflict_source_text(text, approved_indication)
    sentences = split_sentences(text)

    benefit_keywords = ["improved", "effective", "efficacy", "benefit", "response", "survival"]
    benefit_hits = [s for s in sentences if any(k in s.lower() for k in benefit_keywords)]
    risk_present_anywhere = any(term in lower_text for term in RISK_TERMS)

    if benefit_hits and not risk_present_anywhere:
        findings.append({
            "title": "Benefit claim without visible risk language nearby",
            "risk_level": "High",
            "why_flagged": "The text contains benefit-oriented language but no visible risk or safety language was detected in the submitted copy.",
            "matched_text": benefit_hits[0],
            "rule_reference": "FDA 21 CFR Part 202 / EU Directive 2001/83/EC Articles 87 and 89",
            "review_note": "Human review required."
        })

    matched_superlatives = [term for term in SUPERLATIVE_TERMS if term in lower_text]
    if matched_superlatives:
        findings.append({
            "title": "Absolute, superlative, or superiority promotional language",
            "risk_level": "Medium",
            "why_flagged": "The text contains promotional language that may overstate benefit or imply superiority without substantiation in the visible text. Matched terms: " + ", ".join(matched_superlatives[:8]),
            "matched_text": find_snippet(text, matched_superlatives[0]),
            "rule_reference": "FDA 21 CFR Part 202 / EU Directive 2001/83/EC Articles 87 and 89",
            "review_note": "Human review required."
        })

    matched_comparatives = [term for term in COMPARATIVE_TERMS if term in lower_text]
    if matched_comparatives:
        findings.append({
            "title": "Implied comparative or superiority framing",
            "risk_level": "Medium",
            "why_flagged": "The text uses comparative or implied superiority framing that may require strong substantiation, especially if no head-to-head evidence is presented. Matched terms: " + ", ".join(matched_comparatives[:8]),
            "matched_text": find_snippet(text, matched_comparatives[0]),
            "rule_reference": "FDA 21 CFR Part 202 / EU Directive 2001/83/EC Articles 87 and 89",
            "review_note": "Human review required."
        })

    for term in OFF_LABEL_TERMS:
        if term in lower_text:
            findings.append({
                "title": "Potential off-label-looking population or indication language",
                "risk_level": "High",
                "why_flagged": f'The term "{term}" may indicate discussion of a population or use case that requires closer regulatory review.',
                "matched_text": find_snippet(text, term),
                "rule_reference": "FDA 21 CFR Part 202 / EU Directive 2001/83/EC Articles 87 and 89",
                "review_note": "Human review required."
            })
            break

    subgroup_hit = next((term for term in SUBGROUP_TERMS if term in lower_text), None)
    universal_hit = next((term for term in UNIVERSAL_CLAIM_TERMS if term in lower_text), None)
    response_hit = next((term for term in RESPONSE_TERMS if term in lower_text), None)

    if subgroup_hit and universal_hit:
        why = (
            f'The text combines subgroup or post-hoc evidence framing ("{subgroup_hit}") '
            f'with universal or near-universal claim language ("{universal_hit}")'
        )
        if response_hit:
            why += f' and response-oriented wording ("{response_hit}")'
        why += ", which may overstate the strength or generalizability of the evidence."

        findings.append({
            "title": "High-risk subgroup or post-hoc evidence framing",
            "risk_level": "High",
            "why_flagged": why,
            "matched_text": find_snippet(text, subgroup_hit),
            "rule_reference": "FDA 21 CFR Part 202 / EU Directive 2001/83/EC Articles 87 and 89",
            "review_note": "Human review required."
        })

    current_indication_hit = next((term for term in CURRENT_INDICATION_TERMS if term in conflict_source_text), None)
    early_stage_hit = next((term for term in EARLY_STAGE_TERMS if term in lower_text), None)

    if current_indication_hit and early_stage_hit:
        source_label = approved_indication.strip() if approved_indication.strip() else current_indication_hit
        findings.append({
            "title": "Potential indication mismatch or off-label use framing",
            "risk_level": "High",
            "why_flagged": f'The structured approved indication / labeled setting ("{source_label}") appears inconsistent with promoted treatment-setting language in the body ("{early_stage_hit}"), which may indicate off-label framing or indication drift.',
            "matched_text": find_snippet(text, early_stage_hit),
            "rule_reference": "FDA 21 CFR Part 202 / EU Directive 2001/83/EC Articles 87 and 89",
            "review_note": "Human review required."
        })

    weak_evidence_hit = next((term for term in WEAK_EVIDENCE_TERMS if term in lower_text), None)
    n_match = re.search(r'\bn\s*=\s*(\d{1,3})\b', lower_text)
    small_n_value = None
    if n_match:
        try:
            n_value = int(n_match.group(1))
            if n_value < 30:
                small_n_value = n_value
        except ValueError:
            small_n_value = None

    if weak_evidence_hit or small_n_value is not None:
        if small_n_value is not None and weak_evidence_hit:
            why = f'The text references weak or limited evidence framing ("{weak_evidence_hit}") and a small sample size (n={small_n_value}), which may not support strong promotional claims without substantial qualification.'
            snippet_term = f"n={small_n_value}"
        elif small_n_value is not None:
            why = f'The text includes a small sample size (n={small_n_value}), which may represent statistically underpowered evidence for promotional use without substantial qualification.'
            snippet_term = f"n={small_n_value}"
        else:
            why = f'The text references weak or limited evidence framing ("{weak_evidence_hit}"), which may not support strong promotional claims without substantial qualification.'
            snippet_term = weak_evidence_hit

        findings.append({
            "title": "Statistically underpowered or weak evidence framing",
            "risk_level": "Medium",
            "why_flagged": why,
            "matched_text": find_snippet(text, snippet_term),
            "rule_reference": "FDA 21 CFR Part 202 / EU Directive 2001/83/EC Articles 87 and 89",
            "review_note": "Human review required."
        })

    safety_signal_hit = next((term for term in SAFETY_SIGNAL_TERMS if term in lower_text), None)
    benefit_or_promo_present = (
        any(term in lower_text for term in SUPERLATIVE_TERMS)
        or any(term in lower_text for term in ["improved", "response", "orr", "dcr", "survival", "better", "superior"])
    )

    if safety_signal_hit and benefit_or_promo_present:
        findings.append({
            "title": "Safety language may be present but fair balance may be insufficient",
            "risk_level": "Medium",
            "why_flagged": f'The text contains some safety-related language (for example "{safety_signal_hit}") but may still underemphasize safety relative to efficacy or promotional claims.',
            "matched_text": find_snippet(text, safety_signal_hit),
            "rule_reference": "FDA 21 CFR Part 202 / EU Directive 2001/83/EC Articles 87 and 89",
            "review_note": "Human review required."
        })
    elif not safety_signal_hit:
        findings.append({
            "title": "Missing cautionary language trigger",
            "risk_level": "Medium",
            "why_flagged": "No visible safety, warning, precaution, or adverse-event language was detected in the submitted text.",
            "matched_text": text[:220].strip(),
            "rule_reference": "FDA 21 CFR Part 202 / EU Directive 2001/83/EC Articles 87 and 89",
            "review_note": "Human review required."
        })

    return findings


def build_report(promo_text: str, findings: list[dict]) -> str:
    report = []
    report.append("MLR-PRECHECK REPORT")
    report.append("")
    report.append("This public demo uses a limited deterministic rules engine.")
    report.append("It does not determine compliance.")
    report.append("Human review is required.")
    report.append("No PDF or DOCX support is included in this public demo step.")
    report.append("")
    report.append("INPUT SUMMARY")
    report.append(f"Promotional text length: {len(promo_text)} characters")
    report.append("")
    report.append("FINDINGS")

    if findings:
        for i, finding in enumerate(findings, start=1):
            report.append(f"{i}. {finding['title']}")
            report.append(f"   Risk level: {finding['risk_level']}")
            report.append(f"   Why flagged: {finding['why_flagged']}")
            report.append(f"   Matched text: {finding['matched_text']}")
            report.append(f"   Rule reference: {finding['rule_reference']}")
            report.append(f"   Review note: {finding['review_note']}")
            report.append("")
    else:
        report.append("No findings triggered by the current v1 rule set.")
        report.append("")

    report.append("SCOPE LIMITS")
    report.append("- Text-only demo")
    report.append("- No PDF or DOCX support in this step")
    report.append("- No final legal or regulatory determination")
    report.append("")
    return "\n".join(report)


def generate_ai_summary(promo_text: str, findings: list[dict]) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "AI summary is not available because ANTHROPIC_API_KEY is not set on this runtime."

    findings_text = "\n".join(
        [
            f"- {f['title']} | Risk: {f['risk_level']} | Why: {f['why_flagged']} | Rule: {f['rule_reference']}"
            for f in findings
        ]
    ) or "- No deterministic findings triggered."

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = (
        "You are an assistive MLR review summarizer for oncology promotional text. "
        "You must summarize only the deterministic findings provided to you. "
        "Do not invent new findings. "
        "Do not state PASS or FAIL. "
        "Do not say the text is compliant, approved, or legally safe. "
        "Keep the output concise, practical, and plain-English. "
        "End by stating that human review is required."
    )

    user_prompt = f"""
Promotional text:
{promo_text}

Deterministic findings:
{findings_text}

Please produce:
1. A short summary of the main review concerns
2. A short section called "Likely reviewer focus"
3. A short section called "Suggested next step"

Do not add findings beyond what is listed above.
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=700,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    parts = []
    for block in message.content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)

    return "\n".join(parts).strip() or "AI summary returned no text."



def build_transparency_report_text(approved_indication: str = "") -> str:
    approved_indication = (approved_indication or "").strip() or "Not provided"

    lines = [
        "TRANSPARENCY & OVERSIGHT REPORT",
        "",
        "1. SYSTEM IDENTITY",
        "- System: MLR-PreCheck",
        "- Deterministic layer: source of truth for findings in the public demo",
        "- AI layer: optional assistive summary only; it does not replace deterministic findings",
        "",
        "2. APPROVED INDICATION / LABELED SETTING",
        f"- User-provided approved indication: {approved_indication}",
        "",
        "3. HOW THE SYSTEM WORKS",
        "- The deterministic engine checks promotional text against a fixed ruleset.",
        "- The AI layer summarizes deterministic findings in plain language.",
        "- Human review remains required.",
        "",
        "4. HUMAN OVERSIGHT",
        "- This tool is assistive only.",
        "- It does not determine compliance.",
        "- It does not provide legal, regulatory, or MLR approval.",
        "- A qualified human reviewer must review all output before use.",
        "",
        "5. DATA HANDLING",
        "- Public demo inputs are processed to generate the current output.",
        "- Do not submit patient, personal, or confidential commercial data.",
        "- This report is a transparency artifact, not a declaration of conformity.",
        "",
        "6. PUBLIC DEMO LIMITS",
        "- Paste plain text only",
        "- English only",
        "- Deterministic review up to 12,000 characters",
        "- AI summary limited to smaller public-demo inputs",
        "- No PDF or DOCX support in the public demo",
        "",
        "7. ACCOUNTABILITY",
        "- Final accountability remains with the deploying organization and human reviewer.",
        "",
        "8. SUPPORT",
        "- Having issues? drop us an email: hello@lippershey.co",
        "",
    ]
    return "\n".join(lines)


def build_transparency_report_pdf(approved_indication: str = "") -> bytes:
    report_text = build_transparency_report_text(approved_indication)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left = 18 * mm
    top = height - 18 * mm
    line_height = 6 * mm
    y = top

    c.setTitle("MLR-PreCheck Transparency & Oversight Report")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left, y, "MLR-PreCheck Transparency & Oversight Report")
    y -= 10 * mm

    c.setFont("Helvetica", 10)

    for raw_line in report_text.splitlines():
        line = raw_line if raw_line.strip() else " "
        wrapped = []
        max_chars = 95

        while len(line) > max_chars:
            split_at = line.rfind(" ", 0, max_chars)
            if split_at == -1:
                split_at = max_chars
            wrapped.append(line[:split_at].rstrip())
            line = line[split_at:].lstrip()
        wrapped.append(line)

        for part in wrapped:
            if y < 18 * mm:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = top
            c.drawString(left, y, part)
            y -= line_height

    c.save()
    buffer.seek(0)
    return buffer.read()

def render_risk_badge(risk_level: str):
    if risk_level == "High":
        st.error(f"Risk level: {risk_level}")
    elif risk_level == "Medium":
        st.warning(f"Risk level: {risk_level}")
    elif risk_level == "Low":
        st.info(f"Risk level: {risk_level}")
    else:
        st.write(f"Risk level: {risk_level}")



def parse_structured_ai_summary(summary_text: str) -> dict:
    if not summary_text:
        return {}

    pattern = re.compile(
        r"(Main review concerns|Likely reviewer focus|Suggested next step|Human review is required\.?)",
        flags=re.IGNORECASE
    )

    parts = pattern.split(summary_text.strip())
    sections = {}
    current_heading = None

    for part in parts:
        part = part.strip()
        if not part:
            continue

        normalized = part.lower().rstrip(".")

        if normalized == "main review concerns":
            current_heading = "Main review concerns"
            sections[current_heading] = ""
        elif normalized == "likely reviewer focus":
            current_heading = "Likely reviewer focus"
            sections[current_heading] = ""
        elif normalized == "suggested next step":
            current_heading = "Suggested next step"
            sections[current_heading] = ""
        elif normalized == "human review is required":
            current_heading = "Human review is required."
            sections[current_heading] = ""
        else:
            if current_heading:
                if sections[current_heading]:
                    sections[current_heading] += " " + part
                else:
                    sections[current_heading] = part

    if not sections:
        sections = {"Main review concerns": summary_text.strip()}

    return sections


def render_ai_summary_section(title: str, body: str, accent_color: str):
    safe_title = html.escape(title)
    safe_body = html.escape(body).replace("\n", "<br>")

    st.markdown(
        f"""
        <div style="
            border: 1px solid rgba(255,255,255,0.10);
            border-left: 4px solid {accent_color};
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 12px;
            background-color: rgba(255,255,255,0.03);
        ">
            <div style="
                font-size: 1.0rem;
                font-weight: 700;
                color: {accent_color};
                margin-bottom: 8px;
            ">
                {safe_title}
            </div>
            <div style="
                font-size: 0.98rem;
                line-height: 1.65;
                color: #E5E7EB;
            ">
                {safe_body}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_structured_ai_summary(summary_text: str):
    sections = parse_structured_ai_summary(summary_text)

    color_map = {
        "Main review concerns": "#60A5FA",
        "Likely reviewer focus": "#A78BFA",
        "Suggested next step": "#34D399",
    }

    for section_name in [
        "Main review concerns",
        "Likely reviewer focus",
        "Suggested next step",
    ]:
        body = sections.get(section_name, "").strip()
        if body:
            render_ai_summary_section(
                section_name,
                body,
                color_map.get(section_name, "#60A5FA")
            )

    st.warning("Human review is required.")



def render_private_pilot_locked_section(title: str, description: str):
    st.markdown(
        f"""
        <div style="
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 12px;
            background-color: rgba(255,255,255,0.02);
        ">
            <div style="
                font-size: 1.0rem;
                font-weight: 700;
                color: #E5E7EB;
                margin-bottom: 6px;
            ">
                🔒 {title}
            </div>
            <div style="
                font-size: 0.92rem;
                color: #A1A1AA;
                margin-bottom: 10px;
            ">
                <strong>Private Pilot feature</strong>
            </div>
            <div style="
                font-size: 0.97rem;
                line-height: 1.6;
                color: #D4D4D8;
                margin-bottom: 12px;
            ">
                {description}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_finding(finding: dict):
    st.markdown(f"### {finding['title']}")
    render_risk_badge(finding["risk_level"])
    st.write(f"**Why it was flagged:** {finding['why_flagged']}")
    st.write(f"**Matched text snippet:** {finding['matched_text']}")
    st.write(f"**Rule reference:** {finding['rule_reference']}")
    st.write(f"**Review note:** {finding['review_note']}")


st.set_page_config(page_title="MLR-PreCheck", layout="wide")

defaults = {
    "mlr_text": "",
    "mlr_approved_indication": "",
    "mlr_last_approved_indication": "",
    "mlr_precheck_done": False,
    "mlr_last_text": "",
    "mlr_last_findings": [],
    "mlr_last_report": "",
    "mlr_ai_summary": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("MLR-PreCheck")
st.caption("Review promotional text for possible medical, legal, and regulatory risk signals.")

with st.expander("How this tool works", expanded=True):
    st.markdown("""
### Deterministic review engine
This tool first runs a deterministic Python rules engine.  
It checks the submitted text against a fixed set of known promotional-risk patterns and reference areas.  
This deterministic layer is the **source of truth** for findings shown in the public demo.

### Claude-based AI summary
An optional Claude-based AI summary layer can rewrite deterministic findings into a more readable review note.  
This AI layer is **assistive only**. It does not replace the deterministic findings or human review.

### Public demo limits
- Paste plain text only
- Oncology promotional / claim-review text only
- Deterministic review: up to 12,000 characters
- AI summary: limited to 3,500 characters and restricted public-demo usage
- No PDF or DOCX support in the public demo
- No patient, personal, or confidential commercial data

[Having issues? drop us an email](mailto:hello@lippershey.co)
    """)

with st.expander("How to use", expanded=False):
    st.markdown("""
1. Paste promotional text into the input box
2. Click **Run pre-check**
3. Review the flagged findings and rule references
4. Optionally generate an AI summary within public demo limits
    """)

with st.expander("Public demo policy", expanded=False):
    st.markdown("""
- Testing only
- English only
- Paste text only in v1
- No PDF or DOCX support in this demo step
- Maximum 12,000 characters
- No confidential, patient, or business-sensitive data
- Human review required
    """)

top_col1, top_col2, top_col3 = st.columns([1, 1, 3])

with top_col1:
    if st.button("Load sample text"):
        st.session_state.mlr_text = SAMPLE_PROMO_TEXT
        st.session_state.mlr_approved_indication = SAMPLE_APPROVED_INDICATION
        st.session_state.mlr_precheck_done = False
        st.session_state.mlr_ai_summary = ""
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.mlr_text = ""
        st.session_state.mlr_approved_indication = ""
        st.session_state.mlr_last_approved_indication = ""
        st.session_state.mlr_precheck_done = False
        st.session_state.mlr_last_text = ""
        st.session_state.mlr_last_findings = []
        st.session_state.mlr_last_report = ""
        st.session_state.mlr_ai_summary = ""
        st.rerun()

with top_col3:
    st.caption("Use the sample promotional text for a quick demo, or reset the form.")

approved_indication = st.text_input(
    "Approved indication / labeled setting",
    placeholder="Example: Metastatic ALK+ NSCLC",
    key="mlr_approved_indication"
)

promo_text = st.text_area(
    "Promotional text",
    height=320,
    placeholder="Paste promotional copy here...",
    key="mlr_text"
)
st.caption(f"Characters: {len(promo_text)}/12000")

if st.button("Run pre-check"):
    if not promo_text.strip():
        st.warning("Please paste promotional text before running the pre-check.")
    elif len(promo_text) > 12000:
        st.error("Public demo limit reached: this text exceeds 12,000 characters. For larger promotional assets or supported review workflows, contact us for pricing.")
        st.session_state.mlr_precheck_done = False
    else:
        findings = detect_findings(promo_text, approved_indication)
        report_text = build_report(promo_text, findings)
        st.session_state.mlr_last_text = promo_text
        st.session_state.mlr_last_approved_indication = approved_indication
        st.session_state.mlr_last_findings = findings
        st.session_state.mlr_last_report = report_text
        st.session_state.mlr_precheck_done = True
        st.session_state.mlr_ai_summary = ""
        st.rerun()

st.divider()

if not st.session_state.mlr_precheck_done and not promo_text.strip():
    st.info("Start by loading the sample text or pasting promotional text to evaluate.")

if st.session_state.mlr_precheck_done:
    last_text = st.session_state.mlr_last_text
    last_approved_indication = st.session_state.mlr_last_approved_indication
    findings = st.session_state.mlr_last_findings
    report_text = st.session_state.mlr_last_report

    st.success("Pre-check complete.")
    st.info("This output is generated by a limited deterministic rules engine. It does not determine compliance. Human review is required.")
    st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no final legal or regulatory determination.")

    st.download_button(
        label="Download text report",
        data=report_text,
        file_name="mlr_precheck_report.txt",
        mime="text/plain"
    )

    transparency_pdf = build_transparency_report_pdf(
        st.session_state.get("mlr_last_approved_indication", "")
    )

    st.download_button(
        label="Download Transparency & Oversight Report (PDF)",
        data=transparency_pdf,
        file_name="mlr_precheck_transparency_report.pdf",
        mime="application/pdf"
    )

    st.subheader("Findings")
    if findings:
        for finding in findings:
            render_finding(finding)
            st.divider()
    else:
        st.success("No findings were triggered by the current v1 rule set.")

    st.subheader("AI summary")
    allowed, ai_message = ai_summary_allowed(last_text)
    if allowed:
        if st.button("Generate AI summary"):
            with st.spinner("Generating AI summary..."):
                try:
                    st.session_state.mlr_ai_summary = generate_ai_summary(last_text, findings)
                    st.rerun()
                except Exception as e:
                    st.warning(f"AI summary is temporarily unavailable. Deterministic review remains available. Details: {e}")
        else:
            st.caption("AI summary is available for this input under current public-demo limits.")

        if st.session_state.mlr_ai_summary:
            render_structured_ai_summary(st.session_state.mlr_ai_summary)
    else:
        st.warning(ai_message)

    
    st.divider()
    st.subheader("Result Quality Review")
    st.caption("Review how this result can be further analyzed in a private deployment, with deeper case-specific quality checks and internal QA support.")

    if st.button("Open Quality Review"):
        st.session_state.mlr_quality_review_open = True
        st.rerun()

    if st.session_state.get("mlr_quality_review_open"):
        render_private_pilot_locked_section(
            "Case-Specific Result Assessment",
            "Access a deeper review of the result quality based on the exact case, workflow, and output."
        )

        render_private_pilot_locked_section(
            "What the Tool Handled Well",
            "See which parts of the result performed well in this specific scenario."
        )

        render_private_pilot_locked_section(
            "Confidence and Limitations Review",
            "Review a more detailed confidence and limitations analysis tied to the exact output."
        )

        render_private_pilot_locked_section(
            "Detailed Missed-Issue Analysis",
            "Reveal likely gaps, blind spots, or under-detected issues based on the specific case."
        )

        render_private_pilot_locked_section(
            "Case-Specific Improvement Recommendations",
            "Unlock more targeted recommendations for improving logic coverage, evidence quality, and reporting."
        )

        render_private_pilot_locked_section(
            "Structured Edge-Case Logging",
            "Capture structured QA feedback for internal review, future tuning, and product-improvement workflows."
        )

        if st.button("Unlock in Private Pilot"):
            st.info(
                "Private Pilot includes private/internal deployment, deeper adaptive review, and structured QA logging. Contact hello@lippershey.co to discuss options."
            )
    with st.expander("Preview pasted promotional text"):
        st.write(last_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
st.markdown("[Having issues? drop us an email](mailto:hello@lippershey.co)")
