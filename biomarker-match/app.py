import re
import streamlit as st

SAMPLE_TEXT = """Biomarker review input

Tumor type: metastatic NSCLC

Molecular summary:
- Tumor positive for EGFR exon 19 deletion.
- No ALK rearrangement detected.
- RET fusion not detected.
- PD-L1 TPS 65%.
- Tissue quantity is limited for additional testing.

Clinical note:
Patient progressed after prior platinum chemotherapy.
Current goal is to identify actionable alterations and matched therapy or trial directions.
"""

BIOMARKER_RULES = [
    {
        "biomarker": "EGFR exon 19 deletion",
        "patterns": [r"egfr exon 19 deletion", r"exon 19 deletion"],
        "match_type": "Approved / guideline-linked target",
        "therapy_hint": "EGFR-directed therapy may be relevant depending on current line and prior treatment history.",
    },
    {
        "biomarker": "ALK rearrangement",
        "patterns": [r"alk rearrangement", r"alk fusion", r"alk-positive", r"alk positive"],
        "match_type": "Approved / guideline-linked target",
        "therapy_hint": "ALK-directed therapy may be relevant if the alteration is present and sequencing context supports use.",
    },
    {
        "biomarker": "RET fusion",
        "patterns": [r"ret fusion", r"ret-positive", r"ret positive"],
        "match_type": "Precision oncology target",
        "therapy_hint": "RET-directed options or relevant trials may be worth review if a RET alteration is confirmed.",
    },
    {
        "biomarker": "KRAS G12C",
        "patterns": [r"kras g12c"],
        "match_type": "Precision oncology target",
        "therapy_hint": "KRAS G12C-targeted options or matched trials may be relevant depending on tumor type and sequence.",
    },
    {
        "biomarker": "NTRK fusion",
        "patterns": [r"ntrk fusion", r"trk fusion"],
        "match_type": "Rare actionable target",
        "therapy_hint": "Tumor-agnostic or matched precision options may be relevant if an NTRK fusion is confirmed.",
    },
    {
        "biomarker": "HER2-low / HER2 alteration",
        "patterns": [r"her2 low", r"her2-low", r"her2 amplification", r"her2 mutation"],
        "match_type": "Targeted / evolving context",
        "therapy_hint": "HER2-directed options may require review against tumor type, assay context, and label/guideline positioning.",
    },
    {
        "biomarker": "PD-L1 high expression",
        "patterns": [r"pd-l1 tps", r"pd-l1", r"tps 50", r"tps 65", r"high pd-l1"],
        "match_type": "Immunotherapy-relevant marker",
        "therapy_hint": "PD-L1 expression may affect immunotherapy positioning depending on label, tumor type, and line of therapy.",
    },
]

NEGATIVE_TERMS = [
    "not detected",
    "negative",
    "no rearrangement",
    "no fusion",
    "wild type",
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

def snippet_is_negative(snippet: str) -> bool:
    lower = snippet.lower()
    return any(term in lower for term in NEGATIVE_TERMS)

def detect_tumor_type(text: str) -> str:
    lower = text.lower()
    mapping = [
        ("nsclc", "NSCLC"),
        ("small cell lung", "Small cell lung cancer"),
        ("crc", "CRC"),
        ("colorectal", "Colorectal cancer"),
        ("breast", "Breast cancer"),
        ("ovarian", "Ovarian cancer"),
        ("pancreatic", "Pancreatic cancer"),
        ("gastric", "Gastric cancer"),
    ]
    for pattern, label in mapping:
        if pattern in lower:
            return label
    return "Not clearly stated"

def detect_biomarker_matches(text: str):
    findings = []
    table_rows = []
    lower_text = text.lower()
    tumor_type = detect_tumor_type(text)

    for rule in BIOMARKER_RULES:
        for pat in rule["patterns"]:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                snippet = sentence_snippet(text, m.start())
                detected_state = "Detected"
                risk_level = "Info"
                why_text = f'The submitted text includes explicit reference to "{rule["biomarker"]}", suggesting a biomarker review opportunity.'
                therapy_hint = rule["therapy_hint"]

                if snippet_is_negative(snippet):
                    detected_state = "Mentioned as negative / not detected"
                    risk_level = "Low"
                    why_text = f'The submitted text references "{rule["biomarker"]}" in a negative or not-detected context, which may still matter for biomarker review but does not indicate a positive match.'
                    therapy_hint = "No positive match is evident from this snippet. Confirm whether additional testing, prior reports, or broader panel review are needed."

                findings.append({
                    "title": f'Biomarker signal detected: {rule["biomarker"]}',
                    "risk_level": risk_level,
                    "why_flagged": why_text,
                    "matched_text": snippet,
                    "rule_reference": "Biomarker match heuristic",
                    "review_note": "Human review required.",
                })

                table_rows.append({
                    "Biomarker": rule["biomarker"],
                    "Status": detected_state,
                    "Tumor Type": tumor_type,
                    "Match Type": rule["match_type"],
                    "Suggested Review Direction": therapy_hint,
                })
                break

    return findings, table_rows

def build_report(text: str, findings: list[dict], table_rows: list[dict]) -> str:
    report = []
    report.append("BIOMARKER-MATCH REPORT")
    report.append("")
    report.append("This public demo uses a limited deterministic biomarker-matching engine.")
    report.append("It does not determine medical eligibility, treatment selection, or final clinical action.")
    report.append("Human review is required.")
    report.append("No PDF or DOCX support is included in this public demo step.")
    report.append("")
    report.append("INPUT SUMMARY")
    report.append(f"Input length: {len(text)} characters")
    report.append(f"Biomarker rows detected: {len(table_rows)}")
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
        report.append("No biomarker findings were triggered by the current v1 rule set.")
        report.append("")

    report.append("BIOMARKER MATCH TABLE")
    if table_rows:
        for row in table_rows:
            report.append(
                f"- {row['Biomarker']} | {row['Status']} | {row['Tumor Type']} | {row['Match Type']}"
            )
    else:
        report.append("- No biomarker rows available")
    report.append("")
    report.append("SCOPE LIMITS")
    report.append("- Text-only demo")
    report.append("- No PDF or DOCX support in this step")
    report.append("- No final treatment, guideline, or trial-matching determination")
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

st.set_page_config(page_title="Biomarker-Match", layout="wide")

defaults = {
    "bm_text": "",
    "bm_done": False,
    "bm_last_text": "",
    "bm_last_findings": [],
    "bm_last_table_rows": [],
    "bm_last_report": "",
    "bm_ai_summary": "",
    "bm_quality_review_open": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("Biomarker-Match")
st.caption("Scan biomarker/pathology-style text for visible actionable markers and generate a simple match-review table.")

with st.expander("How this tool works", expanded=True):
    st.markdown("""
### Deterministic biomarker engine
This tool checks submitted biomarker or pathology-style text against a limited set of v1 actionable-marker heuristics.
This deterministic layer is the **source of truth** for findings shown in the public demo.

### Claude-based AI summary
An optional Claude-based AI summary layer can later rewrite deterministic findings into a more readable reviewer note.
This AI layer is **assistive only**. It does not replace deterministic findings or human review.

### Public demo limits
- Paste plain text only
- Biomarker / molecular summary text only
- Deterministic review up to 12,000 characters
- AI summary limited to smaller inputs and restricted public-demo usage
- No PDF or DOCX support in the public demo
- No confidential, patient, or business-sensitive data

[Having issues? drop us an email](mailto:hello@lippershey.co)
    """)

with st.expander("How to use", expanded=False):
    st.markdown("""
1. Paste biomarker, molecular, or pathology-style text
2. Click **Run biomarker match**
3. Review deterministic findings
4. Review the biomarker match table
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
        st.session_state.bm_text = SAMPLE_TEXT
        st.session_state.bm_done = False
        st.session_state.bm_ai_summary = ""
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.bm_text = ""
        st.session_state.bm_done = False
        st.session_state.bm_last_text = ""
        st.session_state.bm_last_findings = []
        st.session_state.bm_last_table_rows = []
        st.session_state.bm_last_report = ""
        st.session_state.bm_ai_summary = ""
        st.session_state.bm_quality_review_open = False
        st.rerun()

with top_col3:
    st.caption("Use the sample biomarker text for a quick demo, or reset the form.")

text = st.text_area(
    "Biomarker / molecular summary text",
    height=320,
    placeholder="Paste biomarker or molecular summary text here...",
    key="bm_text"
)
st.caption(f"Characters: {len(text)}/12000")

if st.button("Run biomarker match"):
    if not text.strip():
        st.warning("Please paste biomarker text before running the biomarker match.")
    elif len(text) > 12000:
        st.error("Public demo limit reached: this text exceeds 12,000 characters. For larger reviews or supported workflows, contact us for pricing.")
        st.session_state.bm_done = False
    else:
        findings, table_rows = detect_biomarker_matches(text)
        report_text = build_report(text, findings, table_rows)
        st.session_state.bm_last_text = text
        st.session_state.bm_last_findings = findings
        st.session_state.bm_last_table_rows = table_rows
        st.session_state.bm_last_report = report_text
        st.session_state.bm_done = True
        st.session_state.bm_ai_summary = ""
        st.session_state.bm_quality_review_open = False
        st.rerun()

st.divider()

if not st.session_state.bm_done and not text.strip():
    st.info("Start by loading the sample text or pasting biomarker text to evaluate.")

if st.session_state.bm_done:
    last_text = st.session_state.bm_last_text
    findings = st.session_state.bm_last_findings
    table_rows = st.session_state.bm_last_table_rows
    report_text = st.session_state.bm_last_report

    st.success("Biomarker review complete.")
    st.info("This output is generated by a limited deterministic biomarker engine. It does not determine medical eligibility, treatment selection, or final clinical action. Human review is required.")
    st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no final treatment, guideline, or trial-matching determination.")

    st.download_button(
        label="Download text report",
        data=report_text,
        file_name="biomarker_match_report.txt",
        mime="text/plain"
    )

    st.subheader("Findings")
    if findings:
        for finding in findings:
            render_finding(finding)
            st.divider()
    else:
        st.info("No biomarker findings were triggered by the current v1 rule set.")

    st.subheader("Biomarker match table")
    if table_rows:
        st.dataframe(table_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No biomarker rows available from the current v1 rule set.")

    st.subheader("AI summary")
    st.caption("AI summary will be added in the next step.")

    st.divider()
    st.subheader("Result Quality Review")
    st.caption("Review how this result can be further analyzed in a private deployment, with deeper case-specific quality checks and internal QA support.")

    if st.button("Open Quality Review"):
        st.session_state.bm_quality_review_open = True
        st.rerun()

    if st.session_state.get("bm_quality_review_open"):
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

    with st.expander("Preview pasted biomarker text"):
        st.write(last_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
st.markdown("[Having issues? drop us an email](mailto:hello@lippershey.co)")
