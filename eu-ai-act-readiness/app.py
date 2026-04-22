import streamlit as st

SAMPLE_USE_CASE = """We use an AI system to screen oncology trial candidates based on structured patient data and clinical notes.
The system ranks likely eligible patients for manual review by the study team.
Outputs are reviewed by humans before any enrollment decision is made.
We maintain audit logs, document model versions, and review system performance regularly.
The process includes validation, monitoring, and incident escalation to the digital governance team.
"""


CHECKS = [
    {
        "area": "Human oversight",
        "reference": "EU AI Act — Human Oversight",
        "keywords": ["human review", "human oversight", "manual review", "reviewed by humans", "override", "escalation"]
    },
    {
        "area": "Risk management",
        "reference": "EU AI Act — Risk Management",
        "keywords": ["risk management", "risk assessment", "hazard", "mitigation", "control measure", "risk register"]
    },
    {
        "area": "Data governance",
        "reference": "EU AI Act — Data Governance",
        "keywords": ["data source", "data quality", "data governance", "representative data", "training data", "clinical notes", "structured patient data"]
    },
    {
        "area": "Technical documentation",
        "reference": "EU AI Act — Technical Documentation",
        "keywords": ["documentation", "technical documentation", "model version", "versioning", "system description", "specification"]
    },
    {
        "area": "Logging / record-keeping",
        "reference": "EU AI Act — Logging / Record-Keeping",
        "keywords": ["log", "logs", "logging", "audit trail", "audit logs", "record-keeping", "traceability"]
    },
    {
        "area": "Transparency / instructions for use",
        "reference": "EU AI Act — Transparency / Instructions for Use",
        "keywords": ["instructions", "intended use", "limitation", "limitations", "user guidance", "warning to users", "appropriate use"]
    },
    {
        "area": "Accuracy / robustness / validation / monitoring",
        "reference": "EU AI Act — Accuracy, Robustness, Validation, Monitoring",
        "keywords": ["accuracy", "robustness", "validation", "monitoring", "performance review", "benchmark", "test set", "drift"]
    },
    {
        "area": "Quality management / governance process",
        "reference": "EU AI Act — Quality Management / Governance Process",
        "keywords": ["quality management", "governance", "approval process", "sop", "change management", "governance team", "control process"]
    },
    {
        "area": "Post-market monitoring / incident handling",
        "reference": "EU AI Act — Post-Market Monitoring / Incident Handling",
        "keywords": ["incident", "incident handling", "post-market", "feedback loop", "monitoring after deployment", "escalation", "corrective action"]
    },
]


def find_match_snippet(text: str, keywords: list[str], window: int = 180) -> str:
    lower_text = text.lower()
    for keyword in keywords:
        idx = lower_text.find(keyword.lower())
        if idx != -1:
            start = max(0, idx - 40)
            end = min(len(text), idx + window)
            return text[start:end].strip()
    return ""


def assess_readiness(text: str) -> list[dict]:
    results = []
    lower_text = text.lower()

    for check in CHECKS:
        matched_keywords = [kw for kw in check["keywords"] if kw.lower() in lower_text]
        if matched_keywords:
            results.append({
                "area": check["area"],
                "status": "Present",
                "why_flagged": f"Evidence of this readiness area was detected in the submitted text via keyword(s): {', '.join(matched_keywords[:3])}.",
                "matched_text": find_match_snippet(text, check["keywords"]),
                "reference": check["reference"],
                "review_note": "Human review required."
            })
        else:
            results.append({
                "area": check["area"],
                "status": "Missing",
                "why_flagged": "No clear evidence of this readiness area was detected in the submitted text.",
                "matched_text": "",
                "reference": check["reference"],
                "review_note": "Human review required."
            })

    return results


def build_report(use_case_text: str, results: list[dict]) -> str:
    present_count = sum(1 for r in results if r["status"] == "Present")
    missing_count = sum(1 for r in results if r["status"] == "Missing")

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
    report.append(f"Readiness areas checked: {len(results)}")
    report.append(f"Present: {present_count}")
    report.append(f"Missing: {missing_count}")
    report.append(f"Readiness score: {present_count}/{len(results)}")
    report.append("")
    report.append("READINESS RESULTS")

    for i, result in enumerate(results, start=1):
        report.append(f"{i}. {result['area']}")
        report.append(f"   Status: {result['status']}")
        report.append(f"   Why flagged: {result['why_flagged']}")
        if result["matched_text"]:
            report.append(f"   Matched text: {result['matched_text']}")
        else:
            report.append("   Matched text: None detected")
        report.append(f"   Reference area: {result['reference']}")
        report.append(f"   Review note: {result['review_note']}")
        report.append("")

    report.append("SCOPE LIMITS")
    report.append("- Text-only demo")
    report.append("- No PDF or DOCX support in this step")
    report.append("- No legal determination")
    report.append("- No definitive compliance classification")
    report.append("")
    return "\n".join(report)


def render_status_badge(status: str):
    if status == "Present":
        st.success(f"Status: {status}")
    elif status == "Missing":
        st.warning(f"Status: {status}")
    else:
        st.info(f"Status: {status}")


def render_result(result: dict):
    st.markdown(f"### {result['area']}")
    render_status_badge(result["status"])
    st.write(f"**Why it was flagged:** {result['why_flagged']}")
    if result["matched_text"]:
        st.write(f"**Matched text snippet:** {result['matched_text']}")
    else:
        st.write("**Matched text snippet:** None detected")
    st.write(f"**Reference area:** {result['reference']}")
    st.write(f"**Review note:** {result['review_note']}")


st.set_page_config(page_title="EU-AI-Act-Readiness", layout="wide")

if "eu_ai_text" not in st.session_state:
    st.session_state.eu_ai_text = ""

st.title("EU-AI-Act-Readiness")
st.caption("Assess an AI use case against a limited public-demo readiness workflow.")

with st.expander("How to use", expanded=True):
    st.markdown("""
1. Paste an AI use-case description into the input box
2. Click **Run readiness check**
3. Review the readiness results and reference areas
    """)

with st.expander("Public demo policy", expanded=False):
    st.markdown("""
- Testing only
- English only
- Paste text only in this demo step
- No PDF or DOCX support yet
- Maximum 12,000 characters
- No confidential, patient, or business-sensitive data
- Human review required
    """)

top_col1, top_col2, top_col3 = st.columns([1, 1, 3])

with top_col1:
    if st.button("Load sample use case"):
        st.session_state.eu_ai_text = SAMPLE_USE_CASE
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.eu_ai_text = ""
        st.rerun()

with top_col3:
    st.caption("Use the sample use case for a quick demo, or reset the form.")

use_case_text = st.text_area(
    "AI use-case description",
    height=320,
    placeholder="Describe the AI use case here...",
    key="eu_ai_text"
)
st.caption(f"Characters: {len(use_case_text)}/12000")

run_clicked = st.button("Run readiness check")

st.divider()

if not run_clicked and not use_case_text.strip():
    st.info("Start by loading the sample use case or pasting an AI use-case description to evaluate.")

if run_clicked:
    if not use_case_text.strip():
        st.warning("Please paste an AI use-case description before running the readiness check.")
    elif len(use_case_text) > 12000:
        st.error("The pasted text exceeds the 12,000 character limit.")
    else:
        results = assess_readiness(use_case_text)
        report_text = build_report(use_case_text, results)

        present_count = sum(1 for r in results if r["status"] == "Present")
        missing_count = sum(1 for r in results if r["status"] == "Missing")

        st.success("Readiness check complete.")
        st.info("This output is generated by a limited deterministic checklist engine. It does not make a legal determination. Human review is required.")
        st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no legal determination, no definitive compliance classification.")

        st.download_button(
            label="Download text report",
            data=report_text,
            file_name="eu_ai_act_readiness_report.txt",
            mime="text/plain"
        )

        st.subheader("Assessment summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Readiness areas checked", len(results))
        col2.metric("Present", present_count)
        col3.metric("Missing", missing_count)
        col4.metric("Readiness score", f"{present_count}/{len(results)}")

        st.subheader("Readiness results")
        for result in results:
            render_result(result)
            st.divider()

        with st.expander("Preview pasted use-case description"):
            st.write(use_case_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
