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

SAMPLE_TEXT = """KOL conflict review input

KOL:
Dr. Elena Markovic

Role / context:
Speaker deck review for oncology advisory event

Disclosed relationships:
Consulting fees from NovaThera in 2024.
Advisory board participation for Helix Bio in 2025.

Content signals:
The slide deck includes discussion of CLDN18.2-targeted therapies and mentions NovaThera data.
The speaker introduces comparative positioning language against a competing gastric cancer regimen.
No disclosure slide is included in the extracted text.
"""

CONFLICT_RULES = [
    {
        "title": "Named company relationship detected",
        "patterns": [r"\bconsulting fees\b", r"\badvisory board\b", r"\bdisclosed relationships\b"],
        "type": "Relationship disclosure context",
        "why": "The text appears to include an external company relationship relevant for conflict review.",
    },
    {
        "title": "Promotional or comparative positioning signal detected",
        "patterns": [r"\bcomparative positioning\b", r"\bcompeting\b", r"\bversus\b", r"\bagainst\b"],
        "type": "Comparative / positioning signal",
        "why": "The text appears to include comparative or positioning language that may warrant closer conflict and disclosure review.",
    },
    {
        "title": "Product/company mention in content detected",
        "patterns": [r"\bnovathera\b", r"\bhelix bio\b", r"\btargeted therapies\b", r"\bdata\b"],
        "type": "Content-company overlap",
        "why": "The text appears to include company or product references that may overlap with disclosed relationships.",
    },
    {
        "title": "Possible missing disclosure slide detected",
        "patterns": [r"\bno disclosure slide\b", r"\bno disclosure\b", r"\bnot disclosed\b"],
        "type": "Disclosure completeness signal",
        "why": "The text appears to suggest that disclosure presentation may be missing or incomplete.",
    },
]

def sentence_snippet(text: str, match_start: int, max_len: int = 240) -> str:
    start = max(text.rfind(".", 0, match_start), text.rfind("\n", 0, match_start))
    end_dot = text.find(".", match_start)
    end_nl = text.find("\n", match_start)
    candidates = [x for x in [end_dot, end_nl] if x != -1]
    end = min(candidates) if candidates else len(text)
    start = 0 if start == -1 else start + 1
    snippet = " ".join(text[start:end].strip().split())
    if len(snippet) > max_len:
        snippet = snippet[:max_len].rsplit(" ", 1)[0] + "..."
    return snippet

def extract_kol_name(text: str) -> str:
    m = re.search(r"KOL:\s*(.+)", text, flags=re.IGNORECASE)
    return m.group(1).strip() if m else "Not clearly stated"

def extract_context(text: str) -> str:
    m = re.search(r"Role / context:\s*(.+)", text, flags=re.IGNORECASE)
    return m.group(1).strip() if m else "Not clearly stated"

def looks_like_kol_scope(text: str) -> bool:
    lower_text = text.lower()
    scope_terms = [
        "kol",
        "speaker",
        "disclosed relationships",
        "consulting fees",
        "advisory board",
        "disclosure slide",
        "oncology advisory event",
        "comparative positioning",
        "speaker deck",
        "conflict",
        "novathera",
        "helix bio",
    ]
    return any(term in lower_text for term in scope_terms)


def ai_summary_allowed(text: str):
    if len(text) > 3500:
        return False, "Deterministic review completed. AI summary is limited to 3,500 characters in the public demo. For larger inputs and extended review support, contact us for pricing."
    if not looks_like_kol_scope(text):
        return False, "This public demo AI summary is limited to KOL, speaker, disclosure, or conflict-review text. For broader document review or custom workflows, contact us for pricing."
    return True, ""


def detect_kol_findings(text: str):
    findings = []
    table_rows = []
    kol_name = extract_kol_name(text)
    context = extract_context(text)

    for rule in CONFLICT_RULES:
        matched = None
        for pat in rule["patterns"]:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                matched = m
                break

        if matched:
            snippet = sentence_snippet(text, matched.start())
            findings.append({
                "title": rule["title"],
                "risk_level": "Info",
                "why_flagged": rule["why"],
                "matched_text": snippet,
                "rule_reference": "KOL conflict heuristic",
                "review_note": "Human review required.",
            })
            table_rows.append({
                "KOL": kol_name,
                "Context": context,
                "Conflict Element": rule["type"],
                "Evidence": snippet,
                "Suggested Review Direction": "Check whether disclosed relationships, speaker materials, and event documentation are aligned and complete.",
            })

    return findings, table_rows

def build_report(text: str, findings: list[dict], table_rows: list[dict]) -> str:
    report = []
    report.append("KOL-CONFLICT-SCANNER REPORT")
    report.append("")
    report.append("This public demo uses a limited deterministic conflict-review engine.")
    report.append("It does not determine legal conflict status, compliance approval, or final speaker eligibility.")
    report.append("Human review is required.")
    report.append("No PDF or DOCX support is included in this public demo step.")
    report.append("")
    report.append("INPUT SUMMARY")
    report.append(f"Input length: {len(text)} characters")
    report.append(f"Rows detected: {len(table_rows)}")
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
        report.append("No KOL conflict findings were triggered by the current v1 rule set.")
        report.append("")

    report.append("KOL CONFLICT TABLE")
    if table_rows:
        for row in table_rows:
            report.append(
                f"- {row['KOL']} | {row['Context']} | {row['Conflict Element']}"
            )
    else:
        report.append("- No conflict rows available")
    report.append("")
    report.append("SCOPE LIMITS")
    report.append("- Text-only demo")
    report.append("- No PDF or DOCX support in this step")
    report.append("- No final conflict or compliance determination")
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
    lines.append("Top KOL conflict review signals:")
    for finding in findings[:3]:
        lines.append(f"- {finding['title']} ({finding['risk_level']})")
    if table_rows:
        lines.append("")
        lines.append("Detected conflict-review context:")
        for row in table_rows[:2]:
            lines.append(f"- {row['KOL']} | {row['Context']} | {row['Conflict Element']}")
    lines.append("")
    lines.append("Human review is still required.")
    return "\n".join(lines)


def generate_ai_summary(text: str, findings: list[dict], table_rows: list[dict]) -> str:
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
            f"- {row['KOL']} | {row['Context']} | {row['Conflict Element']} | {row['Evidence']} | {row['Suggested Review Direction']}"
            for row in table_rows
        ]
    ) or "- No conflict rows available."

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = (
        "You are an assistive KOL conflict-review summarizer. "
        "You must summarize only the deterministic findings and conflict-review table provided to you, plus limited clearly grounded interpretation that directly follows from those findings. "
        "Do not invent new findings. "
        "Do not state PASS or FAIL. "
        "Do not state that a conflict exists, that disclosure is legally insufficient, or that the speaker should be approved or rejected unless that was already explicitly established in the deterministic findings. "
        "Do not make definitive legal, medical, compliance, or regulatory judgments. "
        "Be concise, practical, and plain-English. "
        "Your output must use exactly these section headings in this exact order: "
        "'Main review concerns', 'Likely reviewer focus', 'Suggested next step'. "
        "End with the exact sentence: 'Human review is required.'"
    )

    user_prompt = f"""
KOL / disclosure / speaker-review text:
{text}

Deterministic findings:
{findings_text}

Conflict-review table:
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
- Do not add new findings not supported by the deterministic findings or conflict-review table.
- Do not use bullet points.
- Do not output PASS or FAIL.
- Do not say that a conflict exists, that disclosure is legally insufficient, or that the speaker should be approved or rejected.
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
        "- System: KOL-Conflict-Scanner",
        "- Deterministic layer: source of truth for findings in the public demo",
        "- AI layer: optional assistive summary only; it does not replace deterministic findings",
        "",
        "2. INPUT CONTEXT",
        f"- Input length: {len(text_input)} characters",
        f"- Conflict-review rows detected: {len(table_rows)}",
        "",
        "3. HOW THE SYSTEM WORKS",
        "- The deterministic engine checks KOL, speaker, and disclosure-related text against a fixed set of conflict-review heuristics.",
        "- The AI layer summarizes deterministic findings and conflict-review table outputs in plain language.",
        "- Human review remains required.",
        "",
        "4. CONFLICT-REVIEW LOGIC USED IN THIS DEMO",
        "- Relationship-disclosure context detection",
        "- Comparative / positioning signal detection",
        "- Content-company overlap detection",
        "- Disclosure completeness signal detection",
        "- Conflict-review table generation",
        "",
        "5. CURRENT SNAPSHOT",
        f"- High-risk findings: {high_count}",
        f"- Medium-risk findings: {medium_count}",
        f"- Low-risk findings: {low_count}",
        f"- Info findings: {info_count}",
        "",
        "6. HUMAN OVERSIGHT",
        "- This tool is assistive only.",
        "- It does not determine legal conflict status, compliance approval, or final speaker eligibility.",
        "- It does not provide legal, medical, compliance, or regulatory approval.",
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

    c.setTitle("KOL-Conflict-Scanner Transparency & Oversight Report")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left, y, "KOL-Conflict-Scanner Transparency & Oversight Report")
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

st.set_page_config(page_title="KOL-Conflict-Scanner", layout="wide")

defaults = {
    "kol_text": "",
    "kol_done": False,
    "kol_last_text": "",
    "kol_last_findings": [],
    "kol_last_table_rows": [],
    "kol_last_report": "",
    "kol_ai_summary": "",
    "kol_ai_notice_open": False,
    "kol_quality_review_open": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("KOL-Conflict-Scanner")
st.caption("Review KOL-related text for visible disclosure, relationship, and conflict-alignment signals.")

with st.expander("How this tool works", expanded=True):
    st.markdown("""
### Deterministic conflict-review engine
This tool checks submitted KOL-related text against a limited set of v1 conflict-review heuristics.
This deterministic layer is the **source of truth** for findings shown in the public demo.

### Claude-based AI summary
An optional Claude-based AI summary layer can later rewrite deterministic findings into a more readable reviewer note.
This AI layer is **assistive only**. It does not replace deterministic findings or human review.


### Demo rules depth
This public demo uses a **limited deterministic rules pack** with **restricted edge-case coverage**.

To unlock **Private Pilot** with the **full deep rules pack**, **expanded edge-case coverage**, and **rules updates**, contact [hello@lippershey.co](mailto:hello@lippershey.co) or see more details [here](https://standardagentics.ai/pricing).

### Public demo limits
- Paste plain text only
- KOL / speaker / disclosure review text only
- Deterministic review up to 12,000 characters
- AI summary limited to smaller inputs and restricted public-demo usage
- No PDF or DOCX support in the public demo
- No confidential, patient, or business-sensitive data

[Having issues? drop us an email](mailto:hello@lippershey.co)
    """)

with st.expander("How to use", expanded=False):
    st.markdown("""
1. Paste KOL, speaker, advisory, or disclosure-related text
2. Click **Run conflict scan**
3. Review deterministic findings
4. Review the KOL conflict table
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
        st.session_state.kol_text = SAMPLE_TEXT
        st.session_state.kol_done = False
        st.session_state.kol_ai_summary = ""
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.kol_text = ""
        st.session_state.kol_done = False
        st.session_state.kol_last_text = ""
        st.session_state.kol_last_findings = []
        st.session_state.kol_last_table_rows = []
        st.session_state.kol_last_report = ""
        st.session_state.kol_ai_summary = ""
        st.session_state.kol_quality_review_open = False
        st.rerun()

with top_col3:
    st.caption("Use the sample KOL text for a quick demo, or reset the form.")

text = st.text_area(
    "KOL / disclosure / speaker-review text",
    height=320,
    placeholder="Paste KOL or disclosure-related text here...",
    key="kol_text"
)
st.caption(f"Characters: {len(text)}/12000")

if st.button("Run conflict scan"):
    if not text.strip():
        st.warning("Please paste KOL-related text before running the conflict scan.")
    elif len(text) > 12000:
        st.error("Public demo limit reached: this text exceeds 12,000 characters. For larger reviews or supported workflows, contact us for pricing.")
        st.session_state.kol_done = False
    else:
        findings, table_rows = detect_kol_findings(text)
        report_text = build_report(text, findings, table_rows)
        st.session_state.kol_last_text = text
        st.session_state.kol_last_findings = findings
        st.session_state.kol_last_table_rows = table_rows
        st.session_state.kol_last_report = report_text
        st.session_state.kol_done = True
        st.session_state.kol_ai_summary = ""
        st.session_state.kol_quality_review_open = False
        st.rerun()

st.divider()

if not st.session_state.kol_done and not text.strip():
    st.info("Start by loading the sample text or pasting KOL-related text to evaluate.")

if st.session_state.kol_done:
    last_text = st.session_state.kol_last_text
    findings = st.session_state.kol_last_findings
    table_rows = st.session_state.kol_last_table_rows
    report_text = st.session_state.kol_last_report

    st.success("KOL conflict review complete.")
    st.info("This output is generated by a limited deterministic conflict-review engine. It does not determine legal conflict status, compliance approval, or final speaker eligibility. Human review is required.")
    st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no final conflict or compliance determination.")

    st.download_button(
        label="Download text report",
        data=report_text,
        file_name="kol_conflict_scanner_report.txt",
        mime="text/plain"
    )

    transparency_pdf = build_transparency_report_pdf(last_text, findings, table_rows)

    st.download_button(
        label="Download Transparency & Oversight Report (PDF)",
        data=transparency_pdf,
        file_name="kol_conflict_scanner_transparency_report.pdf",
        mime="application/pdf"
    )

    st.subheader("Findings")
    if findings:
        for finding in findings:
            render_finding(finding)
            st.divider()
    else:
        st.info("No KOL conflict findings were triggered by the current v1 rule set.")

    st.subheader("KOL conflict table")
    if table_rows:
        st.dataframe(table_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No conflict rows available from the current v1 rule set.")

    st.subheader("AI summary")
    allowed, ai_message = ai_summary_allowed(last_text)
    if allowed:
        if st.button("Generate AI summary"):
            st.session_state.kol_ai_notice_open = True
            st.rerun()
        else:
            st.caption("AI summary is available for this input under current public-demo limits.")

        if st.session_state.get("kol_ai_notice_open"):
            render_ai_data_notice()
            col_ai_1, col_ai_2 = st.columns(2)
            with col_ai_1:
                if st.button("No, I don't want to use AI", key="kol_ai_notice_cancel"):
                    st.session_state.kol_ai_notice_open = False
                    st.rerun()
            with col_ai_2:
                if st.button("Yes, I understand and confirm the submitted text is example, synthetic, public, or fully anonymised.", key="kol_ai_notice_confirm"):
                    with st.spinner("Generating AI summary..."):
                        try:
                            st.session_state.kol_ai_summary = generate_ai_summary(last_text, findings, table_rows)
                            st.session_state.kol_ai_notice_open = False
                            st.rerun()
                        except Exception as e:
                            st.session_state.kol_ai_notice_open = False
                            st.warning(f"AI summary is temporarily unavailable. Deterministic review remains available. Details: {e}")

        if st.session_state.kol_ai_summary:
            render_structured_ai_summary(st.session_state.kol_ai_summary)
    else:
        st.warning(ai_message)

    st.divider()
    st.subheader("Result Quality Review")
    st.caption("Review how this result can be further analyzed in a private deployment, with deeper case-specific quality checks and internal QA support.")

    if st.button("Open Quality Review"):
        st.session_state.kol_quality_review_open = True
        st.rerun()

    if st.session_state.get("kol_quality_review_open"):
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

    with st.expander("Preview pasted KOL text"):
        st.write(last_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
st.markdown("[Having issues? drop us an email](mailto:hello@lippershey.co)")
