import os
import re
import html
import streamlit as st
import anthropic

SAMPLE_TEXT = """Program: VX-247 Oncology Asset

Nonclinical Summary:
Repeat-dose tox studies have been completed in rat and dog.
Safety pharmacology has been partially completed.
Genotoxicity package includes Ames test; in vivo follow-up study is still pending.
PK summary is available from rodent studies only.
Bioanalytical method validation is in progress.
CMC:
Drug substance process description is available.
Drug product specification draft exists, but stability data are limited to 1 month accelerated only.

Regulatory Note:
The team intends to target an IND submission in Q3.
"""

READINESS_AREAS = [
    {
        "title": "Toxicology package",
        "strong": ["repeat-dose tox", "repeat dose tox", "toxicology completed", "tox studies have been completed"],
        "weak": ["tox", "toxicology"],
    },
    {
        "title": "Safety pharmacology",
        "strong": ["safety pharmacology completed", "safety pharmacology has been completed"],
        "weak": ["safety pharmacology", "partially completed"],
    },
    {
        "title": "Genotoxicity",
        "strong": ["genotoxicity package", "ames test", "in vivo follow-up study"],
        "weak": ["genotoxicity", "ames"],
    },
    {
        "title": "PK / ADME support",
        "strong": ["pk summary", "adme", "rodent studies", "non-rodent studies"],
        "weak": ["pk", "pharmacokinetic"],
    },
    {
        "title": "Bioanalytical readiness",
        "strong": ["bioanalytical method validation", "validated bioanalytical method"],
        "weak": ["bioanalytical", "validation is in progress"],
    },
    {
        "title": "CMC process description",
        "strong": ["drug substance process description", "manufacturing process description"],
        "weak": ["process description", "drug substance"],
    },
    {
        "title": "Specification package",
        "strong": ["drug product specification", "release specification", "specification draft"],
        "weak": ["specification"],
    },
    {
        "title": "Stability data",
        "strong": ["stability data", "long-term stability", "accelerated stability"],
        "weak": ["stability", "1 month accelerated"],
    },
    {
        "title": "Submission timing / readiness statement",
        "strong": ["ind submission", "target an ind submission", "submission in q"],
        "weak": ["submission", "regulatory note"],
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

def classify_readiness_area(text: str, area: dict) -> dict:
    lower_text = text.lower()

    for keyword in area["strong"]:
        if keyword in lower_text:
            return {
                "status": "Present",
                "why_flagged": f'Evidence of this readiness area was detected via strong keyword match: "{keyword}".',
                "matched_text": find_snippet(text, keyword),
            }

    for keyword in area["weak"]:
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

def looks_like_ind_scope(text: str) -> bool:
    lower_text = text.lower()
    scope_terms = [
        "ind submission",
        "nonclinical",
        "toxicology",
        "repeat-dose tox",
        "safety pharmacology",
        "genotoxicity",
        "pk summary",
        "bioanalytical",
        "drug substance",
        "drug product",
        "stability data",
        "cmc",
    ]
    return any(term in lower_text for term in scope_terms)


def ai_summary_allowed(text: str):
    if len(text) > 3500:
        return False, "Deterministic review completed. AI summary is limited to 3,500 characters in the public demo. For larger inputs and extended review support, contact us for pricing."
    if not looks_like_ind_scope(text):
        return False, "This public demo AI summary is limited to preclinical, CMC, or IND-readiness text. For broader document review or custom workflows, contact us for pricing."
    return True, ""


def detect_ind_readiness(text: str) -> list[dict]:
    findings = []

    for area in READINESS_AREAS:
        result = classify_readiness_area(text, area)
        recommended_action = {
            "Present": "Documented evidence appears present. Confirm the package is complete and retained in formal submission records.",
            "Partial": "Add more explicit evidence or completion detail for this area before relying on the package as submission-ready.",
            "Missing": "Add a formal plan, evidence, or completed package component for this readiness area.",
        }[result["status"]]

        findings.append({
            "title": area["title"],
            "status": result["status"],
            "why_flagged": result["why_flagged"],
            "matched_text": result["matched_text"],
            "reference_area": "IND readiness heuristic",
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

def build_report(text: str, findings: list[dict]) -> str:
    present, partial, missing, score = compute_score(findings)

    report = []
    report.append("IND-READINESS-CHECKER REPORT")
    report.append("")
    report.append("This public demo uses a limited deterministic readiness engine.")
    report.append("It does not determine submission adequacy or regulatory acceptability.")
    report.append("Human review is required.")
    report.append("No PDF or DOCX support is included in this public demo step.")
    report.append("")
    report.append("INPUT SUMMARY")
    report.append(f"Package summary length: {len(text)} characters")
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
    report.append("- No final submission adequacy determination")
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
    lines.append("Top flagged readiness areas:")
    for finding in findings[:3]:
        lines.append(f"- {finding['title']} ({finding['status']})")
    lines.append("")
    lines.append("Human review is still required.")
    return "\n".join(lines)


def generate_ai_summary(text: str, findings: list[dict]) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "AI summary is not available because ANTHROPIC_API_KEY is not set on this runtime."

    findings_text = "\n".join(
        [
            f"- {f['title']} | Status: {f['status']} | Why: {f['why_flagged']} | Matched: {f['matched_text']} | Reference: {f['reference_area']}"
            for f in findings
        ]
    ) or "- No deterministic findings triggered."

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = (
        "You are an assistive IND-readiness summarizer. "
        "You must summarize only the deterministic findings provided to you, plus limited clearly grounded interpretation that directly follows from those findings. "
        "Do not invent new findings. "
        "Do not state PASS or FAIL. "
        "Do not state the package is submission-ready, adequate, approved, or final unless that was already explicitly established in the deterministic findings. "
        "Do not make definitive legal, medical, or regulatory judgments. "
        "Be concise, practical, and plain-English. "
        "Your output must use exactly these section headings in this exact order: "
        "'Main review concerns', 'Likely reviewer focus', 'Suggested next step'. "
        "End with the exact sentence: 'Human review is required.'"
    )

    user_prompt = f"""
Preclinical / IND-readiness text:
{text}

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
- Do not say the package is submission-ready, adequate, approved, or final.
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

st.set_page_config(page_title="IND-Readiness-Checker", layout="wide")

defaults = {
    "ind_text": "",
    "ind_done": False,
    "ind_last_text": "",
    "ind_last_findings": [],
    "ind_last_report": "",
    "ind_ai_summary": "",
    "ind_quality_review_open": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("IND-Readiness-Checker")
st.caption("Audit a preclinical / IND package summary for possible readiness gaps before formal submission review.")

with st.expander("How this tool works", expanded=True):
    st.markdown("""
### Deterministic readiness engine
This tool checks submitted package text against a limited set of v1 IND-readiness areas.
This deterministic layer is the **source of truth** for findings shown in the public demo.

### Claude-based AI summary
An optional Claude-based AI summary layer can later rewrite deterministic findings into a more readable reviewer note.
This AI layer is **assistive only**. It does not replace deterministic findings or human review.

### Public demo limits
- Paste plain text only
- Preclinical / IND-readiness text only
- Deterministic review up to 12,000 characters
- AI summary limited to smaller inputs and restricted public-demo usage
- No PDF or DOCX support in the public demo
- No confidential, patient, or business-sensitive data

[Having issues? drop us an email](mailto:hello@lippershey.co)
    """)

with st.expander("How to use", expanded=False):
    st.markdown("""
1. Paste a preclinical or IND package summary
2. Click **Run readiness check**
3. Review deterministic readiness findings
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

top_col1, top_col2, top_col3 = st.columns([1, 1, 3])

with top_col1:
    if st.button("Load sample text"):
        st.session_state.ind_text = SAMPLE_TEXT
        st.session_state.ind_done = False
        st.session_state.ind_ai_summary = ""
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.ind_text = ""
        st.session_state.ind_done = False
        st.session_state.ind_last_text = ""
        st.session_state.ind_last_findings = []
        st.session_state.ind_last_report = ""
        st.session_state.ind_ai_summary = ""
        st.session_state.ind_quality_review_open = False
        st.rerun()

with top_col3:
    st.caption("Use the sample package summary for a quick demo, or reset the form.")

text = st.text_area(
    "Preclinical / IND package summary",
    height=320,
    placeholder="Paste preclinical or IND-readiness text here...",
    key="ind_text"
)
st.caption(f"Characters: {len(text)}/12000")

if st.button("Run readiness check"):
    if not text.strip():
        st.warning("Please paste package summary text before running the readiness check.")
    elif len(text) > 12000:
        st.error("Public demo limit reached: this text exceeds 12,000 characters. For larger package reviews or supported workflows, contact us for pricing.")
        st.session_state.ind_done = False
    else:
        findings = detect_ind_readiness(text)
        report_text = build_report(text, findings)
        st.session_state.ind_last_text = text
        st.session_state.ind_last_findings = findings
        st.session_state.ind_last_report = report_text
        st.session_state.ind_done = True
        st.session_state.ind_ai_summary = ""
        st.session_state.ind_quality_review_open = False
        st.rerun()

st.divider()

if not st.session_state.ind_done and not text.strip():
    st.info("Start by loading the sample text or pasting a package summary to evaluate.")

if st.session_state.ind_done:
    last_text = st.session_state.ind_last_text
    findings = st.session_state.ind_last_findings
    report_text = st.session_state.ind_last_report
    present, partial, missing, score = compute_score(findings)

    st.success("Readiness review complete.")
    st.info("This output is generated by a limited deterministic readiness engine. It does not determine submission adequacy or regulatory acceptability. Human review is required.")
    st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no final submission adequacy determination.")

    st.write(f"**Readiness summary:** Present: {present} | Partial: {partial} | Missing: {missing} | Score: {score:.1f}/{len(findings)}")

    st.download_button(
        label="Download text report",
        data=report_text,
        file_name="ind_readiness_checker_report.txt",
        mime="text/plain"
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
                    st.session_state.ind_ai_summary = generate_ai_summary(last_text, findings)
                    st.rerun()
                except Exception as e:
                    st.warning(f"AI summary is temporarily unavailable. Deterministic review remains available. Details: {e}")
        else:
            st.caption("AI summary is available for this input under current public-demo limits.")

        if st.session_state.ind_ai_summary:
            render_structured_ai_summary(st.session_state.ind_ai_summary)
    else:
        st.warning(ai_message)

    st.divider()
    st.subheader("Result Quality Review")
    st.caption("Review how this result can be further analyzed in a private deployment, with deeper case-specific quality checks and internal QA support.")

    if st.button("Open Quality Review"):
        st.session_state.ind_quality_review_open = True
        st.rerun()

    if st.session_state.get("ind_quality_review_open"):
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

    with st.expander("Preview pasted package summary"):
        st.write(last_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
st.markdown("[Having issues? drop us an email](mailto:hello@lippershey.co)")
