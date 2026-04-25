import re
import streamlit as st

SAMPLE_TEXT = """SAE narrative draft

Patient context:
Adult patient with metastatic colorectal cancer receiving VX-247 plus chemotherapy.

Event:
The patient developed grade 4 neutropenic sepsis requiring hospital admission.

Suspect product exposure:
The event occurred after cycle 2 of VX-247 treatment.

Chronology:
Fever and hypotension began 3 days after the second infusion.

Seriousness / outcome:
The event was considered serious due to hospitalization and life-threatening clinical status.
The patient improved after ICU support and broad-spectrum antibiotics.

Action taken:
Study treatment was interrupted.

Follow-up:
No rechallenge was performed. Additional lab follow-up is pending.
"""

SAE_RULES = [
    {
        "title": "Patient context detected",
        "patterns": [r"\bpatient context\b", r"\badult patient\b", r"\bmale patient\b", r"\bfemale patient\b"],
        "risk_level": "Info",
        "type": "Patient context",
        "why": "The narrative appears to include patient context relevant for SAE completeness review.",
    },
    {
        "title": "Event description detected",
        "patterns": [r"\bevent\b", r"\bdeveloped\b", r"\bsepsis\b", r"\badverse event\b"],
        "risk_level": "Info",
        "type": "Event description",
        "why": "The narrative appears to include an adverse-event description relevant for completeness review.",
    },
    {
        "title": "Exposure / suspect product context detected",
        "patterns": [r"\bsuspect product exposure\b", r"\bafter cycle\b", r"\btreatment\b", r"\binfusion\b"],
        "risk_level": "Info",
        "type": "Exposure context",
        "why": "The narrative appears to include suspect-product exposure context relevant for chronology and causality review.",
    },
    {
        "title": "Chronology detected",
        "patterns": [r"\bchronology\b", r"\bbegan\b", r"\bdays after\b", r"\bonset\b"],
        "risk_level": "Info",
        "type": "Chronology / onset",
        "why": "The narrative appears to include chronology or onset timing relevant for SAE review.",
    },
    {
        "title": "Seriousness / outcome detected",
        "patterns": [r"\bserious\b", r"\bhospitalization\b", r"\blife-threatening\b", r"\boutcome\b", r"\bimproved\b"],
        "risk_level": "Info",
        "type": "Seriousness / outcome",
        "why": "The narrative appears to include seriousness and/or outcome information relevant for SAE completeness.",
    },
    {
        "title": "Action taken detected",
        "patterns": [r"\baction taken\b", r"\binterrupted\b", r"\bdiscontinued\b", r"\bdose reduced\b"],
        "risk_level": "Info",
        "type": "Action taken",
        "why": "The narrative appears to include action-taken information relevant for case review.",
    },
    {
        "title": "Follow-up or rechallenge context detected",
        "patterns": [r"\bfollow-up\b", r"\brechallenge\b", r"\bdechallenge\b", r"\bpending\b"],
        "risk_level": "Low",
        "type": "Follow-up completeness",
        "why": "The narrative appears to include follow-up or rechallenge/dechallenge context relevant for completeness review.",
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

def looks_like_sae_scope(text: str) -> bool:
    lower_text = text.lower()
    scope_terms = [
        "sae",
        "seriousness",
        "outcome",
        "patient context",
        "suspect product exposure",
        "chronology",
        "follow-up",
        "rechallenge",
        "dechallenge",
        "hospitalization",
        "life-threatening",
        "safety-case narrative",
    ]
    return any(term in lower_text for term in scope_terms)


def ai_summary_allowed(text: str):
    if len(text) > 3500:
        return False, "Deterministic review completed. AI summary is limited to 3,500 characters in the public demo. For larger inputs and extended review support, contact us for pricing."
    if not looks_like_sae_scope(text):
        return False, "This public demo AI summary is limited to SAE, safety-case, or narrative-review text. For broader document review or custom workflows, contact us for pricing."
    return True, ""


def detect_sae_findings(text: str):
    findings = []
    table_rows = []

    for rule in SAE_RULES:
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
                "rule_reference": "SAE narrative completeness heuristic",
                "review_note": "Human review required.",
            })
            table_rows.append({
                "Narrative Element": rule["type"],
                "Status": "Detected",
                "Evidence": snippet,
                "Suggested Review Direction": "Confirm whether this SAE narrative element is sufficiently documented for internal safety reporting or case review.",
            })

    return findings, table_rows

def build_report(text: str, findings: list[dict], table_rows: list[dict]) -> str:
    report = []
    report.append("SAE-NARRATIVE-SCORER REPORT")
    report.append("")
    report.append("This public demo uses a limited deterministic SAE narrative completeness engine.")
    report.append("It does not determine MedWatch/EudraVigilance submission readiness, medical causality, or final reporting adequacy.")
    report.append("Human review is required.")
    report.append("No PDF or DOCX support is included in this public demo step.")
    report.append("")
    report.append("INPUT SUMMARY")
    report.append(f"Input length: {len(text)} characters")
    report.append(f"Completeness rows detected: {len(table_rows)}")
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
        report.append("No SAE narrative findings were triggered by the current v1 rule set.")
        report.append("")

    report.append("SAE COMPLETENESS TABLE")
    if table_rows:
        for row in table_rows:
            report.append(
                f"- {row['Narrative Element']} | {row['Status']} | {row['Evidence']}"
            )
    else:
        report.append("- No SAE completeness rows available")
    report.append("")
    report.append("SCOPE LIMITS")
    report.append("- Text-only demo")
    report.append("- No PDF or DOCX support in this step")
    report.append("- No final safety-reporting or submission-readiness determination")
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

st.set_page_config(page_title="SAE-Narrative-Scorer", layout="wide")

defaults = {
    "sae_text": "",
    "sae_done": False,
    "sae_last_text": "",
    "sae_last_findings": [],
    "sae_last_table_rows": [],
    "sae_last_report": "",
    "sae_ai_summary": "",
    "sae_quality_review_open": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("SAE-Narrative-Scorer")
st.caption("Review SAE narrative text for visible completeness elements before deeper safety review.")

with st.expander("How this tool works", expanded=True):
    st.markdown("""
### Deterministic SAE narrative engine
This tool checks submitted SAE narrative text against a limited set of v1 completeness heuristics.
This deterministic layer is the **source of truth** for findings shown in the public demo.

### Claude-based AI summary
An optional Claude-based AI summary layer can later rewrite deterministic findings into a more readable reviewer note.
This AI layer is **assistive only**. It does not replace deterministic findings or human review.

### Public demo limits
- Paste plain text only
- SAE / safety-case narrative text only
- Deterministic review up to 12,000 characters
- AI summary limited to smaller inputs and restricted public-demo usage
- No PDF or DOCX support in the public demo
- No confidential, patient, or business-sensitive data

[Having issues? drop us an email](mailto:hello@lippershey.co)
    """)

with st.expander("How to use", expanded=False):
    st.markdown("""
1. Paste SAE narrative text
2. Click **Run SAE narrative review**
3. Review deterministic findings
4. Review the SAE completeness table
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
        st.session_state.sae_text = SAMPLE_TEXT
        st.session_state.sae_done = False
        st.session_state.sae_ai_summary = ""
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.sae_text = ""
        st.session_state.sae_done = False
        st.session_state.sae_last_text = ""
        st.session_state.sae_last_findings = []
        st.session_state.sae_last_table_rows = []
        st.session_state.sae_last_report = ""
        st.session_state.sae_ai_summary = ""
        st.session_state.sae_quality_review_open = False
        st.rerun()

with top_col3:
    st.caption("Use the sample SAE narrative for a quick demo, or reset the form.")

text = st.text_area(
    "SAE / safety-case narrative text",
    height=320,
    placeholder="Paste SAE narrative text here...",
    key="sae_text"
)
st.caption(f"Characters: {len(text)}/12000")

if st.button("Run SAE narrative review"):
    if not text.strip():
        st.warning("Please paste SAE narrative text before running the review.")
    elif len(text) > 12000:
        st.error("Public demo limit reached: this text exceeds 12,000 characters. For larger reviews or supported workflows, contact us for pricing.")
        st.session_state.sae_done = False
    else:
        findings, table_rows = detect_sae_findings(text)
        report_text = build_report(text, findings, table_rows)
        st.session_state.sae_last_text = text
        st.session_state.sae_last_findings = findings
        st.session_state.sae_last_table_rows = table_rows
        st.session_state.sae_last_report = report_text
        st.session_state.sae_done = True
        st.session_state.sae_ai_summary = ""
        st.session_state.sae_quality_review_open = False
        st.rerun()

st.divider()

if not st.session_state.sae_done and not text.strip():
    st.info("Start by loading the sample text or pasting SAE narrative text to evaluate.")

if st.session_state.sae_done:
    last_text = st.session_state.sae_last_text
    findings = st.session_state.sae_last_findings
    table_rows = st.session_state.sae_last_table_rows
    report_text = st.session_state.sae_last_report

    st.success("SAE narrative review complete.")
    st.info("This output is generated by a limited deterministic SAE narrative completeness engine. It does not determine MedWatch/EudraVigilance submission readiness, medical causality, or final reporting adequacy. Human review is required.")
    st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no final safety-reporting or submission-readiness determination.")

    st.download_button(
        label="Download text report",
        data=report_text,
        file_name="sae_narrative_scorer_report.txt",
        mime="text/plain"
    )

    st.subheader("Findings")
    if findings:
        for finding in findings:
            render_finding(finding)
            st.divider()
    else:
        st.info("No SAE narrative findings were triggered by the current v1 rule set.")

    st.subheader("SAE completeness table")
    if table_rows:
        st.dataframe(table_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No SAE completeness rows available from the current v1 rule set.")

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
        st.session_state.sae_quality_review_open = True
        st.rerun()

    if st.session_state.get("sae_quality_review_open"):
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

    with st.expander("Preview pasted SAE narrative text"):
        st.write(last_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
st.markdown("[Having issues? drop us an email](mailto:hello@lippershey.co)")
