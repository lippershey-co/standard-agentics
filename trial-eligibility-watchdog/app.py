import re
import streamlit as st

SAMPLE_TRIAL_ID = "NCT-DEMO-001"

SAMPLE_ELIGIBILITY_TEXT = """Inclusion Criteria:
- Adults aged 18 years or older
- Histologically confirmed metastatic non-small cell lung cancer
- ECOG performance status 0-1
- At least one measurable lesion per RECIST 1.1
- Prior platinum-based chemotherapy allowed

Exclusion Criteria:
- Active untreated brain metastases
- Significant cardiovascular disease within 6 months
- Prior treatment with the investigational study drug
"""

CHANGE_TRIGGER_TERMS = [
    "must", "required", "only", "prior", "allowed", "excluded",
    "exclusion", "inclusion", "ecog", "measurable", "metastatic",
    "brain metastases", "cardiovascular"
]


def split_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def normalize_line(line: str) -> str:
    line = line.lower().strip()
    line = re.sub(r"\s+", " ", line)
    return line


def looks_like_trial_scope(text: str) -> bool:
    lower_text = text.lower()
    scope_terms = [
        "inclusion criteria", "exclusion criteria", "ecog", "metastatic",
        "brain metastases", "eligibility", "trial", "study", "recist",
        "measurable lesion", "performance status", "cardiovascular"
    ]
    return any(term in lower_text for term in scope_terms)


def ai_summary_allowed(text: str) -> tuple[bool, str]:
    if len(text) > 3500:
        return False, "Deterministic review completed. AI summary is limited to 3,500 characters in the public demo. For larger inputs and extended review support, contact us for pricing."
    if not looks_like_trial_scope(text):
        return False, "This public demo AI summary is limited to trial eligibility or screening text. For broader document review or custom workflows, contact us for pricing."
    return True, ""


def detect_watchdog_findings(trial_id: str, eligibility_text: str) -> list[dict]:
    findings = []
    lines = split_lines(eligibility_text)
    lower_text = eligibility_text.lower()

    if trial_id.strip():
        findings.append({
            "title": "Trial identifier provided",
            "risk_level": "Info",
            "why_flagged": f'The review is anchored to the provided trial identifier: "{trial_id.strip()}".',
            "matched_text": trial_id.strip(),
            "rule_reference": "Structured metadata anchor",
            "review_note": "Human review required."
        })

    if "inclusion criteria" not in lower_text and "exclusion criteria" not in lower_text:
        findings.append({
            "title": "Criteria structure may be incomplete",
            "risk_level": "Medium",
            "why_flagged": "The submitted text does not clearly separate inclusion and exclusion criteria.",
            "matched_text": eligibility_text[:220].strip(),
            "rule_reference": "Trial criteria structure heuristic",
            "review_note": "Human review required."
        })

    matched_terms = [term for term in CHANGE_TRIGGER_TERMS if term in lower_text]
    if matched_terms:
        findings.append({
            "title": "Potential eligibility tightening or screening impact terms detected",
            "risk_level": "Medium",
            "why_flagged": "The submitted criteria include terms that often affect screening burden or enrollment eligibility. Matched terms: " + ", ".join(matched_terms[:8]),
            "matched_text": lines[0] if lines else "",
            "rule_reference": "Eligibility screening heuristic",
            "review_note": "Human review required."
        })

    if "ecog" in lower_text and ("0-1" in lower_text or "0/1" in lower_text):
        findings.append({
            "title": "Performance status restriction detected",
            "risk_level": "Medium",
            "why_flagged": "A performance status restriction was detected and may materially affect the eligible population.",
            "matched_text": next((line for line in lines if "ecog" in line.lower()), ""),
            "rule_reference": "Eligibility population narrowing heuristic",
            "review_note": "Human review required."
        })

    if "brain metastases" in lower_text and ("exclude" in lower_text or "exclusion" in lower_text or "untreated" in lower_text):
        findings.append({
            "title": "Potential CNS-related exclusion detected",
            "risk_level": "Medium",
            "why_flagged": "The criteria appear to include a brain metastases-related exclusion, which may significantly affect enrollment.",
            "matched_text": next((line for line in lines if "brain metastases" in line.lower()), ""),
            "rule_reference": "Eligibility exclusion heuristic",
            "review_note": "Human review required."
        })

    return findings


def build_report(trial_id: str, eligibility_text: str, findings: list[dict]) -> str:
    report = []
    report.append("TRIAL-ELIGIBILITY-WATCHDOG REPORT")
    report.append("")
    report.append("This public demo uses a limited deterministic review engine.")
    report.append("It does not determine trial feasibility or regulatory acceptability.")
    report.append("Human review is required.")
    report.append("")
    report.append("INPUT SUMMARY")
    report.append(f"Trial identifier: {trial_id.strip() or 'Not provided'}")
    report.append(f"Eligibility text length: {len(eligibility_text)} characters")
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
    report.append("- No final feasibility or regulatory determination")
    report.append("")
    return "\n".join(report)


def generate_ai_summary_placeholder(trial_id: str, findings: list[dict]) -> str:
    if not findings:
        return (
            "No deterministic findings were triggered by the current v1 rule set. "
            "Once connected, the Claude-based AI summary will turn this result into a short plain-language reviewer note."
        )

    lines = []
    lines.append("Claude-based AI summary preview")
    lines.append("")
    lines.append("This placeholder shows where the assistive AI summary will appear.")
    lines.append("It will summarize deterministic findings only, not replace them.")
    lines.append("")
    if trial_id.strip():
        lines.append(f"Trial identifier: {trial_id.strip()}")
    lines.append(f"Number of deterministic findings: {len(findings)}")
    lines.append("Top flagged issues:")
    for finding in findings[:3]:
        lines.append(f"- {finding['title']} ({finding['risk_level']})")
    lines.append("")
    lines.append("Human review is still required.")
    return "\n".join(lines)


def render_risk_badge(risk_level: str):
    if risk_level == "High":
        st.error(f"Risk level: {risk_level}")
    elif risk_level == "Medium":
        st.warning(f"Risk level: {risk_level}")
    elif risk_level == "Low":
        st.info(f"Risk level: {risk_level}")
    elif risk_level == "Info":
        st.caption(f"Risk level: {risk_level}")
    else:
        st.write(f"Risk level: {risk_level}")


def render_finding(finding: dict):
    st.markdown(f"### {finding['title']}")
    render_risk_badge(finding["risk_level"])
    st.write(f"**Why it was flagged:** {finding['why_flagged']}")
    st.write(f"**Matched text snippet:** {finding['matched_text'] or 'None'}")
    st.write(f"**Rule reference:** {finding['rule_reference']}")
    st.write(f"**Review note:** {finding['review_note']}")


st.set_page_config(page_title="Trial-Eligibility-Watchdog", layout="wide")

defaults = {
    "tew_trial_id": "",
    "tew_text": "",
    "tew_done": False,
    "tew_last_trial_id": "",
    "tew_last_text": "",
    "tew_last_findings": [],
    "tew_last_report": "",
    "tew_ai_summary": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("Trial-Eligibility-Watchdog")
st.caption("Track and review clinical trial eligibility criteria for possible screening or enrollment-impact signals.")

with st.expander("How this tool works", expanded=True):
    st.markdown("""
### Deterministic review engine
This tool first runs a deterministic Python review engine.  
It checks the submitted eligibility text against a fixed set of structural and screening-impact heuristics.  
This deterministic layer is the **source of truth** for findings shown in the public demo.

### Claude-based AI summary
An optional Claude-based AI summary layer can later rewrite deterministic findings into a more readable reviewer note.  
This AI layer is **assistive only**. It does not replace deterministic findings or human review.

### Public demo limits
- Paste plain text only
- Trial eligibility / screening text only
- Deterministic review: up to 12,000 characters
- AI summary: limited to smaller inputs and restricted public-demo usage
- No PDF or DOCX support in the public demo
- No patient, personal, or confidential commercial data

[Having issues? drop us an email](mailto:hello@lippershey.co)
    """)

with st.expander("How to use", expanded=False):
    st.markdown("""
1. Enter a trial identifier if available
2. Paste eligibility criteria text
3. Click **Run watchdog**
4. Review deterministic findings
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
        st.session_state.tew_trial_id = SAMPLE_TRIAL_ID
        st.session_state.tew_text = SAMPLE_ELIGIBILITY_TEXT
        st.session_state.tew_done = False
        st.session_state.tew_ai_summary = ""
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.tew_trial_id = ""
        st.session_state.tew_text = ""
        st.session_state.tew_done = False
        st.session_state.tew_last_trial_id = ""
        st.session_state.tew_last_text = ""
        st.session_state.tew_last_findings = []
        st.session_state.tew_last_report = ""
        st.session_state.tew_ai_summary = ""
        st.rerun()

with top_col3:
    st.caption("Use the sample eligibility text for a quick demo, or reset the form.")

trial_id = st.text_input(
    "Trial identifier / NCT ID",
    placeholder="Example: NCT01234567",
    key="tew_trial_id"
)

eligibility_text = st.text_area(
    "Eligibility criteria text",
    height=320,
    placeholder="Paste eligibility criteria here...",
    key="tew_text"
)
st.caption(f"Characters: {len(eligibility_text)}/12000")

if st.button("Run watchdog"):
    if not eligibility_text.strip():
        st.warning("Please paste eligibility criteria text before running the watchdog.")
    elif len(eligibility_text) > 12000:
        st.error("Public demo limit reached: this text exceeds 12,000 characters. For larger criteria sets or supported workflows, contact us for pricing.")
        st.session_state.tew_done = False
    else:
        findings = detect_watchdog_findings(trial_id, eligibility_text)
        report_text = build_report(trial_id, eligibility_text, findings)
        st.session_state.tew_last_trial_id = trial_id
        st.session_state.tew_last_text = eligibility_text
        st.session_state.tew_last_findings = findings
        st.session_state.tew_last_report = report_text
        st.session_state.tew_done = True
        st.session_state.tew_ai_summary = ""
        st.rerun()

st.divider()

if not st.session_state.tew_done and not eligibility_text.strip():
    st.info("Start by loading the sample text or pasting eligibility criteria to evaluate.")

if st.session_state.tew_done:
    last_trial_id = st.session_state.tew_last_trial_id
    last_text = st.session_state.tew_last_text
    findings = st.session_state.tew_last_findings
    report_text = st.session_state.tew_last_report

    st.success("Watchdog review complete.")
    st.info("This output is generated by a limited deterministic review engine. It does not determine feasibility, eligibility approval, or regulatory acceptability. Human review is required.")
    st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no final feasibility or regulatory determination.")

    st.download_button(
        label="Download text report",
        data=report_text,
        file_name="trial_eligibility_watchdog_report.txt",
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
            st.info(generate_ai_summary_placeholder(last_trial_id, findings))
        else:
            st.caption("AI summary is available for this input under current public-demo limits.")
    else:
        st.warning(ai_message)

    with st.expander("Preview pasted eligibility text"):
        st.write(last_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
st.markdown("[Having issues? drop us an email](mailto:hello@lippershey.co)")
