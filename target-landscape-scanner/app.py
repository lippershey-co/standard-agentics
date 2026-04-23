import re
import streamlit as st

SAMPLE_TEXT = """Target landscape scan input

Date range: last 90 days
Tumor focus: NSCLC, CRC, breast cancer

Recent observations:
- Claudin 18.2 continues to attract GI oncology activity, with multiple new programs discussed across gastric and pancreatic settings.
- DLL3 remains active in small cell lung cancer, with new trial activity and continued big-pharma interest.
- B7-H3 appears in several new solid tumor programs, including radioligand and ADC approaches.
- TIGIT momentum appears weaker than last year, with fewer clearly differentiated updates.
- KRAS G12D interest is rising, especially in pancreatic and colorectal pipelines.
- HER3 remains relevant through ADC competition in breast and lung tumors.
- EGFR remains crowded, especially in NSCLC, but newer mutation-specific positioning is still emerging.
- Mesothelin shows selective activity, mostly in ovarian and pancreatic development programs.
"""

TARGET_RULES = [
    {"target": "Claudin 18.2", "aliases": ["claudin 18.2", "claudin18.2"], "signal": "Emerging / active"},
    {"target": "DLL3", "aliases": ["dll3"], "signal": "Emerging / active"},
    {"target": "B7-H3", "aliases": ["b7-h3", "b7h3"], "signal": "Emerging / active"},
    {"target": "TIGIT", "aliases": ["tigit"], "signal": "Cooling / mixed"},
    {"target": "KRAS G12D", "aliases": ["kras g12d"], "signal": "Rising"},
    {"target": "HER3", "aliases": ["her3"], "signal": "Active"},
    {"target": "EGFR", "aliases": ["egfr"], "signal": "Crowded / mature"},
    {"target": "Mesothelin", "aliases": ["mesothelin"], "signal": "Selective / niche"},
]

TUMOR_TYPES = [
    "nsclc", "small cell lung", "lung", "crc", "colorectal", "breast", "ovarian",
    "pancreatic", "gastric", "solid tumor", "solid tumors"
]

def find_sentence_snippet(text: str, keyword: str, max_len: int = 240) -> str:
    lower_text = text.lower()
    lower_keyword = keyword.lower()
    idx = lower_text.find(lower_keyword)
    if idx == -1:
        return ""

    start = max(
        text.rfind(".", 0, idx),
        text.rfind("\n", 0, idx)
    )
    end_dot = text.find(".", idx)
    end_nl = text.find("\n", idx)

    candidates = [x for x in [end_dot, end_nl] if x != -1]
    end = min(candidates) if candidates else len(text)

    start = 0 if start == -1 else start + 1
    snippet = " ".join(text[start:end].strip().split())

    if len(snippet) > max_len:
        snippet = snippet[:max_len].rsplit(" ", 1)[0] + "..."
    return snippet

def detect_tumor_types(snippet: str) -> list[str]:
    found = []
    lower = snippet.lower()
    for tumor in TUMOR_TYPES:
        if tumor in lower:
            found.append(tumor)
    # normalize display
    pretty = []
    for tumor in found:
        label = tumor.upper() if tumor in ["nsclc", "crc", "egfr"] else tumor.title()
        if label not in pretty:
            pretty.append(label)
    return pretty[:3]

def build_target_findings(text: str):
    findings = []
    table_rows = []
    lower_text = text.lower()

    for rule in TARGET_RULES:
        matched_alias = next((a for a in rule["aliases"] if a in lower_text), None)
        if matched_alias:
            snippet = find_sentence_snippet(text, matched_alias)
            tumors = detect_tumor_types(snippet)
            findings.append({
                "title": f"Target activity detected: {rule['target']}",
                "risk_level": "Info",
                "why_flagged": f'The submitted scan text includes explicit reference to "{rule["target"]}", suggesting target-landscape activity worth review.',
                "matched_text": snippet or rule["target"],
                "rule_reference": "Target landscape heuristic",
                "review_note": "Human review required.",
            })
            table_rows.append({
                "Target": rule["target"],
                "Signal": rule["signal"],
                "Tumor Types": ", ".join(tumors) if tumors else "Not clearly stated",
                "Evidence": snippet or rule["target"],
            })

    return findings, table_rows

def build_report(text: str, findings: list[dict], table_rows: list[dict]) -> str:
    report = []
    report.append("TARGET-LANDSCAPE-SCANNER REPORT")
    report.append("")
    report.append("This public demo uses a limited deterministic scan engine.")
    report.append("It does not determine strategic attractiveness, scientific validity, or competitive priority.")
    report.append("Human review is required.")
    report.append("No PDF or DOCX support is included in this public demo step.")
    report.append("")
    report.append("INPUT SUMMARY")
    report.append(f"Scan text length: {len(text)} characters")
    report.append(f"Targets detected: {len(table_rows)}")
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
        report.append("No target activity was detected by the current v1 rule set.")
        report.append("")

    report.append("TOP TARGET TABLE")
    if table_rows:
        for row in table_rows:
            report.append(f"- {row['Target']} | {row['Signal']} | {row['Tumor Types']}")
    else:
        report.append("- No rows available")
    report.append("")
    report.append("SCOPE LIMITS")
    report.append("- Text-only demo")
    report.append("- No PDF or DOCX support in this step")
    report.append("- No final scientific, commercial, or strategic determination")
    report.append("")
    return "\n".join(report)

def render_risk_badge(risk_level: str):
    if risk_level == "High":
        st.error(f"Risk level: {risk_level}")
    elif risk_level == "Medium":
        st.warning(f"Risk level: {risk_level}")
    elif risk_level == "Low":
        st.info(f"Risk level: {risk_level}")
    else:
        st.caption(f"Risk level: {risk_level}")

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

st.set_page_config(page_title="Target-Landscape-Scanner", layout="wide")

defaults = {
    "tls_text": "",
    "tls_done": False,
    "tls_last_text": "",
    "tls_last_findings": [],
    "tls_last_table_rows": [],
    "tls_last_report": "",
    "tls_ai_summary": "",
    "tls_quality_review_open": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("Target-Landscape-Scanner")
st.caption("Scan oncology target-landscape notes for visible target activity and produce a simple ranked review table.")

with st.expander("How this tool works", expanded=True):
    st.markdown("""
### Deterministic scan engine
This tool checks submitted scan text against a limited set of v1 target-activity heuristics.
This deterministic layer is the **source of truth** for findings shown in the public demo.

### Claude-based AI summary
An optional Claude-based AI summary layer can later rewrite deterministic findings into a more readable reviewer note.
This AI layer is **assistive only**. It does not replace deterministic findings or human review.

### Public demo limits
- Paste plain text only
- Discovery / target-landscape text only
- Deterministic review up to 12,000 characters
- AI summary limited to smaller inputs and restricted public-demo usage
- No PDF or DOCX support in the public demo
- No confidential, patient, or business-sensitive data

[Having issues? drop us an email](mailto:hello@lippershey.co)
    """)

with st.expander("How to use", expanded=False):
    st.markdown("""
1. Paste target-landscape notes or a scan summary
2. Click **Run landscape scan**
3. Review deterministic findings
4. Review the simple target table
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
        st.session_state.tls_text = SAMPLE_TEXT
        st.session_state.tls_done = False
        st.session_state.tls_ai_summary = ""
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.tls_text = ""
        st.session_state.tls_done = False
        st.session_state.tls_last_text = ""
        st.session_state.tls_last_findings = []
        st.session_state.tls_last_table_rows = []
        st.session_state.tls_last_report = ""
        st.session_state.tls_ai_summary = ""
        st.session_state.tls_quality_review_open = False
        st.rerun()

with top_col3:
    st.caption("Use the sample scan text for a quick demo, or reset the form.")

text = st.text_area(
    "Target landscape scan text",
    height=320,
    placeholder="Paste discovery or target-landscape text here...",
    key="tls_text"
)
st.caption(f"Characters: {len(text)}/12000")

if st.button("Run landscape scan"):
    if not text.strip():
        st.warning("Please paste scan text before running the landscape scan.")
    elif len(text) > 12000:
        st.error("Public demo limit reached: this text exceeds 12,000 characters. For larger scans or supported workflows, contact us for pricing.")
        st.session_state.tls_done = False
    else:
        findings, table_rows = build_target_findings(text)
        report_text = build_report(text, findings, table_rows)
        st.session_state.tls_last_text = text
        st.session_state.tls_last_findings = findings
        st.session_state.tls_last_table_rows = table_rows
        st.session_state.tls_last_report = report_text
        st.session_state.tls_done = True
        st.session_state.tls_ai_summary = ""
        st.session_state.tls_quality_review_open = False
        st.rerun()

st.divider()

if not st.session_state.tls_done and not text.strip():
    st.info("Start by loading the sample text or pasting a target-landscape summary to evaluate.")

if st.session_state.tls_done:
    last_text = st.session_state.tls_last_text
    findings = st.session_state.tls_last_findings
    table_rows = st.session_state.tls_last_table_rows
    report_text = st.session_state.tls_last_report

    st.success("Landscape scan complete.")
    st.info("This output is generated by a limited deterministic scan engine. It does not determine scientific validity, strategic attractiveness, or competitive priority. Human review is required.")
    st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no final scientific or strategic determination.")

    st.download_button(
        label="Download text report",
        data=report_text,
        file_name="target_landscape_scanner_report.txt",
        mime="text/plain"
    )

    st.subheader("Findings")
    if findings:
        for finding in findings:
            render_finding(finding)
            st.divider()
    else:
        st.info("No target activity was detected by the current v1 rule set.")

    st.subheader("Target activity table")
    if table_rows:
        st.dataframe(table_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No target rows available from the current v1 rule set.")

    st.subheader("AI summary")
    st.caption("AI summary will be added in the next step.")

    st.divider()
    st.subheader("Result Quality Review")
    st.caption("Review how this result can be further analyzed in a private deployment, with deeper case-specific quality checks and internal QA support.")

    if st.button("Open Quality Review"):
        st.session_state.tls_quality_review_open = True
        st.rerun()

    if st.session_state.get("tls_quality_review_open"):
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

    with st.expander("Preview pasted scan text"):
        st.write(last_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
st.markdown("[Having issues? drop us an email](mailto:hello@lippershey.co)")
