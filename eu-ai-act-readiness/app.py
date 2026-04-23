import os
import re
from io import BytesIO
from datetime import datetime
import streamlit as st
import anthropic
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

SAMPLE_USE_CASE_TEXT = """We use an AI system to screen oncology trial candidates based on structured patient data and clinical notes.
The system ranks likely eligible patients for manual review by the study team.
Outputs are reviewed by humans before any enrollment decision is made.
We maintain audit logs, document model versions, and review system performance regularly.
The process includes validation, monitoring, and incident escalation to the digital governance team.
"""

STRONG_SIGNALS = {
    "Human oversight": ["human review", "reviewed by humans", "human oversight", "manual review", "override"],
    "Risk management": ["risk management", "risk mitigation", "identified risks", "residual risk"],
    "Data governance": ["data governance", "data quality", "representative", "bias testing", "data provenance"],
    "Technical documentation": ["technical documentation", "model versions", "system architecture", "documentation"],
    "Logging / record-keeping": ["audit logs", "logging", "record-keeping", "traceability"],
    "Transparency / instructions for use": ["intended use", "instructions for use", "transparency", "limitations"],
    "Accuracy / robustness / validation / monitoring": ["validation", "monitoring", "accuracy", "robustness", "performance"],
    "Quality management / governance process": ["quality management", "governance", "governance team", "qms"],
    "Post-market monitoring / incident handling": ["incident escalation", "post-market monitoring", "serious incident", "surveillance"],
}

WEAK_SIGNALS = {
    "Human oversight": ["review", "human"],
    "Risk management": ["risk"],
    "Data governance": ["ehr", "dataset", "data"],
    "Technical documentation": ["documented", "documentation"],
    "Logging / record-keeping": ["log"],
    "Transparency / instructions for use": ["instructions", "use"],
    "Accuracy / robustness / validation / monitoring": ["real-world evidence", "performance"],
    "Quality management / governance process": ["governance", "committee"],
    "Post-market monitoring / incident handling": ["incident", "escalation"],
}


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

    snippet = snippet.replace("**", "")
    snippet = snippet.replace("__", "")
    snippet = " ".join(snippet.split())

    if len(snippet) > max_len:
        snippet = snippet[:max_len].rsplit(" ", 1)[0] + "..."

    return snippet


def classify_area(text: str, area: str) -> dict:
    lower_text = text.lower()

    for keyword in STRONG_SIGNALS[area]:
        if keyword in lower_text:
            return {
                "status": "Present",
                "why_flagged": f'Evidence of this readiness area was detected via strong keyword match: "{keyword}".',
                "matched_text": find_snippet(text, keyword),
            }

    for keyword in WEAK_SIGNALS[area]:
        if keyword in lower_text:
            return {
                "status": "Partial",
                "why_flagged": f'Possible evidence of this readiness area was detected via weaker keyword match: "{keyword}".',
                "matched_text": find_snippet(text, keyword),
            }

    return {
        "status": "Missing",
        "why_flagged": "No clear evidence of this readiness area was detected in the submitted text.",
        "matched_text": "None detected",
    }


def looks_like_eu_ai_act_scope(text: str) -> bool:
    lower_text = text.lower()
    scope_terms = [
        "ai system", "human oversight", "risk management", "data governance",
        "technical documentation", "logging", "validation", "monitoring",
        "governance", "incident", "transparency", "instructions for use",
        "quality management", "post-market", "serious incident"
    ]
    return any(term in lower_text for term in scope_terms)


def ai_summary_allowed(text: str) -> tuple[bool, str]:
    if len(text) > 3500:
        return False, "Deterministic review completed. AI summary is limited to 3,500 characters in the public demo. For larger inputs and extended review support, contact us for pricing."
    if not looks_like_eu_ai_act_scope(text):
        return False, "This public demo AI summary is limited to EU AI Act readiness or governance text. For broader document review or custom workflows, contact us for pricing."
    return True, ""


def detect_readiness(use_case_text: str) -> list[dict]:
    areas = [
        "Human oversight",
        "Risk management",
        "Data governance",
        "Technical documentation",
        "Logging / record-keeping",
        "Transparency / instructions for use",
        "Accuracy / robustness / validation / monitoring",
        "Quality management / governance process",
        "Post-market monitoring / incident handling",
    ]

    findings = []
    for area in areas:
        result = classify_area(use_case_text, area)
        recommended_action = {
            "Present": "Documented evidence appears present. Confirm the process is operational and retained in formal records.",
            "Partial": "Add more explicit language and retained evidence for this area so it is easier to verify.",
            "Missing": "Add a formal description and retained evidence for this readiness area.",
        }[result["status"]]

        findings.append({
            "title": area,
            "status": result["status"],
            "why_flagged": result["why_flagged"],
            "matched_text": result["matched_text"],
            "reference_area": f"EU AI Act — {area}",
            "recommended_next_action": recommended_action,
            "review_note": "Human review required.",
        })

    return findings


def compute_score(findings: list[dict]) -> tuple[int, int, int, float]:
    present = sum(1 for f in findings if f["status"] == "Present")
    partial = sum(1 for f in findings if f["status"] == "Partial")
    missing = sum(1 for f in findings if f["status"] == "Missing")
    score = present + 0.5 * partial
    return present, partial, missing, score


def build_report(use_case_text: str, findings: list[dict]) -> str:
    present, partial, missing, score = compute_score(findings)

    report = []
    report.append("EU-AI-ACT-READINESS REPORT")
    report.append("")
    report.append("This public demo uses a limited deterministic checklist engine.")
    report.append("It does not make a legal determination.")
    report.append("Human review is required.")
    report.append("No PDF or DOCX support is included in this public demo step.")
    report.append("")
    report.append("INPUT SUMMARY")
    report.append(f"Use-case description length: {len(use_case_text)} characters")
    report.append("")
    report.append("READINESS SUMMARY")
    report.append(f"Readiness areas checked: {len(findings)}")
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

    report.append("SCOPE LIMITS")
    report.append("- Text-only demo")
    report.append("- No PDF or DOCX support in this step")
    report.append("- No legal determination")
    report.append("- No definitive compliance classification")
    report.append("")
    return "\n".join(report)


def generate_ai_summary_placeholder(findings: list[dict]) -> str:
    if not findings:
        return (
            "No deterministic findings were triggered by the current v1 rule set. "
            "Once connected, the Claude-based AI summary will turn this result into a short plain-language executive note."
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
    lines.append("Top flagged areas:")
    for finding in findings[:3]:
        lines.append(f"- {finding['title']} ({finding['status']})")
    lines.append("")
    lines.append("Human review is still required.")
    return "\n".join(lines)


def generate_ai_summary(use_case_text: str, findings: list[dict]) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "AI summary is not available because ANTHROPIC_API_KEY is not set on this runtime."

    findings_text = "\n".join(
        [
            f"- {f['title']} | Status: {f['status']} | Why: {f['why_flagged']} | Reference: {f['reference_area']}"
            for f in findings
        ]
    ) or "- No deterministic findings triggered."

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = (
        "You are an assistive EU AI Act readiness summarizer. "
        "You must summarize only the deterministic findings provided to you, plus limited clearly grounded implications that directly follow from those findings. "
        "Do not invent new findings. "
        "Do not state PASS or FAIL. "
        "Do not state the system is compliant, approved, legal, or high-risk unless that was already explicitly established in the deterministic findings. "
        "Do not make definitive legal or regulatory judgments. "
        "Be concise, practical, and plain-English. "
        "Your output must use exactly these section headings in this exact order: "
        "'Main review concerns', 'Likely reviewer focus', 'Suggested next step'. "
        "End with the exact sentence: 'Human review is required.'"
    )

    user_prompt = f"""
Use-case text:
{use_case_text}

Deterministic findings:
{findings_text}

Write the response in this exact structure:

Main review concerns
<1 short paragraph summarizing the most important deterministic findings and any limited directly grounded implications.>

Likely reviewer focus
<1 short paragraph describing what a reviewer would most likely examine next, based only on the deterministic findings and clearly grounded implications.>

Suggested next step
<1 short paragraph with the most practical next action, based only on the deterministic findings.>

Human review is required.

Rules:
- Do not add new findings not supported by the deterministic findings.
- Do not use bullet points.
- Do not output PASS or FAIL.
- Do not say the system is compliant, approved, legal, or definitively classified.
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



def build_transparency_report_text(use_case_text: str = "", findings=None) -> str:
    report_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    findings = findings or []

    present = sum(1 for f in findings if f.get("status") == "Present")
    partial = sum(1 for f in findings if f.get("status") == "Partial")
    missing = sum(1 for f in findings if f.get("status") == "Missing")

    lines = [
        "TRANSPARENCY & OVERSIGHT REPORT",
        "",
        f"Generated: {report_date}",
        "",
        "1. SYSTEM IDENTITY",
        "- System: EU-AI-Act-Readiness",
        "- Deterministic layer: source of truth for findings in the public demo",
        "- AI layer: optional assistive summary only; it does not replace deterministic findings",
        "",
        "2. INPUT CONTEXT",
        f"- Use-case text length: {len(use_case_text)} characters",
        "",
        "3. HOW THE SYSTEM WORKS",
        "- The deterministic engine checks use-case text against a fixed EU AI Act readiness checklist.",
        "- The AI layer summarizes deterministic findings in plain language.",
        "- Human review remains required.",
        "",
        "4. READINESS LOGIC USED IN THIS DEMO",
        "- Human oversight",
        "- Risk management",
        "- Data governance",
        "- Technical documentation",
        "- Logging / record-keeping",
        "- Transparency / instructions for use",
        "- Accuracy / robustness / validation / monitoring",
        "- Quality management / governance process",
        "- Post-market monitoring / incident handling",
        "",
        "5. CURRENT READINESS SNAPSHOT",
        f"- Present: {present}",
        f"- Partial: {partial}",
        f"- Missing: {missing}",
        "",
        "6. HUMAN OVERSIGHT",
        "- This tool is assistive only.",
        "- It does not determine legal compliance.",
        "- It does not provide legal approval or definitive regulatory classification.",
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


def build_transparency_report_pdf(use_case_text: str = "", findings=None) -> bytes:
    report_text = build_transparency_report_text(use_case_text, findings)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left = 18 * mm
    top = height - 18 * mm
    line_height = 6 * mm
    y = top

    c.setTitle("EU-AI-Act-Readiness Transparency & Oversight Report")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left, y, "EU-AI-Act-Readiness Transparency & Oversight Report")
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


def render_status_badge(status: str):
    if status == "Present":
        st.success(f"Status: {status}")
    elif status == "Partial":
        st.warning(f"Status: {status}")
    elif status == "Missing":
        st.error(f"Status: {status}")
    else:
        st.write(f"Status: {status}")


def render_finding(finding: dict):
    st.markdown(f"### {finding['title']}")
    render_status_badge(finding["status"])
    st.write(f"**Why it was flagged:** {finding['why_flagged']}")
    st.write(f"**Matched text snippet:** {finding['matched_text']}")
    st.write(f"**Reference area:** {finding['reference_area']}")
    st.write(f"**Recommended next action:** {finding['recommended_next_action']}")
    st.write(f"**Review note:** {finding['review_note']}")


st.set_page_config(page_title="EU-AI-Act-Readiness", layout="wide")

defaults = {
    "euai_text": "",
    "euai_done": False,
    "euai_last_text": "",
    "euai_last_findings": [],
    "euai_last_report": "",
    "euai_ai_summary": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("EU-AI-Act-Readiness")
st.caption("Assess an AI use case against a limited public-demo readiness workflow.")

with st.expander("How this tool works", expanded=True):
    st.markdown("""
### Deterministic readiness engine
This tool first runs a deterministic checklist engine.  
It checks the submitted use-case text against a fixed set of readiness areas and evidence signals.  
This deterministic layer is the **source of truth** for findings shown in the public demo.

### Claude-based AI summary
An optional Claude-based AI summary layer can later rewrite deterministic findings into a more readable executive note.  
This AI layer is **assistive only**. It does not replace deterministic findings or human review.

### Public demo limits
- Paste plain text only
- EU AI Act readiness / governance text only
- Deterministic review: up to 12,000 characters
- AI summary: limited to smaller inputs and restricted public-demo usage
- No PDF or DOCX support in the public demo
- No confidential, patient, or business-sensitive data

[Having issues? drop us an email](mailto:hello@lippershey.co)
    """)

with st.expander("How to use", expanded=False):
    st.markdown("""
1. Paste an AI use-case or governance description
2. Click **Run readiness check**
3. Review deterministic findings and recommended next actions
4. Optionally generate an AI summary in a later step
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
        st.session_state.euai_text = SAMPLE_USE_CASE_TEXT
        st.session_state.euai_done = False
        st.session_state.euai_ai_summary = ""
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.euai_text = ""
        st.session_state.euai_done = False
        st.session_state.euai_last_text = ""
        st.session_state.euai_last_findings = []
        st.session_state.euai_last_report = ""
        st.session_state.euai_ai_summary = ""
        st.rerun()

with top_col3:
    st.caption("Use the sample AI use case for a quick demo, or reset the form.")

use_case_text = st.text_area(
    "AI use-case / governance text",
    height=320,
    placeholder="Paste AI use-case or governance text here...",
    key="euai_text"
)
st.caption(f"Characters: {len(use_case_text)}/12000")

if st.button("Run readiness check"):
    if not use_case_text.strip():
        st.warning("Please paste AI use-case text before running the readiness check.")
    elif len(use_case_text) > 12000:
        st.error("Public demo limit reached: this text exceeds 12,000 characters. For larger governance materials or supported workflows, contact us for pricing.")
        st.session_state.euai_done = False
    else:
        findings = detect_readiness(use_case_text)
        report_text = build_report(use_case_text, findings)
        st.session_state.euai_last_text = use_case_text
        st.session_state.euai_last_findings = findings
        st.session_state.euai_last_report = report_text
        st.session_state.euai_done = True
        st.session_state.euai_ai_summary = ""
        st.rerun()

st.divider()

if not st.session_state.euai_done and not use_case_text.strip():
    st.info("Start by loading the sample text or pasting an AI use case to evaluate.")

if st.session_state.euai_done:
    last_text = st.session_state.euai_last_text
    findings = st.session_state.euai_last_findings
    report_text = st.session_state.euai_last_report
    present, partial, missing, score = compute_score(findings)

    st.success("Readiness review complete.")
    st.info("This output is generated by a limited deterministic checklist engine. It does not determine legal compliance. Human review is required.")
    st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no legal determination or definitive compliance classification.")

    st.write(f"**Readiness summary:** Present: {present} | Partial: {partial} | Missing: {missing} | Score: {score:.1f}/{len(findings)}")

    st.download_button(
        label="Download text report",
        data=report_text,
        file_name="eu_ai_act_readiness_report.txt",
        mime="text/plain"
    )

    transparency_pdf = build_transparency_report_pdf(last_text, findings)

    st.download_button(
        label="Download Transparency & Oversight Report (PDF)",
        data=transparency_pdf,
        file_name="eu_ai_act_readiness_transparency_report.pdf",
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
                    st.session_state.euai_ai_summary = generate_ai_summary(last_text, findings)
                    st.rerun()
                except Exception as e:
                    st.warning(f"AI summary is temporarily unavailable. Deterministic review remains available. Details: {e}")
        else:
            st.caption("AI summary is available for this input under current public-demo limits.")

        if st.session_state.euai_ai_summary:
            st.info(st.session_state.euai_ai_summary)
    else:
        st.warning(ai_message)

    with st.expander("Preview pasted use-case text"):
        st.write(last_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
st.markdown("[Having issues? drop us an email](mailto:hello@lippershey.co)")
