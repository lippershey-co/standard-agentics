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

SAMPLE_TEXT = """PSUR Draft Summary

Reporting interval:
01 Jan 2025 to 30 Jun 2025

Product:
VX-247

Executive summary:
The benefit-risk profile remains unchanged based on currently available data.

Worldwide marketing authorization status:
Authorized in EU and UK. US filing remains under review.

Actions taken for safety reasons:
No new urgent safety restrictions were introduced during the interval.

Changes to reference safety information:
Reference safety information was updated to include additional wording on hepatic monitoring.

Estimated exposure:
Cumulative exposure estimate is included for the interval with patient-exposure narrative.

Individual case safety data:
Case narrative trends are summarized, including serious hepatic events under ongoing evaluation.

Signal evaluation:
A hepatic safety signal remains under review. No final causal conclusion has been established.

Benefit-risk evaluation:
The overall benefit-risk profile remains favorable based on available evidence.

Conclusion:
Continued monitoring is recommended. No immediate variation action is proposed.
"""

PSUR_AREAS = [
    {
        "title": "Reporting interval",
        "strong": ["reporting interval"],
        "weak": ["interval"],
    },
    {
        "title": "Worldwide authorization status",
        "strong": ["worldwide marketing authorization status", "authorized in", "filing remains under review"],
        "weak": ["authorization status", "authorized"],
    },
    {
        "title": "Actions taken for safety reasons",
        "strong": ["actions taken for safety reasons", "urgent safety restrictions"],
        "weak": ["safety reasons", "restrictions"],
    },
    {
        "title": "Reference safety information changes",
        "strong": ["changes to reference safety information", "reference safety information was updated"],
        "weak": ["reference safety information", "updated"],
    },
    {
        "title": "Estimated exposure",
        "strong": ["estimated exposure", "cumulative exposure estimate", "patient-exposure narrative"],
        "weak": ["exposure"],
    },
    {
        "title": "Individual case safety data",
        "strong": ["individual case safety data", "case narrative trends", "serious hepatic events"],
        "weak": ["case narrative", "safety data"],
    },
    {
        "title": "Signal evaluation",
        "strong": ["signal evaluation", "signal remains under review"],
        "weak": ["signal", "under review"],
    },
    {
        "title": "Benefit-risk evaluation",
        "strong": ["benefit-risk evaluation", "benefit-risk profile remains favorable"],
        "weak": ["benefit-risk", "benefit risk"],
    },
    {
        "title": "Conclusion",
        "strong": ["conclusion", "continued monitoring is recommended"],
        "weak": ["recommended", "monitoring"],
    },
]

def find_snippet(text: str, keyword: str, max_len: int = 220) -> str:
    if not text or not keyword:
        return ""

    lower_text = text.lower()
    lower_keyword = keyword.lower()
    idx = lower_text.find(lower_keyword)
    if idx == -1:
        return ""

    line_start = text.rfind("\n", 0, idx)
    line_end = text.find("\n", idx)

    line_start = 0 if line_start == -1 else line_start + 1
    line_end = len(text) if line_end == -1 else line_end

    snippet = text[line_start:line_end].strip()

    if len(snippet) < 40:
        start = max(0, idx - 80)
        end = min(len(text), idx + 160)
        snippet = text[start:end].strip()

    snippet = " ".join(snippet.split())
    if len(snippet) > max_len:
        snippet = snippet[:max_len].rsplit(" ", 1)[0] + "..."
    return snippet

def classify_psur_area(text: str, area: dict) -> dict:
    lower_text = text.lower()

    for keyword in area["strong"]:
        if keyword in lower_text:
            return {
                "status": "Present",
                "why_flagged": f'Evidence of this PSUR area was detected via strong keyword match: "{keyword}".',
                "matched_text": find_snippet(text, keyword),
            }

    for keyword in area["weak"]:
        if keyword in lower_text:
            return {
                "status": "Partial",
                "why_flagged": f'Possible evidence of this PSUR area was detected via weaker keyword match: "{keyword}".',
                "matched_text": find_snippet(text, keyword),
            }

    return {
        "status": "Missing",
        "why_flagged": "No clear evidence of this PSUR area was detected in the submitted text.",
        "matched_text": "None detected",
    }

def looks_like_psur_scope(text: str) -> bool:
    lower_text = text.lower()
    scope_terms = [
        "psur",
        "reporting interval",
        "worldwide marketing authorization status",
        "actions taken for safety reasons",
        "reference safety information",
        "estimated exposure",
        "individual case safety data",
        "signal evaluation",
        "benefit-risk evaluation",
        "benefit risk evaluation",
        "pharmacovigilance",
    ]
    return any(term in lower_text for term in scope_terms)


def ai_summary_allowed(text: str):
    if len(text) > 3500:
        return False, "Deterministic review completed. AI summary is limited to 3,500 characters in the public demo. For larger inputs and extended review support, contact us for pricing."
    if not looks_like_psur_scope(text):
        return False, "This public demo AI summary is limited to PSUR, pharmacovigilance, or related safety-report text. For broader document review or custom workflows, contact us for pricing."
    return True, ""


def detect_psur_gaps(text: str):
    findings = []
    table_rows = []

    for area in PSUR_AREAS:
        result = classify_psur_area(text, area)
        recommended_action = {
            "Present": "Documented evidence appears present. Confirm the section is complete and retained in formal PSUR records.",
            "Partial": "Add more explicit section detail or completion evidence before relying on this PSUR area as complete.",
            "Missing": "Add a formal section, supporting evidence, or retained summary for this PSUR area.",
        }[result["status"]]

        findings.append({
            "title": area["title"],
            "status": result["status"],
            "why_flagged": result["why_flagged"],
            "matched_text": result["matched_text"],
            "reference_area": "PSUR completeness heuristic",
            "recommended_next_action": recommended_action,
            "review_note": "Human review required.",
        })

        table_rows.append({
            "PSUR Area": area["title"],
            "Status": result["status"],
            "Evidence": result["matched_text"],
            "Next Action": recommended_action,
        })

    return findings, table_rows

def compute_score(findings: list[dict]) -> tuple[int, int, int, float]:
    present = sum(1 for f in findings if f["status"] == "Present")
    partial = sum(1 for f in findings if f["status"] == "Partial")
    missing = sum(1 for f in findings if f["status"] == "Missing")
    score = present + 0.5 * partial
    return present, partial, missing, score

def build_report(text: str, findings: list[dict], table_rows: list[dict]) -> str:
    present, partial, missing, score = compute_score(findings)

    report = []
    report.append("PSUR-GAP-DETECTOR REPORT")
    report.append("")
    report.append("This public demo uses a limited deterministic completeness engine.")
    report.append("It does not determine regulatory adequacy or submission acceptability.")
    report.append("Human review is required.")
    report.append("No PDF or DOCX support is included in this public demo step.")
    report.append("")
    report.append("INPUT SUMMARY")
    report.append(f"PSUR draft length: {len(text)} characters")
    report.append("")
    report.append("READINESS SUMMARY")
    report.append(f"PSUR areas checked: {len(findings)}")
    report.append(f"Present: {present}")
    report.append(f"Partial: {partial}")
    report.append(f"Missing: {missing}")
    report.append(f"Readiness score: {score:.1f}/{len(findings)}")
    report.append("")
    report.append("READINESS RESULTS")

    for i, finding in enumerate(findings, start=1):
        report.append(f"{i}. {finding['title']}")
        report.append(f"   Status: {finding['status']}")
        report.append(f"   Why flagged: {finding['why_flagged']}")
        report.append(f"   Matched text: {finding['matched_text']}")
        report.append(f"   Reference area: {finding['reference_area']}")
        report.append(f"   Recommended next action: {finding['recommended_next_action']}")
        report.append(f"   Review note: {finding['review_note']}")
        report.append("")

    report.append("PSUR COMPLETENESS TABLE")
    for row in table_rows:
        report.append(f"- {row['PSUR Area']} | {row['Status']}")

    report.append("")
    report.append("SCOPE LIMITS")
    report.append("- Text-only demo")
    report.append("- No PDF or DOCX support in this step")
    report.append("- No final regulatory adequacy determination")
    report.append("")
    return "\n".join(report)

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
    present = sum(1 for f in findings if f["status"] == "Present")
    partial = sum(1 for f in findings if f["status"] == "Partial")
    missing = sum(1 for f in findings if f["status"] == "Missing")
    lines.append(f"Present: {present}")
    lines.append(f"Partial: {partial}")
    lines.append(f"Missing: {missing}")
    lines.append("Top flagged PSUR areas:")
    for row in table_rows[:3]:
        lines.append(f"- {row['PSUR Area']} | {row['Status']}")
    lines.append("")
    lines.append("Human review is still required.")
    return "\n".join(lines)


def generate_ai_summary(text: str, findings: list[dict], table_rows: list[dict]) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "AI summary is not available because ANTHROPIC_API_KEY is not set on this runtime."

    findings_text = "\n".join(
        [
            f"- {f['title']} | Status: {f['status']} | Why: {f['why_flagged']} | Matched: {f['matched_text']} | Reference: {f['reference_area']}"
            for f in findings
        ]
    ) or "- No deterministic findings triggered."

    table_text = "\n".join(
        [
            f"- {row['PSUR Area']} | {row['Status']} | {row['Evidence']} | {row['Next Action']}"
            for row in table_rows
        ]
    ) or "- No table rows available."

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = (
        "You are an assistive PSUR-readiness summarizer. "
        "You must summarize only the deterministic findings and completeness table provided to you, plus limited clearly grounded interpretation that directly follows from those findings. "
        "Do not invent new findings. "
        "Do not state PASS or FAIL. "
        "Do not state the draft is adequate, accepted, approved, or final unless that was already explicitly established in the deterministic findings. "
        "Do not make definitive legal, medical, or regulatory judgments. "
        "Be concise, practical, and plain-English. "
        "Your output must use exactly these section headings in this exact order: "
        "'Main review concerns', 'Likely reviewer focus', 'Suggested next step'. "
        "End with the exact sentence: 'Human review is required.'"
    )

    user_prompt = f"""
PSUR / safety-report text:
{text}

Deterministic findings:
{findings_text}

Completeness table:
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
- Do not add new findings not supported by the deterministic findings or completeness table.
- Do not use bullet points.
- Do not output PASS or FAIL.
- Do not say the draft is adequate, accepted, approved, or final.
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



def build_transparency_report_text(text_input: str = "", findings=None, table_rows=None) -> str:
    report_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    findings = findings or []
    table_rows = table_rows or []

    present = sum(1 for f in findings if f.get("status") == "Present")
    partial = sum(1 for f in findings if f.get("status") == "Partial")
    missing = sum(1 for f in findings if f.get("status") == "Missing")

    lines = [
        "TRANSPARENCY & OVERSIGHT REPORT",
        "",
        f"Generated: {report_date}",
        "",
        "1. SYSTEM IDENTITY",
        "- System: PSUR-Gap-Detector",
        "- Deterministic layer: source of truth for findings in the public demo",
        "- AI layer: optional assistive summary only; it does not replace deterministic findings",
        "",
        "2. INPUT CONTEXT",
        f"- PSUR draft length: {len(text_input)} characters",
        f"- PSUR areas checked: {len(table_rows)}",
        "",
        "3. HOW THE SYSTEM WORKS",
        "- The deterministic engine checks PSUR text against a fixed completeness checklist.",
        "- The AI layer summarizes deterministic findings and completeness outputs in plain language.",
        "- Human review remains required.",
        "",
        "4. READINESS LOGIC USED IN THIS DEMO",
        "- Reporting interval",
        "- Worldwide authorization status",
        "- Actions taken for safety reasons",
        "- Reference safety information changes",
        "- Estimated exposure",
        "- Individual case safety data",
        "- Signal evaluation",
        "- Benefit-risk evaluation",
        "- Conclusion",
        "",
        "5. CURRENT READINESS SNAPSHOT",
        f"- Present: {present}",
        f"- Partial: {partial}",
        f"- Missing: {missing}",
        "",
        "6. HUMAN OVERSIGHT",
        "- This tool is assistive only.",
        "- It does not determine regulatory adequacy or submission acceptability.",
        "- It does not provide legal, medical, or regulatory approval.",
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
        "- Deterministic review up to 12,000 characters",
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


def build_transparency_report_pdf(text_input: str = "", findings=None, table_rows=None) -> bytes:
    report_text = build_transparency_report_text(text_input, findings, table_rows)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left = 18 * mm
    top = height - 18 * mm
    line_height = 6 * mm
    y = top

    c.setTitle("PSUR-Gap-Detector Transparency & Oversight Report")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left, y, "PSUR-Gap-Detector Transparency & Oversight Report")
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

def render_status_badge(status: str):
    if status == "Present":
        st.success(f"Status: {status}")
    elif status == "Partial":
        st.warning(f"Status: {status}")
    elif status == "Missing":
        st.error(f"Status: {status}")
    else:
        st.write(f"Status: {status}")

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
    render_status_badge(finding["status"])
    st.write(f"**Why it was flagged:** {finding['why_flagged']}")
    st.write(f"**Matched text snippet:** {finding['matched_text']}")
    st.write(f"**Reference area:** {finding['reference_area']}")
    st.write(f"**Recommended next action:** {finding['recommended_next_action']}")
    st.write(f"**Review note:** {finding['review_note']}")

st.set_page_config(page_title="PSUR-Gap-Detector", layout="wide")

defaults = {
    "psur_text": "",
    "psur_done": False,
    "psur_last_text": "",
    "psur_last_findings": [],
    "psur_last_table_rows": [],
    "psur_last_report": "",
    "psur_ai_summary": "",
    "psur_ai_notice_open": False,
    "psur_quality_review_open": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("PSUR-Gap-Detector")
st.caption("Audit a PSUR draft summary for possible missing or incomplete section coverage before formal regulatory review.")

with st.expander("How this tool works", expanded=True):
    st.markdown("""
### Deterministic completeness engine
This tool checks submitted PSUR text against a limited set of v1 completeness areas.
This deterministic layer is the **source of truth** for findings shown in the public demo.

### Claude-based AI summary
An optional Claude-based AI summary layer can later rewrite deterministic findings into a more readable reviewer note.
This AI layer is **assistive only**. It does not replace deterministic findings or human review.


### Demo rules depth
This public demo uses a **limited deterministic rules pack** with **restricted edge-case coverage**.

To unlock **Private Pilot** with the **full deep rules pack**, **expanded edge-case coverage**, and **rules updates**, contact [hello@lippershey.co](mailto:hello@lippershey.co) or see more details [here](https://standardagentics.ai/pricing).

### Public demo limits
- Paste plain text only
- PSUR / pharmacovigilance text only
- Deterministic review up to 12,000 characters
- AI summary limited to smaller inputs and restricted public-demo usage
- No PDF or DOCX support in the public demo
- No confidential, patient, or business-sensitive data

[Having issues? drop us an email](mailto:hello@lippershey.co)
    """)

with st.expander("How to use", expanded=False):
    st.markdown("""
1. Paste a PSUR draft or summary
2. Click **Run PSUR gap check**
3. Review deterministic completeness findings
4. Review the section completeness table
5. Optionally generate an AI summary in a later step
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
    if st.button("Load sample text"):
        st.session_state.psur_text = SAMPLE_TEXT
        st.session_state.psur_done = False
        st.session_state.psur_ai_summary = ""
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.psur_text = ""
        st.session_state.psur_done = False
        st.session_state.psur_last_text = ""
        st.session_state.psur_last_findings = []
        st.session_state.psur_last_table_rows = []
        st.session_state.psur_last_report = ""
        st.session_state.psur_ai_summary = ""
        st.session_state.psur_quality_review_open = False
        st.rerun()

with top_col3:
    st.caption("Use the sample PSUR summary for a quick demo, or reset the form.")

text = st.text_area(
    "PSUR draft summary",
    height=320,
    placeholder="Paste PSUR or PV summary text here...",
    key="psur_text"
)
st.caption(f"Characters: {len(text)}/12000")

if st.button("Run PSUR gap check"):
    if not text.strip():
        st.warning("Please paste PSUR text before running the gap check.")
    elif len(text) > 12000:
        st.error("Public demo limit reached: this text exceeds 12,000 characters. For larger PSUR reviews or supported workflows, contact us for pricing.")
        st.session_state.psur_done = False
    else:
        findings, table_rows = detect_psur_gaps(text)
        report_text = build_report(text, findings, table_rows)
        st.session_state.psur_last_text = text
        st.session_state.psur_last_findings = findings
        st.session_state.psur_last_table_rows = table_rows
        st.session_state.psur_last_report = report_text
        st.session_state.psur_done = True
        st.session_state.psur_ai_summary = ""
        st.session_state.psur_quality_review_open = False
        st.rerun()

st.divider()

if not st.session_state.psur_done and not text.strip():
    st.info("Start by loading the sample text or pasting a PSUR summary to evaluate.")

if st.session_state.psur_done:
    last_text = st.session_state.psur_last_text
    findings = st.session_state.psur_last_findings
    table_rows = st.session_state.psur_last_table_rows
    report_text = st.session_state.psur_last_report
    present, partial, missing, score = compute_score(findings)

    st.success("PSUR gap review complete.")
    st.info("This output is generated by a limited deterministic completeness engine. It does not determine regulatory adequacy or submission acceptability. Human review is required.")
    st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no final regulatory adequacy determination.")

    st.write(f"**Readiness summary:** Present: {present} | Partial: {partial} | Missing: {missing} | Score: {score:.1f}/{len(findings)}")

    st.download_button(
        label="Download text report",
        data=report_text,
        file_name="psur_gap_detector_report.txt",
        mime="text/plain"
    )

    transparency_pdf = build_transparency_report_pdf(last_text, findings, table_rows)

    st.download_button(
        label="Download Transparency & Oversight Report (PDF)",
        data=transparency_pdf,
        file_name="psur_gap_detector_transparency_report.pdf",
        mime="application/pdf"
    )

    st.subheader("Findings")
    if findings:
        for finding in findings:
            render_finding(finding)
            st.divider()
    else:
        st.info("No findings were triggered by the current v1 rule set.")

    st.subheader("PSUR completeness table")
    if table_rows:
        st.dataframe(table_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No completeness rows available from the current v1 rule set.")

    st.subheader("AI summary")
    allowed, ai_message = ai_summary_allowed(last_text)
    if allowed:
        if st.button("Generate AI summary"):
            st.session_state.psur_ai_notice_open = True
            st.rerun()
        else:
            st.caption("AI summary is available for this input under current public-demo limits.")

        if st.session_state.get("psur_ai_notice_open"):
            render_ai_data_notice()
            col_ai_1, col_ai_2 = st.columns(2)
            with col_ai_1:
                if st.button("No, I don't want to use AI", key="psur_ai_notice_open_cancel"):
                    st.session_state.psur_ai_notice_open = False
                    st.rerun()
            with col_ai_2:
                if st.button("Yes, I understand and confirm the submitted text is example, synthetic, public, or fully anonymised.", key="psur_ai_notice_open_confirm"):
                    with st.spinner("Generating AI summary..."):
                        try:
                            st.session_state.psur_ai_summary = generate_ai_summary(last_text, findings, table_rows)
                            st.session_state.psur_ai_notice_open = False
                            st.rerun()
                        except Exception as e:
                            st.session_state.psur_ai_notice_open = False
                            st.warning(f"AI summary is temporarily unavailable. Deterministic review remains available. Details: {e}")

        if st.session_state.psur_ai_summary:
            render_structured_ai_summary(st.session_state.psur_ai_summary)
    else:
        st.warning(ai_message)

    st.divider()
    st.subheader("Result Quality Review")
    st.caption("Review how this result can be further analyzed in a private deployment, with deeper case-specific quality checks and internal QA support.")

    if st.button("Open Quality Review"):
        st.session_state.psur_quality_review_open = True
        st.rerun()

    if st.session_state.get("psur_quality_review_open"):
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

    with st.expander("Preview pasted PSUR text"):
        st.write(last_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
st.markdown("[Having issues? drop us an email](mailto:hello@lippershey.co)")
