import re
import streamlit as st

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
        st.caption("AI summary is available for this input under current public-demo limits.")
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
