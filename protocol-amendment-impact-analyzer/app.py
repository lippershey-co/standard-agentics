import os
import re
import html
from io import BytesIO
from datetime import datetime
import streamlit as st
import anthropic
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

SAMPLE_OLD_TEXT = """Protocol version 1.0

Study title:
Phase 2 study of VX-247 in metastatic NSCLC

Eligibility:
Patients must have received exactly one prior line of systemic therapy.
ECOG performance status must be 0 or 1.
Patients with untreated brain metastases are excluded.

Safety reporting:
SAEs must be reported within 24 hours of site awareness.

Assessments:
Tumor imaging every 8 weeks.

Endpoints:
Primary endpoint is progression-free survival.
Secondary endpoints include overall survival and ORR.
"""

SAMPLE_NEW_TEXT = """Protocol version 2.0

Study title:
Phase 2 study of VX-247 in metastatic NSCLC

Eligibility:
Patients may have received up to two prior lines of systemic therapy.
ECOG performance status may be 0, 1, or 2.
Patients with stable treated brain metastases may be enrolled.

Safety reporting:
Fatal or life-threatening SAEs require immediate notification, and all SAEs must be reported within 24 hours of site awareness.

Assessments:
Tumor imaging every 6 weeks.

Endpoints:
Primary endpoint is objective response rate.
Key secondary endpoints include progression-free survival and overall survival.
"""

CHANGE_RULES = [
    {
        "title": "Eligibility criteria change detected",
        "old_patterns": [r"exactly one prior line", r"ecog performance status must be 0 or 1", r"untreated brain metastases are excluded"],
        "new_patterns": [r"up to two prior lines", r"ecog performance status may be 0, 1, or 2", r"stable treated brain metastases may be enrolled"],
        "impact_type": "Eligibility / enrollment impact",
        "why": "The amendment appears to change who can be enrolled, which may affect site screening, patient eligibility, and amendment communication.",
    },
    {
        "title": "Safety-reporting change detected",
        "old_patterns": [r"saes must be reported within 24 hours"],
        "new_patterns": [r"fatal or life-threatening saes require immediate notification", r"all saes must be reported within 24 hours"],
        "impact_type": "Safety reporting impact",
        "why": "The amendment appears to change safety-reporting expectations, which may require site retraining or updated reporting workflows.",
    },
    {
        "title": "Assessment schedule change detected",
        "old_patterns": [r"tumor imaging every 8 weeks"],
        "new_patterns": [r"tumor imaging every 6 weeks"],
        "impact_type": "Assessment / visit burden impact",
        "why": "The amendment appears to change study assessments or timing, which may affect site operations and patient burden.",
    },
    {
        "title": "Endpoint hierarchy change detected",
        "old_patterns": [r"primary endpoint is progression-free survival"],
        "new_patterns": [r"primary endpoint is objective response rate", r"key secondary endpoints include progression-free survival"],
        "impact_type": "Endpoint / statistical impact",
        "why": "The amendment appears to change endpoint framing or hierarchy, which may affect study interpretation and amendment significance.",
    },
]

def extract_line(text: str, keyword: str, max_len: int = 220) -> str:
    lower_text = text.lower()
    lower_keyword = keyword.lower()
    idx = lower_text.find(lower_keyword)
    if idx == -1:
        return ""

    line_start = text.rfind("\n", 0, idx)
    line_end = text.find("\n", idx)

    line_start = 0 if line_start == -1 else line_start + 1
    line_end = len(text) if line_end == -1 else line_end

    snippet = " ".join(text[line_start:line_end].strip().split())
    if len(snippet) > max_len:
        snippet = snippet[:max_len].rsplit(" ", 1)[0] + "..."
    return snippet

def looks_like_protocol_amendment_scope(old_text: str, new_text: str) -> bool:
    lower_text = (old_text + "\n" + new_text).lower()
    scope_terms = [
        "protocol",
        "eligibility",
        "safety reporting",
        "sae",
        "assessments",
        "endpoint",
        "ecog",
        "brain metastases",
        "tumor imaging",
        "progression-free survival",
        "objective response rate",
        "systemic therapy",
    ]
    return any(term in lower_text for term in scope_terms)


def ai_summary_allowed(old_text: str, new_text: str):
    combined_length = len(old_text) + len(new_text)
    if combined_length > 3500:
        return False, "Deterministic review completed. AI summary is limited to 3,500 combined characters in the public demo. For larger inputs and extended review support, contact us for pricing."
    if not looks_like_protocol_amendment_scope(old_text, new_text):
        return False, "This public demo AI summary is limited to protocol-amendment or clinical study amendment text. For broader document review or custom workflows, contact us for pricing."
    return True, ""


def detect_amendment_findings(old_text: str, new_text: str):
    findings = []
    table_rows = []

    old_lower = old_text.lower()
    new_lower = new_text.lower()

    for rule in CHANGE_RULES:
        old_hit = next((p for p in rule["old_patterns"] if re.search(p, old_lower, flags=re.IGNORECASE)), None)
        new_hit = next((p for p in rule["new_patterns"] if re.search(p, new_lower, flags=re.IGNORECASE)), None)

        if old_hit and new_hit:
            old_snippet = extract_line(old_text, old_hit)
            new_snippet = extract_line(new_text, new_hit)

            findings.append({
                "title": rule["title"],
                "risk_level": "Medium",
                "why_flagged": rule["why"],
                "matched_text": f"Old: {old_snippet} | New: {new_snippet}",
                "rule_reference": "Protocol amendment impact heuristic",
                "review_note": "Human review required.",
            })

            table_rows.append({
                "Impact Area": rule["impact_type"],
                "Old Version Signal": old_snippet,
                "New Version Signal": new_snippet,
                "Suggested Review Direction": "Confirm whether this amendment changes site instructions, ethics submission needs, or study conduct expectations.",
            })

    return findings, table_rows

def build_report(old_text: str, new_text: str, findings: list[dict], table_rows: list[dict]) -> str:
    report = []
    report.append("PROTOCOL-AMENDMENT-IMPACT-ANALYZER REPORT")
    report.append("")
    report.append("This public demo uses a limited deterministic amendment-impact engine.")
    report.append("It does not determine formal amendment classification, ethics requirements, or final regulatory obligations.")
    report.append("Human review is required.")
    report.append("No PDF or DOCX support is included in this public demo step.")
    report.append("")
    report.append("INPUT SUMMARY")
    report.append(f"Old text length: {len(old_text)} characters")
    report.append(f"New text length: {len(new_text)} characters")
    report.append(f"Impact rows detected: {len(table_rows)}")
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
        report.append("No amendment-impact findings were triggered by the current v1 rule set.")
        report.append("")

    report.append("AMENDMENT IMPACT TABLE")
    if table_rows:
        for row in table_rows:
            report.append(
                f"- {row['Impact Area']} | {row['Old Version Signal']} | {row['New Version Signal']}"
            )
    else:
        report.append("- No amendment-impact rows available")
    report.append("")
    report.append("SCOPE LIMITS")
    report.append("- Text-only demo")
    report.append("- No PDF or DOCX support in this step")
    report.append("- No final amendment-classification or ethics-submission determination")
    report.append("")
    return "\n".join(report)

def render_ai_data_notice():
    st.warning("Data notice — public demo only")

    st.write(
        "Use this AI summary only with **example, synthetic, public, or fully anonymised text**."
    )

    st.markdown(
        """**Do not submit:**
- Real patient data or case narratives
- Unpublished compound or trial data
- Confidential regulatory documents
- Anything covered by an NDA or confidentiality agreement
"""
    )

    st.markdown(
        """**Safe to use:**
- Publicly available label text
- Anonymised or synthetic examples
- Your own non-confidential draft promotional copy
- Published regulatory guidance excerpts
"""
    )

    st.write(
        "The selected text will be sent to the **Anthropic API** for summarisation. "
        "Under Anthropic's commercial API terms, inputs are **not used for model training** "
        "and are retained for up to **7 days** by default."
    )

    st.info(
        "Want a private deployment or EU-residency setup? Contact hello@lippershey.co."
    )


def generate_ai_summary_placeholder(findings: list[dict], table_rows: list[dict]) -> str:
    if not findings:
        return (
            "No deterministic findings were triggered by the current v1 rule set. "
            "Once connected, the Claude-based AI summary will turn this result into a short plain-language reviewer note."
        )

    lines = []
    lines.append("Claude-based AI summary preview")
    lines.append("")
    lines.append("This placeholder shows where the assistive AI summary will appear.")
    lines.append("It will summarize deterministic findings only, not replace them.")
    lines.append("")
    lines.append(f"Findings detected: {len(findings)}")
    lines.append("Top amendment-impact review signals:")
    for finding in findings[:3]:
        lines.append(f"- {finding['title']} ({finding['risk_level']})")
    if table_rows:
        lines.append("")
        lines.append("Detected amendment-impact context:")
        for row in table_rows[:2]:
            lines.append(f"- {row['Impact Area']} | {row['Old Version Signal']} | {row['New Version Signal']}")
    lines.append("")
    lines.append("Human review is still required.")
    return "\n".join(lines)


def generate_ai_summary(old_text: str, new_text: str, findings: list[dict], table_rows: list[dict]) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "AI summary is not available because ANTHROPIC_API_KEY is not set on this runtime."

    findings_text = "\n".join(
        [
            f"- {f['title']} | Risk: {f['risk_level']} | Why: {f['why_flagged']} | Matched: {f['matched_text']} | Reference: {f['rule_reference']}"
            for f in findings
        ]
    ) or "- No deterministic findings triggered."

    table_text = "\n".join(
        [
            f"- {row['Impact Area']} | {row['Old Version Signal']} | {row['New Version Signal']} | {row['Suggested Review Direction']}"
            for row in table_rows
        ]
    ) or "- No amendment-impact rows available."

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = (
        "You are an assistive protocol-amendment impact summarizer. "
        "You must summarize only the deterministic findings and amendment-impact table provided to you, plus limited clearly grounded interpretation that directly follows from those findings. "
        "Do not invent new findings. "
        "Do not state PASS or FAIL. "
        "Do not state the amendment is major, substantial, approved, or submission-ready unless that was already explicitly established in the deterministic findings. "
        "Do not make definitive legal, medical, clinical, ethics, or regulatory judgments. "
        "Be concise, practical, and plain-English. "
        "Your output must use exactly these section headings in this exact order: "
        "'Main review concerns', 'Likely reviewer focus', 'Suggested next step'. "
        "End with the exact sentence: 'Human review is required.'"
    )

    user_prompt = f"""
Old protocol text:
{old_text}

New protocol text:
{new_text}

Deterministic findings:
{findings_text}

Amendment impact table:
{table_text}

Write the response in this exact structure:

Main review concerns
<1 short paragraph summarizing the most important deterministic findings and any limited directly grounded interpretation.>

Likely reviewer focus
<1 short paragraph describing what a reviewer would most likely examine next, based only on the deterministic findings and clearly grounded interpretation.>

Suggested next step
<1 short paragraph with the most practical next action, based only on the deterministic findings.>

Human review is required.

Rules:
- Do not add new findings not supported by the deterministic findings or amendment-impact table.
- Do not use bullet points.
- Do not output PASS or FAIL.
- Do not say the amendment is major, substantial, approved, or submission-ready.
- Keep the tone practical and professional.
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=700,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    parts = []
    for block in message.content:
        block_text = getattr(block, "text", None)
        if block_text:
            parts.append(block_text)

    return "\n".join(parts).strip() or "AI summary returned no text."


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



def build_transparency_report_text(old_text: str = "", new_text: str = "", findings=None, table_rows=None) -> str:
    report_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    findings = findings or []
    table_rows = table_rows or []

    info_count = sum(1 for f in findings if f.get("risk_level") == "Info")
    low_count = sum(1 for f in findings if f.get("risk_level") == "Low")
    medium_count = sum(1 for f in findings if f.get("risk_level") == "Medium")
    high_count = sum(1 for f in findings if f.get("risk_level") == "High")

    lines = [
        "TRANSPARENCY & OVERSIGHT REPORT",
        "",
        f"Generated: {report_date}",
        "",
        "1. SYSTEM IDENTITY",
        "- System: Protocol-Amendment-Impact-Analyzer",
        "- Deterministic layer: source of truth for findings in the public demo",
        "- AI layer: optional assistive summary only; it does not replace deterministic findings",
        "",
        "2. INPUT CONTEXT",
        f"- Old protocol text length: {len(old_text)} characters",
        f"- New protocol text length: {len(new_text)} characters",
        f"- Amendment-impact rows detected: {len(table_rows)}",
        "",
        "3. HOW THE SYSTEM WORKS",
        "- The deterministic engine compares old vs new protocol-style text against a fixed set of amendment-impact heuristics.",
        "- The AI layer summarizes deterministic findings and amendment-impact table outputs in plain language.",
        "- Human review remains required.",
        "",
        "4. AMENDMENT-IMPACT LOGIC USED IN THIS DEMO",
        "- Eligibility-criteria change detection",
        "- Safety-reporting change detection",
        "- Assessment-schedule change detection",
        "- Endpoint-hierarchy change detection",
        "- Amendment-impact table generation",
        "",
        "5. CURRENT SNAPSHOT",
        f"- High-risk findings: {high_count}",
        f"- Medium-risk findings: {medium_count}",
        f"- Low-risk findings: {low_count}",
        f"- Info findings: {info_count}",
        "",
        "6. HUMAN OVERSIGHT",
        "- This tool is assistive only.",
        "- It does not determine formal amendment classification, ethics requirements, or final regulatory obligations.",
        "- It does not provide legal, medical, clinical, ethics, or regulatory approval.",
        "- A qualified human reviewer must review all output before use.",
        "",
        "7. DATA HANDLING",
        "- Public demo inputs are processed to generate the current output.",
        "- Do not submit patient, personal, or confidential commercial data.",
        "- This report is a transparency artifact, not a declaration of conformity.",
        "",
        "8. PUBLIC DEMO LIMITS",
        "- Paste plain text only",
        "- English only",
        "- Deterministic review up to 12,000 characters per text box",
        "- AI summary limited to smaller public-demo inputs",
        "- No PDF or DOCX support in the public demo",
        "",
        "9. ACCOUNTABILITY",
        "- Final accountability remains with the deploying organization and human reviewer.",
        "",
        "10. SUPPORT",
        "- Having issues? drop us an email: hello@lippershey.co",
        "",
    ]
    return "\n".join(lines)


def build_transparency_report_pdf(old_text: str = "", new_text: str = "", findings=None, table_rows=None) -> bytes:
    report_text = build_transparency_report_text(old_text, new_text, findings, table_rows)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left = 18 * mm
    top = height - 18 * mm
    line_height = 6 * mm
    y = top

    c.setTitle("Protocol-Amendment-Impact-Analyzer Transparency & Oversight Report")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left, y, "Protocol-Amendment-Impact-Analyzer Transparency & Oversight Report")
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
    else:
        st.info(f"Risk level: {risk_level}")

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
    st.write(f"**Matched text:** {finding['matched_text']}")
    st.write(f"**Rule reference:** {finding['rule_reference']}")
    st.write(f"**Review note:** {finding['review_note']}")

st.set_page_config(page_title="Protocol-Amendment-Impact-Analyzer", layout="wide")

defaults = {
    "pai_old_text": "",
    "pai_new_text": "",
    "pai_done": False,
    "pai_last_old_text": "",
    "pai_last_new_text": "",
    "pai_last_findings": [],
    "pai_last_table_rows": [],
    "pai_last_report": "",
    "pai_ai_summary": "",
    "pai_ai_notice_open": False,
    "pai_quality_review_open": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("Protocol-Amendment-Impact-Analyzer")
st.caption("Compare old vs new protocol-style text and surface likely amendment impacts on eligibility, safety, assessments, and endpoints.")

with st.expander("How this tool works", expanded=True):
    st.markdown("""
### Deterministic amendment-impact engine
This tool checks old vs new protocol-style text against a limited set of v1 amendment-impact heuristics.
This deterministic layer is the **source of truth** for findings shown in the public demo.

### Claude-based AI summary
An optional Claude-based AI summary layer can later rewrite deterministic findings into a more readable reviewer note.
This AI layer is **assistive only**. It does not replace deterministic findings or human review.


### Demo rules depth
This public demo uses a **limited deterministic rules pack** with **restricted edge-case coverage**.

To unlock **Private Pilot** with the **full deep rules pack**, **expanded edge-case coverage**, and **rules updates**, contact [hello@lippershey.co](mailto:hello@lippershey.co) or see more details [here](https://standardagentics.ai/pricing).

### Public demo limits
- Paste plain text only
- Protocol / amendment comparison text only
- Deterministic review up to 12,000 characters per box
- AI summary limited to smaller inputs and restricted public-demo usage
- No PDF or DOCX support in the public demo
- No confidential, patient, or business-sensitive data

[Having issues? drop us an email](mailto:hello@lippershey.co)
    """)

with st.expander("How to use", expanded=False):
    st.markdown("""
1. Paste the old protocol text
2. Paste the new protocol text
3. Click **Run amendment impact review**
4. Review deterministic findings
5. Review the amendment impact table
6. Optionally generate an AI summary in a later step
    """)

with st.expander("Public demo policy", expanded=False):
    st.markdown("""
- Testing only
- English only
- Paste text only in v1
- No PDF or DOCX support in this demo step
- Maximum 12,000 characters per text box
- No confidential, patient, or business-sensitive data
- Human review required
    """)


with st.expander("Transparency & oversight", expanded=False):
    st.markdown("""
This app can generate a **Transparency & Oversight Report** describing:

- the system identity
- deterministic vs AI summary roles
- human oversight expectations
- public-demo limits
- data-handling cautions
- support contact

This is a transparency artifact for stakeholders.  
It is **not** a declaration of conformity and **not** a legal approval.
    """)

top_col1, top_col2, top_col3 = st.columns([1, 1, 3])

with top_col1:
    if st.button("Load sample texts"):
        st.session_state.pai_old_text = SAMPLE_OLD_TEXT
        st.session_state.pai_new_text = SAMPLE_NEW_TEXT
        st.session_state.pai_done = False
        st.session_state.pai_ai_summary = ""
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.pai_old_text = ""
        st.session_state.pai_new_text = ""
        st.session_state.pai_done = False
        st.session_state.pai_last_old_text = ""
        st.session_state.pai_last_new_text = ""
        st.session_state.pai_last_findings = []
        st.session_state.pai_last_table_rows = []
        st.session_state.pai_last_report = ""
        st.session_state.pai_ai_summary = ""
        st.session_state.pai_quality_review_open = False
        st.rerun()

with top_col3:
    st.caption("Use the sample protocol texts for a quick demo, or reset the form.")

old_text = st.text_area(
    "Old protocol text",
    height=240,
    placeholder="Paste old protocol text here...",
    key="pai_old_text"
)
st.caption(f"Old text characters: {len(old_text)}/12000")

new_text = st.text_area(
    "New protocol text",
    height=240,
    placeholder="Paste new protocol text here...",
    key="pai_new_text"
)
st.caption(f"New text characters: {len(new_text)}/12000")

if st.button("Run amendment impact review"):
    if not old_text.strip() or not new_text.strip():
        st.warning("Please paste both old and new protocol text before running the amendment impact review.")
    elif len(old_text) > 12000 or len(new_text) > 12000:
        st.error("Public demo limit reached: one or both text boxes exceed 12,000 characters. For larger reviews or supported workflows, contact us for pricing.")
        st.session_state.pai_done = False
    else:
        findings, table_rows = detect_amendment_findings(old_text, new_text)
        report_text = build_report(old_text, new_text, findings, table_rows)
        st.session_state.pai_last_old_text = old_text
        st.session_state.pai_last_new_text = new_text
        st.session_state.pai_last_findings = findings
        st.session_state.pai_last_table_rows = table_rows
        st.session_state.pai_last_report = report_text
        st.session_state.pai_done = True
        st.session_state.pai_ai_summary = ""
        st.session_state.pai_quality_review_open = False
        st.rerun()

st.divider()

if not st.session_state.pai_done and not old_text.strip() and not new_text.strip():
    st.info("Start by loading the sample texts or pasting old and new protocol text to evaluate.")

if st.session_state.pai_done:
    last_old_text = st.session_state.pai_last_old_text
    last_new_text = st.session_state.pai_last_new_text
    findings = st.session_state.pai_last_findings
    table_rows = st.session_state.pai_last_table_rows
    report_text = st.session_state.pai_last_report

    st.success("Protocol amendment impact review complete.")
    st.info("This output is generated by a limited deterministic amendment-impact engine. It does not determine formal amendment classification, ethics requirements, or final regulatory obligations. Human review is required.")
    st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no final amendment-classification or ethics-submission determination.")

    st.download_button(
        label="Download text report",
        data=report_text,
        file_name="protocol_amendment_impact_analyzer_report.txt",
        mime="text/plain"
    )

    transparency_pdf = build_transparency_report_pdf(last_old_text, last_new_text, findings, table_rows)

    st.download_button(
        label="Download Transparency & Oversight Report (PDF)",
        data=transparency_pdf,
        file_name="protocol_amendment_impact_analyzer_transparency_report.pdf",
        mime="application/pdf"
    )

    st.subheader("Findings")
    if findings:
        for finding in findings:
            render_finding(finding)
            st.divider()
    else:
        st.info("No amendment-impact findings were triggered by the current v1 rule set.")

    st.subheader("Amendment impact table")
    if table_rows:
        st.dataframe(table_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No amendment-impact rows available from the current v1 rule set.")

    st.subheader("AI summary")
    allowed, ai_message = ai_summary_allowed(last_old_text, last_new_text)
    if allowed:
        if st.button("Generate AI summary"):
            st.session_state.pai_ai_notice_open = True
            st.rerun()
        else:
            st.caption("AI summary is available for this input under current public-demo limits.")

        if st.session_state.get("pai_ai_notice_open"):
            render_ai_data_notice()
            col_ai_1, col_ai_2 = st.columns(2)
            with col_ai_1:
                if st.button("No, I don't want to use AI", key="pai_ai_notice_cancel"):
                    st.session_state.pai_ai_notice_open = False
                    st.rerun()
            with col_ai_2:
                if st.button("Yes, I understand and confirm the submitted text is example, synthetic, public, or fully anonymised.", key="pai_ai_notice_confirm"):
                    with st.spinner("Generating AI summary..."):
                        try:
                            st.session_state.pai_ai_summary = generate_ai_summary(last_old_text, last_new_text, findings, table_rows)
                            st.session_state.pai_ai_notice_open = False
                            st.rerun()
                        except Exception as e:
                            st.session_state.pai_ai_notice_open = False
                            st.warning(f"AI summary is temporarily unavailable. Deterministic review remains available. Details: {e}")

        if st.session_state.pai_ai_summary:
            render_structured_ai_summary(st.session_state.pai_ai_summary)
    else:
        st.warning(ai_message)

    st.divider()
    st.subheader("Result Quality Review")
    st.caption("Review how this result can be further analyzed in a private deployment, with deeper case-specific quality checks and internal QA support.")

    if st.button("Open Quality Review"):
        st.session_state.pai_quality_review_open = True
        st.rerun()

    if st.session_state.get("pai_quality_review_open"):
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

    with st.expander("Preview pasted old protocol text"):
        st.write(last_old_text[:1200])

    with st.expander("Preview pasted new protocol text"):
        st.write(last_new_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
st.markdown("[Having issues? drop us an email](mailto:hello@lippershey.co)")
