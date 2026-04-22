import re
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
        "strong_keywords": [
            "human oversight", "human review", "manual review", "reviewed by humans",
            "human-in-the-loop", "human in the loop", "hitl", "override", "manual sign-off"
        ],
        "weak_keywords": [
            "clinician review", "medical review", "review by team", "sign off", "sign-off"
        ],
    },
    {
        "area": "Risk management",
        "reference": "EU AI Act — Risk Management",
        "strong_keywords": [
            "risk management", "risk assessment", "risk register", "residual risk",
            "control measure", "mitigation measure", "hazard analysis"
        ],
        "weak_keywords": [
            "mitigates risks", "identify risks", "identified risks", "foreseeable risks",
            "risk mitigation", "safety risk"
        ],
    },
    {
        "area": "Data governance",
        "reference": "EU AI Act — Data Governance",
        "strong_keywords": [
            "data governance", "data quality", "training data", "validation data",
            "test data", "representative data", "data provenance"
        ],
        "weak_keywords": [
            "clinical notes", "structured patient data", "ehr", "electronic health records",
            "bias mitigation", "bias detection", "representative", "data source"
        ],
    },
    {
        "area": "Technical documentation",
        "reference": "EU AI Act — Technical Documentation",
        "strong_keywords": [
            "technical documentation", "annex iv", "system architecture",
            "model specification", "system description", "documentation package"
        ],
        "weak_keywords": [
            "documentation", "model version", "versioning", "specification", "audit-ready"
        ],
    },
    {
        "area": "Logging / record-keeping",
        "reference": "EU AI Act — Logging / Record-Keeping",
        "strong_keywords": [
            "audit trail", "audit log", "audit logs", "record-keeping",
            "traceability", "tamper-proof log", "event logs"
        ],
        "weak_keywords": [
            "logging", "logs", "record retention", "trace logs"
        ],
    },
    {
        "area": "Transparency / instructions for use",
        "reference": "EU AI Act — Transparency / Instructions for Use",
        "strong_keywords": [
            "instructions for use", "intended use", "user guidance",
            "appropriate use", "limitations", "warning to users"
        ],
        "weak_keywords": [
            "transparency", "explainability", "interpretability", "user instructions"
        ],
    },
    {
        "area": "Accuracy / robustness / validation / monitoring",
        "reference": "EU AI Act — Accuracy, Robustness, Validation, Monitoring",
        "strong_keywords": [
            "accuracy", "robustness", "validation", "monitoring",
            "performance review", "drift detection", "model drift",
            "adversarial testing", "benchmarking"
        ],
        "weak_keywords": [
            "stress tests", "stress testing", "real-world evidence", "rwe",
            "toxicity reports", "performance", "monitor"
        ],
    },
    {
        "area": "Quality management / governance process",
        "reference": "EU AI Act — Quality Management / Governance Process",
        "strong_keywords": [
            "quality management system", "qms", "governance committee",
            "change management", "approval process", "control process"
        ],
        "weak_keywords": [
            "governance", "digital governance", "sop", "committee", "oversight team"
        ],
    },
    {
        "area": "Post-market monitoring / incident handling",
        "reference": "EU AI Act — Post-Market Monitoring / Incident Handling",
        "strong_keywords": [
            "post-market monitoring", "post market monitoring", "incident handling",
            "serious incident", "corrective action", "supervisory authority"
        ],
        "weak_keywords": [
            "incident escalation", "post-market surveillance", "pms", "post market surveillance",
            "feedback loop", "surveillance loop"
        ],
    },
]


def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_keyword_match(text: str, keywords: list[str]):
    normalized = normalize_text(text)
    for keyword in keywords:
        normalized_keyword = normalize_text(keyword)
        pattern = r"\b" + re.escape(normalized_keyword) + r"\b"
        match = re.search(pattern, normalized)
        if match:
            return keyword, match.start(), match.end()
    return None, None, None


def extract_snippet_from_normalized(text: str, start_idx: int, end_idx: int, window: int = 120) -> str:
    normalized = normalize_text(text)
    if start_idx is None:
        return ""
    start = max(0, start_idx - 40)
    end = min(len(normalized), end_idx + window)
    return normalized[start:end].strip()


def assess_readiness(text: str) -> list[dict]:
    results = []

    for check in CHECKS:
        strong_kw, strong_start, strong_end = find_keyword_match(text, check["strong_keywords"])
        weak_kw, weak_start, weak_end = find_keyword_match(text, check["weak_keywords"])

        if strong_kw:
            results.append({
                "area": check["area"],
                "status": "Present",
                "score_value": 1.0,
                "why_flagged": f'Evidence of this readiness area was detected via strong keyword match: "{strong_kw}".',
                "matched_text": extract_snippet_from_normalized(text, strong_start, strong_end),
                "reference": check["reference"],
                "review_note": "Human review required."
            })
        elif weak_kw:
            results.append({
                "area": check["area"],
                "status": "Partial",
                "score_value": 0.5,
                "why_flagged": f'Possible evidence of this readiness area was detected via weaker keyword match: "{weak_kw}".',
                "matched_text": extract_snippet_from_normalized(text, weak_start, weak_end),
                "reference": check["reference"],
                "review_note": "Human review required."
            })
        else:
            results.append({
                "area": check["area"],
                "status": "Missing",
                "score_value": 0.0,
                "why_flagged": "No clear evidence of this readiness area was detected in the submitted text.",
                "matched_text": "",
                "reference": check["reference"],
                "review_note": "Human review required."
            })

    return results


def build_report(use_case_text: str, results: list[dict]) -> str:
    present_count = sum(1 for r in results if r["status"] == "Present")
    partial_count = sum(1 for r in results if r["status"] == "Partial")
    missing_count = sum(1 for r in results if r["status"] == "Missing")
    readiness_score = sum(r["score_value"] for r in results)

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
    report.append(f"Partial: {partial_count}")
    report.append(f"Missing: {missing_count}")
    report.append(f"Readiness score: {readiness_score:.1f}/{len(results)}")
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
    elif status == "Partial":
        st.info(f"Status: {status}")
    elif status == "Missing":
        st.warning(f"Status: {status}")
    else:
        st.write(f"Status: {status}")


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
        partial_count = sum(1 for r in results if r["status"] == "Partial")
        missing_count = sum(1 for r in results if r["status"] == "Missing")
        readiness_score = sum(r["score_value"] for r in results)

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
        col3.metric("Partial", partial_count)
        col4.metric("Missing", missing_count)

        st.metric("Readiness score", f"{readiness_score:.1f}/{len(results)}")

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
