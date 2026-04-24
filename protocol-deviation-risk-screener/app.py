import re
import streamlit as st

SAMPLE_TEXT = """Protocol deviation risk review input

Study title:
Nonclinical in vivo toxicology assessment of VX-247

Study objective:
To evaluate repeat-dose tolerability and liver safety findings over 28 days.

Design summary:
Animals are assigned to vehicle control, low dose, and high dose groups.
An interim necropsy may be performed if clinically indicated.
Study procedures should be conducted according to site standard practice where feasible.

Endpoints:
Primary endpoint: liver histopathology findings at day 28.
Secondary endpoints: body weight, clinical observations, serum chemistry.

Operational notes:
Blood sampling should occur at baseline and at selected follow-up time points.
Protocol deviations are documented locally.
GLP archiving language is not included in this draft excerpt.
"""

RISK_RULES = [
    {
        "title": "Control-arm language detected",
        "patterns": [r"\bvehicle control\b", r"\bcontrol\b", r"\bcontrol groups?\b"],
        "risk_level": "Info",
        "type": "Control-arm structure",
        "why": "The text includes control-arm language. This is useful context for screening protocol design completeness.",
    },
    {
        "title": "Potential endpoint/objective mismatch signal",
        "patterns": [r"\bobjective\b", r"\bprimary endpoint\b", r"\bsecondary endpoints?\b"],
        "risk_level": "Medium",
        "type": "Objective-endpoint alignment",
        "why": "The text includes objectives and endpoints that may require review for clarity and alignment.",
    },
    {
        "title": "Potential operational ambiguity detected",
        "patterns": [r"\bwhere feasible\b", r"\bmay be performed\b", r"\bselected follow-up time points\b", r"\bshould occur\b"],
        "risk_level": "Medium",
        "type": "Operational ambiguity",
        "why": "The text includes potentially flexible or ambiguous operational wording that may increase deviation risk.",
    },
    {
        "title": "Deviation handling language detected",
        "patterns": [r"\bprotocol deviations?\b", r"\bdocumented locally\b"],
        "risk_level": "Info",
        "type": "Deviation handling",
        "why": "The text includes protocol-deviation handling language relevant for governance review.",
    },
    {
        "title": "Possible GLP/documentation gap signal",
        "patterns": [r"\bglp\b", r"\barchiving\b", r"\bnot included\b"],
        "risk_level": "Low",
        "type": "Documentation / GLP signal",
        "why": "The text includes language that may point to a documentation or GLP-completeness review need.",
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

def extract_study_title(text: str) -> str:
    m = re.search(r"Study title:\s*(.+)", text, flags=re.IGNORECASE)
    return m.group(1).strip() if m else "Not clearly stated"

def extract_objective(text: str) -> str:
    m = re.search(r"Study objective:\s*(.+)", text, flags=re.IGNORECASE)
    return m.group(1).strip() if m else "Not clearly stated"

def detect_protocol_deviation_risks(text: str):
    findings = []
    table_rows = []
    title = extract_study_title(text)
    objective = extract_objective(text)

    for rule in RISK_RULES:
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
                "risk_level": rule["risk_level"],
                "why_flagged": rule["why"],
                "matched_text": snippet,
                "rule_reference": "Protocol deviation-risk heuristic",
                "review_note": "Human review required.",
            })
            table_rows.append({
                "Study Title": title,
                "Risk Type": rule["type"],
                "Objective Context": objective,
                "Evidence": snippet,
                "Suggested Review Direction": "Check whether this wording could increase protocol deviation risk, reduce reproducibility, or weaken documentation clarity.",
            })

    return findings, table_rows

def build_report(text: str, findings: list[dict], table_rows: list[dict]) -> str:
    report = []
    report.append("PROTOCOL-DEVIATION-RISK-SCREENER REPORT")
    report.append("")
    report.append("This public demo uses a limited deterministic deviation-risk engine.")
    report.append("It does not determine formal GLP compliance, audit outcome, or final regulatory acceptability.")
    report.append("Human review is required.")
    report.append("No PDF or DOCX support is included in this public demo step.")
    report.append("")
    report.append("INPUT SUMMARY")
    report.append(f"Input length: {len(text)} characters")
    report.append(f"Risk rows detected: {len(table_rows)}")
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
        report.append("No protocol deviation-risk findings were triggered by the current v1 rule set.")
        report.append("")

    report.append("DEVIATION-RISK TABLE")
    if table_rows:
        for row in table_rows:
            report.append(
                f"- {row['Study Title']} | {row['Risk Type']} | {row['Objective Context']}"
            )
    else:
        report.append("- No deviation-risk rows available")
    report.append("")
    report.append("SCOPE LIMITS")
    report.append("- Text-only demo")
    report.append("- No PDF or DOCX support in this step")
    report.append("- No final GLP, audit, or regulatory determination")
    report.append("")
    return "\n".join(report)

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

st.set_page_config(page_title="Protocol-Deviation-Risk-Screener", layout="wide")

defaults = {
    "pdr_text": "",
    "pdr_done": False,
    "pdr_last_text": "",
    "pdr_last_findings": [],
    "pdr_last_table_rows": [],
    "pdr_last_report": "",
    "pdr_ai_summary": "",
    "pdr_quality_review_open": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("Protocol-Deviation-Risk-Screener")
st.caption("Screen protocol-style text for visible deviation-risk patterns, operational ambiguity, and documentation gaps.")

with st.expander("How this tool works", expanded=True):
    st.markdown("""
### Deterministic deviation-risk engine
This tool checks submitted protocol-style text against a limited set of v1 deviation-risk heuristics.
This deterministic layer is the **source of truth** for findings shown in the public demo.

### Claude-based AI summary
An optional Claude-based AI summary layer can later rewrite deterministic findings into a more readable reviewer note.
This AI layer is **assistive only**. It does not replace deterministic findings or human review.

### Public demo limits
- Paste plain text only
- Protocol / study-design / nonclinical text only
- Deterministic review up to 12,000 characters
- AI summary limited to smaller inputs and restricted public-demo usage
- No PDF or DOCX support in the public demo
- No confidential, patient, or business-sensitive data

[Having issues? drop us an email](mailto:hello@lippershey.co)
    """)

with st.expander("How to use", expanded=False):
    st.markdown("""
1. Paste protocol or study-design text
2. Click **Run deviation risk screen**
3. Review deterministic findings
4. Review the deviation-risk table
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

top_col1, top_col2, top_col3 = st.columns([1, 1, 3])

with top_col1:
    if st.button("Load sample text"):
        st.session_state.pdr_text = SAMPLE_TEXT
        st.session_state.pdr_done = False
        st.session_state.pdr_ai_summary = ""
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.pdr_text = ""
        st.session_state.pdr_done = False
        st.session_state.pdr_last_text = ""
        st.session_state.pdr_last_findings = []
        st.session_state.pdr_last_table_rows = []
        st.session_state.pdr_last_report = ""
        st.session_state.pdr_ai_summary = ""
        st.session_state.pdr_quality_review_open = False
        st.rerun()

with top_col3:
    st.caption("Use the sample protocol text for a quick demo, or reset the form.")

text = st.text_area(
    "Protocol / study-design text",
    height=320,
    placeholder="Paste protocol or study-design text here...",
    key="pdr_text"
)
st.caption(f"Characters: {len(text)}/12000")

if st.button("Run deviation risk screen"):
    if not text.strip():
        st.warning("Please paste protocol text before running the deviation risk screen.")
    elif len(text) > 12000:
        st.error("Public demo limit reached: this text exceeds 12,000 characters. For larger reviews or supported workflows, contact us for pricing.")
        st.session_state.pdr_done = False
    else:
        findings, table_rows = detect_protocol_deviation_risks(text)
        report_text = build_report(text, findings, table_rows)
        st.session_state.pdr_last_text = text
        st.session_state.pdr_last_findings = findings
        st.session_state.pdr_last_table_rows = table_rows
        st.session_state.pdr_last_report = report_text
        st.session_state.pdr_done = True
        st.session_state.pdr_ai_summary = ""
        st.session_state.pdr_quality_review_open = False
        st.rerun()

st.divider()

if not st.session_state.pdr_done and not text.strip():
    st.info("Start by loading the sample text or pasting protocol text to evaluate.")

if st.session_state.pdr_done:
    last_text = st.session_state.pdr_last_text
    findings = st.session_state.pdr_last_findings
    table_rows = st.session_state.pdr_last_table_rows
    report_text = st.session_state.pdr_last_report

    st.success("Protocol deviation-risk review complete.")
    st.info("This output is generated by a limited deterministic deviation-risk engine. It does not determine formal GLP compliance, audit outcome, or final regulatory acceptability. Human review is required.")
    st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no final GLP, audit, or regulatory determination.")

    st.download_button(
        label="Download text report",
        data=report_text,
        file_name="protocol_deviation_risk_screener_report.txt",
        mime="text/plain"
    )

    st.subheader("Findings")
    if findings:
        for finding in findings:
            render_finding(finding)
            st.divider()
    else:
        st.info("No protocol deviation-risk findings were triggered by the current v1 rule set.")

    st.subheader("Deviation-risk table")
    if table_rows:
        st.dataframe(table_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No deviation-risk rows available from the current v1 rule set.")

    st.subheader("AI summary")
    st.caption("AI summary will be added in the next step.")

    st.divider()
    st.subheader("Result Quality Review")
    st.caption("Review how this result can be further analyzed in a private deployment, with deeper case-specific quality checks and internal QA support.")

    if st.button("Open Quality Review"):
        st.session_state.pdr_quality_review_open = True
        st.rerun()

    if st.session_state.get("pdr_quality_review_open"):
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

    with st.expander("Preview pasted protocol text"):
        st.write(last_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
st.markdown("[Having issues? drop us an email](mailto:hello@lippershey.co)")
