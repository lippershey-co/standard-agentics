import re
import streamlit as st

SAMPLE_TEXT = """Program: VX-247 Oncology Asset

Submission Package Summary:
Module 1 regional administrative documents are in preparation.
Module 2 overview package includes a draft quality overall summary and nonclinical overview.
Clinical overview is not yet finalized.

Module 3 CMC:
Drug substance description is available.
Drug product composition is described.
Specification tables are included.
Container closure details are still pending.
Stability summary includes accelerated data only.

Module 4 Nonclinical:
Repeat-dose toxicology studies are summarized.
Safety pharmacology section is partial.
Genotoxicity summary is included.

Module 5 Clinical:
Study synopsis for first-in-human study is available.
Investigator brochure is in draft.
Clinical protocol is under final review.

Regulatory Note:
Team is targeting submission readiness review in Q4.
"""

CTD_AREAS = [
    {
        "title": "Module 1 administrative documentation",
        "strong": ["module 1", "regional administrative documents"],
        "weak": ["administrative", "regional"],
    },
    {
        "title": "Module 2 summary documentation",
        "strong": ["module 2", "quality overall summary", "nonclinical overview", "clinical overview"],
        "weak": ["overview", "summary package"],
    },
    {
        "title": "Module 3 CMC content",
        "strong": ["module 3", "drug substance", "drug product composition", "specification tables"],
        "weak": ["cmc", "specification", "drug product"],
    },
    {
        "title": "Container closure documentation",
        "strong": ["container closure"],
        "weak": ["closure", "container"],
    },
    {
        "title": "Stability package",
        "strong": ["stability summary", "accelerated data", "long-term stability"],
        "weak": ["stability"],
    },
    {
        "title": "Module 4 nonclinical content",
        "strong": ["module 4", "repeat-dose toxicology", "safety pharmacology", "genotoxicity"],
        "weak": ["nonclinical", "toxicology", "genotoxicity"],
    },
    {
        "title": "Module 5 clinical content",
        "strong": ["module 5", "study synopsis", "investigator brochure", "clinical protocol"],
        "weak": ["clinical", "protocol", "brochure"],
    },
    {
        "title": "Submission timing / readiness statement",
        "strong": ["submission readiness", "targeting submission", "readiness review in q"],
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

def classify_ctd_area(text: str, area: dict) -> dict:
    lower_text = text.lower()

    for keyword in area["strong"]:
        if keyword in lower_text:
            return {
                "status": "Present",
                "why_flagged": f'Evidence of this CTD area was detected via strong keyword match: "{keyword}".',
                "matched_text": find_snippet(text, keyword),
            }

    for keyword in area["weak"]:
        if keyword in lower_text:
            return {
                "status": "Partial",
                "why_flagged": f'Possible evidence of this CTD area was detected via weaker keyword match: "{keyword}".',
                "matched_text": find_snippet(text, keyword),
            }

    return {
        "status": "Missing",
        "why_flagged": "No clear evidence of this CTD area was detected in the submitted text.",
        "matched_text": "None detected",
    }

def detect_ctd_gaps(text: str) -> list[dict]:
    findings = []

    for area in CTD_AREAS:
        result = classify_ctd_area(text, area)
        recommended_action = {
            "Present": "Documented evidence appears present. Confirm the section is complete and retained in formal submission records.",
            "Partial": "Add more explicit section detail or completion evidence before relying on this CTD area as submission-ready.",
            "Missing": "Add a formal section, summary, or retained evidence for this CTD area.",
        }[result["status"]]

        findings.append({
            "title": area["title"],
            "status": result["status"],
            "why_flagged": result["why_flagged"],
            "matched_text": result["matched_text"],
            "reference_area": "CTD completeness heuristic",
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
    report.append("CTD-GAP-FINDER REPORT")
    report.append("")
    report.append("This public demo uses a limited deterministic completeness engine.")
    report.append("It does not determine submission adequacy or regulatory acceptability.")
    report.append("Human review is required.")
    report.append("No PDF or DOCX support is included in this public demo step.")
    report.append("")
    report.append("INPUT SUMMARY")
    report.append(f"Package summary length: {len(text)} characters")
    report.append("")
    report.append("READINESS SUMMARY")
    report.append(f"CTD areas checked: {len(findings)}")
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

st.set_page_config(page_title="CTD-Gap-Finder", layout="wide")

defaults = {
    "ctd_text": "",
    "ctd_done": False,
    "ctd_last_text": "",
    "ctd_last_findings": [],
    "ctd_last_report": "",
    "ctd_ai_summary": "",
    "ctd_quality_review_open": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("CTD-Gap-Finder")
st.caption("Audit a CTD package summary for possible missing or incomplete section coverage before formal submission review.")

with st.expander("How this tool works", expanded=True):
    st.markdown("""
### Deterministic completeness engine
This tool checks submitted package text against a limited set of v1 CTD completeness areas.
This deterministic layer is the **source of truth** for findings shown in the public demo.

### Claude-based AI summary
An optional Claude-based AI summary layer can later rewrite deterministic findings into a more readable reviewer note.
This AI layer is **assistive only**. It does not replace deterministic findings or human review.

### Public demo limits
- Paste plain text only
- CTD / submission-readiness text only
- Deterministic review up to 12,000 characters
- AI summary limited to smaller inputs and restricted public-demo usage
- No PDF or DOCX support in the public demo
- No confidential, patient, or business-sensitive data

[Having issues? drop us an email](mailto:hello@lippershey.co)
    """)

with st.expander("How to use", expanded=False):
    st.markdown("""
1. Paste a CTD or submission package summary
2. Click **Run gap check**
3. Review deterministic completeness findings
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
        st.session_state.ctd_text = SAMPLE_TEXT
        st.session_state.ctd_done = False
        st.session_state.ctd_ai_summary = ""
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.ctd_text = ""
        st.session_state.ctd_done = False
        st.session_state.ctd_last_text = ""
        st.session_state.ctd_last_findings = []
        st.session_state.ctd_last_report = ""
        st.session_state.ctd_ai_summary = ""
        st.session_state.ctd_quality_review_open = False
        st.rerun()

with top_col3:
    st.caption("Use the sample CTD summary for a quick demo, or reset the form.")

text = st.text_area(
    "CTD / submission package summary",
    height=320,
    placeholder="Paste CTD or submission-readiness text here...",
    key="ctd_text"
)
st.caption(f"Characters: {len(text)}/12000")

if st.button("Run gap check"):
    if not text.strip():
        st.warning("Please paste package summary text before running the gap check.")
    elif len(text) > 12000:
        st.error("Public demo limit reached: this text exceeds 12,000 characters. For larger package reviews or supported workflows, contact us for pricing.")
        st.session_state.ctd_done = False
    else:
        findings = detect_ctd_gaps(text)
        report_text = build_report(text, findings)
        st.session_state.ctd_last_text = text
        st.session_state.ctd_last_findings = findings
        st.session_state.ctd_last_report = report_text
        st.session_state.ctd_done = True
        st.session_state.ctd_ai_summary = ""
        st.session_state.ctd_quality_review_open = False
        st.rerun()

st.divider()

if not st.session_state.ctd_done and not text.strip():
    st.info("Start by loading the sample text or pasting a package summary to evaluate.")

if st.session_state.ctd_done:
    last_text = st.session_state.ctd_last_text
    findings = st.session_state.ctd_last_findings
    report_text = st.session_state.ctd_last_report
    present, partial, missing, score = compute_score(findings)

    st.success("Gap review complete.")
    st.info("This output is generated by a limited deterministic completeness engine. It does not determine submission adequacy or regulatory acceptability. Human review is required.")
    st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no final submission adequacy determination.")

    st.write(f"**Readiness summary:** Present: {present} | Partial: {partial} | Missing: {missing} | Score: {score:.1f}/{len(findings)}")

    st.download_button(
        label="Download text report",
        data=report_text,
        file_name="ctd_gap_finder_report.txt",
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
    st.caption("AI summary will be added in the next step.")

    st.divider()
    st.subheader("Result Quality Review")
    st.caption("Review how this result can be further analyzed in a private deployment, with deeper case-specific quality checks and internal QA support.")

    if st.button("Open Quality Review"):
        st.session_state.ctd_quality_review_open = True
        st.rerun()

    if st.session_state.get("ctd_quality_review_open"):
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
