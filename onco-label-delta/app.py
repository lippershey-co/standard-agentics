import os
import re
import html
import streamlit as st
import anthropic

SAMPLE_OLD_LABEL = """INDICATIONS AND USAGE
VANGARD-X is indicated for the treatment of adult patients with metastatic NSCLC whose tumors express ALK rearrangements.

DOSAGE AND ADMINISTRATION
The recommended dose is 600 mg orally twice daily.

WARNINGS AND PRECAUTIONS
Monitor liver function tests before treatment initiation and monthly thereafter.
"""

SAMPLE_NEW_LABEL = """INDICATIONS AND USAGE
VANGARD-X is indicated for the treatment of adult patients with metastatic or locally advanced NSCLC whose tumors express ALK rearrangements.

DOSAGE AND ADMINISTRATION
The recommended dose is 450 mg orally twice daily.

WARNINGS AND PRECAUTIONS
Monitor liver function tests before treatment initiation, every 2 weeks for the first 2 months, and monthly thereafter.

ADVERSE REACTIONS
The most common adverse reactions were diarrhea, edema, and fatigue.
"""

CHANGE_PATTERNS = [
    ("Indication / population language change", r"(indicated for|patients with|metastatic|locally advanced|adult patients)"),
    ("Dose or schedule change", r"(\bmg\b|twice daily|once daily|recommended dose)"),
    ("Monitoring / precaution change", r"(monitor|warnings and precautions|liver function|monthly|weeks)"),
    ("Adverse reaction / safety section change", r"(adverse reactions|safety|fatigue|edema|diarrhea)"),
]

def normalize_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]

def looks_like_onco_label_scope(old_text: str, new_text: str) -> bool:
    combined = (old_text + "\n" + new_text).lower()
    scope_terms = [
        "indications and usage",
        "dosage and administration",
        "warnings and precautions",
        "adverse reactions",
        "recommended dose",
        "prescribing information",
        "smpc",
        "label",
        "monitor",
        "patients with",
    ]
    return any(term in combined for term in scope_terms)


def ai_summary_allowed(old_text: str, new_text: str):
    if len(old_text) > 3500 or len(new_text) > 3500:
        return False, "Deterministic review completed. AI summary is limited to 3,500 characters per text block in the public demo. For larger inputs and extended review support, contact us for pricing."
    if not looks_like_onco_label_scope(old_text, new_text):
        return False, "This public demo AI summary is limited to oncology label, SmPC, or prescribing-information text. For broader document review or custom workflows, contact us for pricing."
    return True, ""


def build_line_delta(old_text: str, new_text: str) -> list[dict]:
    old_lines = normalize_lines(old_text)
    new_lines = normalize_lines(new_text)

    findings = []

    old_set = set(old_lines)
    new_set = set(new_lines)

    removed = [line for line in old_lines if line not in new_set]
    added = [line for line in new_lines if line not in old_set]

    for title, pattern in CHANGE_PATTERNS:
        related_removed = [line for line in removed if re.search(pattern, line, flags=re.IGNORECASE)]
        related_added = [line for line in added if re.search(pattern, line, flags=re.IGNORECASE)]

        if related_removed or related_added:
            findings.append({
                "title": title,
                "risk_level": "Medium",
                "why_flagged": "Potential meaningful label change detected in this section or concept area.",
                "old_text": related_removed[:2],
                "new_text": related_added[:2],
                "rule_reference": "Onco Label Delta heuristic",
                "review_note": "Human review required."
            })

    if not findings and (removed or added):
        findings.append({
            "title": "General label text change detected",
            "risk_level": "Low",
            "why_flagged": "Text differences were detected between the two label versions, but no current v1 rule family matched strongly.",
            "old_text": removed[:3],
            "new_text": added[:3],
            "rule_reference": "Generic label delta heuristic",
            "review_note": "Human review required."
        })

    return findings

def build_report(old_text: str, new_text: str, findings: list[dict]) -> str:
    report = []
    report.append("ONCO-LABEL-DELTA REPORT")
    report.append("")
    report.append("This public demo uses a limited deterministic comparison engine.")
    report.append("It does not determine regulatory significance.")
    report.append("Human review is required.")
    report.append("No PDF or DOCX support is included in this public demo step.")
    report.append("")
    report.append("INPUT SUMMARY")
    report.append(f"Old label length: {len(old_text)} characters")
    report.append(f"New label length: {len(new_text)} characters")
    report.append("")
    report.append("FINDINGS")

    if findings:
        for i, finding in enumerate(findings, start=1):
            report.append(f"{i}. {finding['title']}")
            report.append(f"   Risk level: {finding['risk_level']}")
            report.append(f"   Why flagged: {finding['why_flagged']}")
            report.append(f"   Old text: {' | '.join(finding['old_text']) if finding['old_text'] else 'None'}")
            report.append(f"   New text: {' | '.join(finding['new_text']) if finding['new_text'] else 'None'}")
            report.append(f"   Rule reference: {finding['rule_reference']}")
            report.append(f"   Review note: {finding['review_note']}")
            report.append("")
    else:
        report.append("No changes were detected by the current v1 rule set.")
        report.append("")

    report.append("SCOPE LIMITS")
    report.append("- Text-only demo")
    report.append("- No PDF or DOCX support in this step")
    report.append("- No final regulatory significance determination")
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
    lines.append(f"Findings detected: {len(findings)}")
    lines.append("Top flagged change areas:")
    for finding in findings[:3]:
        lines.append(f"- {finding['title']} ({finding['risk_level']})")
    lines.append("")
    lines.append("Human review is still required.")
    return "\n".join(lines)


def generate_ai_summary(old_text: str, new_text: str, findings: list[dict]) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "AI summary is not available because ANTHROPIC_API_KEY is not set on this runtime."

    findings_text = "\n".join(
        [
            f"- {f['title']} | Risk: {f['risk_level']} | Why: {f['why_flagged']} | Old: {' | '.join(f['old_text']) if f['old_text'] else 'None'} | New: {' | '.join(f['new_text']) if f['new_text'] else 'None'} | Reference: {f['rule_reference']}"
            for f in findings
        ]
    ) or "- No deterministic findings triggered."

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = (
        "You are an assistive oncology label-comparison summarizer. "
        "You must summarize only the deterministic findings provided to you, plus limited clearly grounded interpretation that directly follows from those findings. "
        "Do not invent new findings. "
        "Do not state PASS or FAIL. "
        "Do not state the changes are clinically significant, regulatorily significant, approved, or final unless that was already explicitly established in the deterministic findings. "
        "Do not make definitive legal, medical, or regulatory judgments. "
        "Be concise, practical, and plain-English. "
        "Your output must use exactly these section headings in this exact order: "
        "'Main review concerns', 'Likely reviewer focus', 'Suggested next step'. "
        "End with the exact sentence: 'Human review is required.'"
    )

    user_prompt = f"""
Earlier label text:
{old_text}

Newer label text:
{new_text}

Deterministic findings:
{findings_text}

Write the response in this exact structure:

Main review concerns
<1 short paragraph summarizing the most important deterministic findings and any limited directly grounded interpretation.>

Likely reviewer focus
<1 short paragraph describing what a reviewer would most likely examine next, based only on the deterministic findings and clearly grounded interpretation.>

Suggested next step
<1 short paragraph with the most practical next action, based only on the deterministic findings.>

Human review is required.

Rules:
- Do not add new findings not supported by the deterministic findings.
- Do not use bullet points.
- Do not output PASS or FAIL.
- Do not say the changes are clinically significant, regulatorily significant, approved, or final.
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


def render_risk_badge(risk_level: str):
    if risk_level == "High":
        st.error(f"Risk level: {risk_level}")
    elif risk_level == "Medium":
        st.warning(f"Risk level: {risk_level}")
    elif risk_level == "Low":
        st.info(f"Risk level: {risk_level}")
    else:
        st.write(f"Risk level: {risk_level}")

def render_finding(finding: dict):
    st.markdown(f"### {finding['title']}")
    render_risk_badge(finding["risk_level"])
    st.write(f"**Why it was flagged:** {finding['why_flagged']}")
    st.write(f"**Old text:** {' | '.join(finding['old_text']) if finding['old_text'] else 'None'}")
    st.write(f"**New text:** {' | '.join(finding['new_text']) if finding['new_text'] else 'None'}")
    st.write(f"**Rule reference:** {finding['rule_reference']}")
    st.write(f"**Review note:** {finding['review_note']}")

st.set_page_config(page_title="Onco-Label-Delta", layout="wide")

defaults = {
    "old_label_text": "",
    "new_label_text": "",
    "old_done": False,
    "old_last_old_text": "",
    "old_last_new_text": "",
    "old_last_findings": [],
    "old_last_report": "",
    "old_ai_summary": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("Onco-Label-Delta")
st.caption("Compare two oncology label versions for possible meaningful section-level changes.")

with st.expander("How this tool works", expanded=True):
    st.markdown("""
### Deterministic comparison engine
This tool compares two pasted label versions and checks for a limited set of v1 change families.
This deterministic layer is the **source of truth** for findings shown in the public demo.

### Claude-based AI summary
An optional Claude-based AI summary layer can later rewrite deterministic findings into a more readable reviewer note.
This AI layer is **assistive only**. It does not replace deterministic findings or human review.

### Public demo limits
- Paste plain text only
- Oncology label / SmPC / prescribing text only
- Deterministic comparison: up to 12,000 characters per text block
- AI summary: limited to smaller inputs and restricted public-demo usage
- No PDF or DOCX support in the public demo
- No confidential, patient, or business-sensitive data

[Having issues? drop us an email](mailto:hello@lippershey.co)
    """)

with st.expander("How to use", expanded=False):
    st.markdown("""
1. Paste the earlier label version
2. Paste the newer label version
3. Click **Run delta check**
4. Review deterministic findings
5. Optionally generate an AI summary in a later step
    """)

with st.expander("Public demo policy", expanded=False):
    st.markdown("""
- Testing only
- English only
- Paste text only in v1
- No PDF or DOCX support in this demo step
- Maximum 12,000 characters per text block
- No confidential, patient, or business-sensitive data
- Human review required
    """)

top_col1, top_col2, top_col3 = st.columns([1, 1, 3])

with top_col1:
    if st.button("Load sample text"):
        st.session_state.old_label_text = SAMPLE_OLD_LABEL
        st.session_state.new_label_text = SAMPLE_NEW_LABEL
        st.session_state.old_done = False
        st.session_state.old_ai_summary = ""
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.old_label_text = ""
        st.session_state.new_label_text = ""
        st.session_state.old_done = False
        st.session_state.old_last_old_text = ""
        st.session_state.old_last_new_text = ""
        st.session_state.old_last_findings = []
        st.session_state.old_last_report = ""
        st.session_state.old_ai_summary = ""
        st.rerun()

with top_col3:
    st.caption("Use the sample label texts for a quick demo, or reset the form.")

old_text = st.text_area(
    "Earlier label version",
    height=240,
    placeholder="Paste earlier label text here...",
    key="old_label_text"
)

new_text = st.text_area(
    "Newer label version",
    height=240,
    placeholder="Paste newer label text here...",
    key="new_label_text"
)

st.caption(f"Old label characters: {len(old_text)}/12000 | New label characters: {len(new_text)}/12000")

if st.button("Run delta check"):
    if not old_text.strip() or not new_text.strip():
        st.warning("Please paste both label versions before running the delta check.")
    elif len(old_text) > 12000 or len(new_text) > 12000:
        st.error("Public demo limit reached: one or both text blocks exceed 12,000 characters. For larger documents or supported workflows, contact us for pricing.")
        st.session_state.old_done = False
    else:
        findings = build_line_delta(old_text, new_text)
        report_text = build_report(old_text, new_text, findings)
        st.session_state.old_last_old_text = old_text
        st.session_state.old_last_new_text = new_text
        st.session_state.old_last_findings = findings
        st.session_state.old_last_report = report_text
        st.session_state.old_done = True
        st.session_state.old_ai_summary = ""
        st.rerun()

st.divider()

if not st.session_state.old_done and not old_text.strip() and not new_text.strip():
    st.info("Start by loading the sample text or pasting two label versions to compare.")

if st.session_state.old_done:
    last_old_text = st.session_state.old_last_old_text
    last_new_text = st.session_state.old_last_new_text
    findings = st.session_state.old_last_findings
    report_text = st.session_state.old_last_report

    st.success("Delta review complete.")
    st.info("This output is generated by a limited deterministic comparison engine. It does not determine regulatory significance. Human review is required.")
    st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no final regulatory significance determination.")

    st.download_button(
        label="Download text report",
        data=report_text,
        file_name="onco_label_delta_report.txt",
        mime="text/plain"
    )

    st.subheader("Findings")
    if findings:
        for finding in findings:
            render_finding(finding)
            st.divider()
    else:
        st.success("No changes were detected by the current v1 rule set.")

    st.subheader("AI summary")
    allowed, ai_message = ai_summary_allowed(last_old_text, last_new_text)
    if allowed:
        if st.button("Generate AI summary"):
            with st.spinner("Generating AI summary..."):
                try:
                    st.session_state.old_ai_summary = generate_ai_summary(last_old_text, last_new_text, findings)
                    st.rerun()
                except Exception as e:
                    st.warning(f"AI summary is temporarily unavailable. Deterministic review remains available. Details: {e}")
        else:
            st.caption("AI summary is available for this input under current public-demo limits.")

        if st.session_state.old_ai_summary:
            render_structured_ai_summary(st.session_state.old_ai_summary)
    else:
        st.warning(ai_message)

    st.divider()
    st.subheader("Result Quality Review")
    st.caption("Review how this result can be further analyzed in a private deployment, with deeper case-specific quality checks and internal QA support.")

    if st.button("Open Quality Review"):
        st.session_state.old_quality_review_open = True
        st.rerun()

    if st.session_state.get("old_quality_review_open"):
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

    with st.expander("Preview earlier label text"):
        st.write(last_old_text[:1200])

    with st.expander("Preview newer label text"):
        st.write(last_new_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
st.markdown("[Having issues? drop us an email](mailto:hello@lippershey.co)")
