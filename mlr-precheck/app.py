import re
import streamlit as st

SAMPLE_PROMO_TEXT = """Drug X significantly improved progression-free survival in adult patients with advanced solid tumors.
This breakthrough therapy was well tolerated and offers superior disease control.
See full prescribing information for warnings and precautions.
"""

SUPERLATIVE_TERMS = [
    "best", "breakthrough", "safer", "superior", "guaranteed",
    "guarantees", "unique", "unmatched", "leading", "most effective"
]

RISK_TERMS = [
    "risk", "risks", "warning", "warnings", "precaution", "precautions",
    "adverse", "adverse reactions", "side effects", "safety",
    "contraindication", "contraindications"
]

OFF_LABEL_TERMS = [
    "pediatric", "children", "adolescent", "pregnant", "pregnancy",
    "unapproved", "not approved", "off-label", "unlicensed"
]


def split_sentences(text: str) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def find_snippet(text: str, keyword: str, window: int = 160) -> str:
    lower_text = text.lower()
    idx = lower_text.find(keyword.lower())
    if idx == -1:
        return ""
    start = max(0, idx - 40)
    end = min(len(text), idx + window)
    return text[start:end].strip()


def detect_findings(text: str) -> list[dict]:
    findings = []
    lower_text = text.lower()
    sentences = split_sentences(text)

    # Rule 1: benefit claim without visible risk language nearby
    benefit_keywords = ["improved", "effective", "efficacy", "benefit", "response", "survival"]
    benefit_hits = [s for s in sentences if any(k in s.lower() for k in benefit_keywords)]
    risk_present_anywhere = any(term in lower_text for term in RISK_TERMS)

    if benefit_hits and not risk_present_anywhere:
        findings.append({
            "title": "Benefit claim without visible risk language nearby",
            "risk_level": "High",
            "why_flagged": "The text contains benefit-oriented language but no visible risk or safety language was detected in the submitted copy.",
            "matched_text": benefit_hits[0],
            "rule_reference": "FDA 21 CFR Part 202 / EU Directive 2001/83/EC Articles 87 and 89",
            "review_note": "Human review required."
        })

    # Rule 2: absolute / superlative promotional language
    for term in SUPERLATIVE_TERMS:
        if term in lower_text:
            findings.append({
                "title": "Absolute or superlative promotional language",
                "risk_level": "Medium",
                "why_flagged": f'The term "{term}" may overstate the claim or imply superiority without substantiation in the visible text.',
                "matched_text": find_snippet(text, term),
                "rule_reference": "FDA 21 CFR Part 202 / EU Directive 2001/83/EC Articles 87 and 89",
                "review_note": "Human review required."
            })
            break

    # Rule 3: off-label-looking population or indication language
    for term in OFF_LABEL_TERMS:
        if term in lower_text:
            findings.append({
                "title": "Potential off-label-looking population or indication language",
                "risk_level": "High",
                "why_flagged": f'The term "{term}" may indicate discussion of a population or use case that requires closer regulatory review.',
                "matched_text": find_snippet(text, term),
                "rule_reference": "FDA 21 CFR Part 202 / EU Directive 2001/83/EC Articles 87 and 89",
                "review_note": "Human review required."
            })
            break

    # Rule 4: missing cautionary language trigger
    caution_present = any(term in lower_text for term in ["warning", "warnings", "precaution", "precautions"])
    if not caution_present:
        findings.append({
            "title": "Missing cautionary language trigger",
            "risk_level": "Medium",
            "why_flagged": "No visible warning or precaution language was detected in the submitted text.",
            "matched_text": text[:220].strip(),
            "rule_reference": "FDA 21 CFR Part 202 / EU Directive 2001/83/EC Articles 87 and 89",
            "review_note": "Human review required."
        })

    return findings


def build_report(promo_text: str, findings: list[dict]) -> str:
    report = []
    report.append("MLR-PRECHECK REPORT")
    report.append("")
    report.append("This public demo uses a limited deterministic rules engine.")
    report.append("It does not determine compliance.")
    report.append("Human review is required.")
    report.append("No PDF or DOCX support is included in this public demo step.")
    report.append("")
    report.append("INPUT SUMMARY")
    report.append(f"Promotional text length: {len(promo_text)} characters")
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
        report.append("No findings triggered by the current v1 rule set.")
        report.append("")

    report.append("SCOPE LIMITS")
    report.append("- Text-only demo")
    report.append("- No PDF or DOCX support in this step")
    report.append("- No final legal or regulatory determination")
    report.append("")
    return "\n".join(report)


def render_finding(finding: dict):
    st.markdown(f"### {finding['title']}")
    st.write(f"**Risk level:** {finding['risk_level']}")
    st.write(f"**Why it was flagged:** {finding['why_flagged']}")
    st.write(f"**Matched text snippet:** {finding['matched_text']}")
    st.write(f"**Rule reference:** {finding['rule_reference']}")
    st.write(f"**Review note:** {finding['review_note']}")


st.set_page_config(page_title="MLR-PreCheck", layout="wide")

if "mlr_text" not in st.session_state:
    st.session_state.mlr_text = ""

st.title("MLR-PreCheck")
st.caption("Review promotional text for possible medical, legal, and regulatory risk signals.")

with st.expander("How to use", expanded=True):
    st.markdown("""
1. Paste promotional text into the input box
2. Click **Run pre-check**
3. Review the flagged findings and rule references
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
        st.session_state.mlr_text = SAMPLE_PROMO_TEXT
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.mlr_text = ""
        st.rerun()

with top_col3:
    st.caption("Use the sample promotional text for a quick demo, or reset the form.")

promo_text = st.text_area(
    "Promotional text",
    height=320,
    placeholder="Paste promotional copy here...",
    key="mlr_text"
)
st.caption(f"Characters: {len(promo_text)}/12000")

run_clicked = st.button("Run pre-check")

st.divider()

if not run_clicked and not promo_text.strip():
    st.info("Start by loading the sample text or pasting promotional text to evaluate.")

if run_clicked:
    if not promo_text.strip():
        st.warning("Please paste promotional text before running the pre-check.")
    elif len(promo_text) > 12000:
        st.error("The pasted text exceeds the 12,000 character limit.")
    else:
        findings = detect_findings(promo_text)
        report_text = build_report(promo_text, findings)

        st.success("Pre-check complete.")
        st.info("This output is generated by a limited deterministic rules engine. It does not determine compliance. Human review is required.")
        st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no final legal or regulatory determination.")

        st.download_button(
            label="Download text report",
            data=report_text,
            file_name="mlr_precheck_report.txt",
            mime="text/plain"
        )

        st.subheader("Findings")
        if findings:
            for finding in findings:
                render_finding(finding)
                st.divider()
        else:
            st.success("No findings were triggered by the current v1 rule set.")

        with st.expander("Preview pasted promotional text"):
            st.write(promo_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
