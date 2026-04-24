import re
import streamlit as st

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
    "pai_old_text": SAMPLE_OLD_TEXT,
    "pai_new_text": SAMPLE_NEW_TEXT,
    "pai_done": False,
    "pai_last_old_text": "",
    "pai_last_new_text": "",
    "pai_last_findings": [],
    "pai_last_table_rows": [],
    "pai_last_report": "",
    "pai_ai_summary": "",
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
    st.caption("AI summary will be added in the next step.")

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
