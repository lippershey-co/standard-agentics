import os
import re
from io import BytesIO
from datetime import datetime
import streamlit as st
import anthropic
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

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


def extract_timeline_lines(lines: list[str]) -> list[str]:
    timeline_terms = [
        "within", "days", "day", "weeks", "week", "screening period",
        "prior to day 1", "prior to", "first dose", "major surgery",
        "radiotherapy", "biopsy", "site"
    ]
    return [line for line in lines if any(term in line.lower() for term in timeline_terms)]


def detect_possible_timeline_conflict(lines: list[str]):
    lower_lines = [line.lower() for line in lines]

    biopsy_requirement_line = next(
        (lines[i] for i, line in enumerate(lower_lines)
         if "biopsy" in line and ("within" in line or "screening period" in line or "prior to day 1" in line)),
        None
    )

    biopsy_exclusion_line = next(
        (lines[i] for i, line in enumerate(lower_lines)
         if ("biopsy site" in line or "active tumor biopsy site" in line)
         and ("within" in line or "days" in line or "day" in line)),
        None
    )

    surgery_or_radiotherapy_line = next(
        (lines[i] for i, line in enumerate(lower_lines)
         if ("major surgery" in line or "radiotherapy" in line)
         and ("within" in line or "weeks" in line or "days" in line)),
        None
    )

    if biopsy_requirement_line and biopsy_exclusion_line:
        return biopsy_requirement_line, biopsy_exclusion_line

    if biopsy_requirement_line and surgery_or_radiotherapy_line:
        return biopsy_requirement_line, surgery_or_radiotherapy_line

    return None, None


def find_snippet(text: str, keyword: str, max_len: int = 260) -> str:
    if not text or not keyword:
        return ""

    lower_text = text.lower()
    lower_keyword = keyword.lower()
    idx = lower_text.find(lower_keyword)
    if idx == -1:
        return ""

    # Prefer full line first
    line_start = text.rfind("\n", 0, idx)
    line_end = text.find("\n", idx)

    line_start = 0 if line_start == -1 else line_start + 1
    line_end = len(text) if line_end == -1 else line_end

    snippet = text[line_start:line_end].strip()

    # If line is too short, expand to nearby sentence-ish boundaries
    if len(snippet) < 50:
        left_candidates = [
            text.rfind(". ", 0, idx),
            text.rfind("? ", 0, idx),
            text.rfind("! ", 0, idx),
            text.rfind("\n\n", 0, idx),
            text.rfind("\n", 0, idx),
        ]
        left = max(left_candidates)
        left = 0 if left == -1 else left + 1

        right_candidates = [
            text.find(". ", idx),
            text.find("? ", idx),
            text.find("! ", idx),
            text.find("\n\n", idx),
            text.find("\n", idx),
        ]
        right_candidates = [x for x in right_candidates if x != -1]
        right = min(right_candidates) if right_candidates else len(text)

        snippet = text[left:right].strip()

    # Controlled fallback
    if len(snippet) < 25:
        window_left = max(0, idx - 80)
        window_right = min(len(text), idx + 180)
        snippet = text[window_left:window_right].strip()

    # Clean formatting noise
    snippet = snippet.replace("**", "")
    snippet = snippet.replace("__", "")
    snippet = snippet.replace("```", "")
    snippet = " ".join(snippet.split())

    # Trim leading bullets / markers cleanly
    while snippet.startswith(("-", "*", ">", "#", ":")):
        snippet = snippet[1:].lstrip()

    # If still too long, trim neatly
    if len(snippet) > max_len:
        snippet = snippet[:max_len].rsplit(" ", 1)[0] + "..."

    return snippet


def detect_population_accessibility_risk(text: str):
    lower_text = text.lower()

    nsclc_context = (
        "nsclc" in lower_text
        or "non-small cell lung cancer" in lower_text
        or "non small cell lung cancer" in lower_text
    )

    metastatic_context = "metastatic" in lower_text or "stage iv" in lower_text

    multi_line_requirement = (
        "at least 2 prior lines" in lower_text
        or "2 prior lines" in lower_text
        or "two prior lines" in lower_text
        or "received at least 2 prior lines" in lower_text
    )

    excludes_checkpoint = (
        "pd-1" in lower_text
        or "pd-l1" in lower_text
        or "checkpoint inhibitor" in lower_text
        or "checkpoint inhibitors" in lower_text
    )

    if nsclc_context and metastatic_context and multi_line_requirement and excludes_checkpoint:
        return True

    return False


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
        preferred_term = None
        for candidate in ["must", "ecog", "prior", "brain metastases", "cardiovascular"]:
            if candidate in matched_terms:
                preferred_term = candidate
                break
        if not preferred_term:
            preferred_term = matched_terms[0]

        findings.append({
            "title": "Potential eligibility tightening or screening impact terms detected",
            "risk_level": "Medium",
            "why_flagged": "The submitted criteria include terms that often affect screening burden or enrollment eligibility. Matched terms: " + ", ".join(matched_terms[:8]),
            "matched_text": find_snippet(eligibility_text, preferred_term),
            "rule_reference": "Eligibility screening heuristic",
            "review_note": "Human review required."
        })

    if "ecog" in lower_text and ("0-1" in lower_text or "0/1" in lower_text):
        findings.append({
            "title": "Performance status restriction detected",
            "risk_level": "Medium",
            "why_flagged": "A performance status restriction was detected and may materially affect the eligible population.",
            "matched_text": find_snippet(eligibility_text, "ecog"),
            "rule_reference": "Eligibility population narrowing heuristic",
            "review_note": "Human review required."
        })

    if "brain metastases" in lower_text and ("exclude" in lower_text or "exclusion" in lower_text or "untreated" in lower_text):
        findings.append({
            "title": "Potential CNS-related exclusion detected",
            "risk_level": "Medium",
            "why_flagged": "The criteria appear to include a brain metastases-related exclusion, which may significantly affect enrollment.",
            "matched_text": find_snippet(eligibility_text, "brain metastases"),
            "rule_reference": "Eligibility exclusion heuristic",
            "review_note": "Human review required."
        })

    timeline_lines = extract_timeline_lines(lines)
    timeline_line_a, timeline_line_b = detect_possible_timeline_conflict(timeline_lines)

    if timeline_line_a and timeline_line_b:
        findings.append({
            "title": "Potential timeline conflict or logistical deadlock",
            "risk_level": "High",
            "why_flagged": "The submitted criteria contain multiple time-bound procedural requirements or exclusions that may create a narrow or conflicting screening window, potentially reducing enrollment feasibility.",
            "matched_text": timeline_line_a + " | " + timeline_line_b,
            "rule_reference": "Eligibility feasibility / timeline conflict heuristic",
            "review_note": "Human review required."
        })

    if detect_population_accessibility_risk(eligibility_text):
        findings.append({
            "title": "Potential population accessibility risk",
            "risk_level": "High",
            "why_flagged": "The criteria appear to require heavily pretreated metastatic NSCLC patients while excluding therapies commonly used in the current standard-of-care pathway, which may materially reduce the realistically eligible population.",
            "matched_text": find_snippet(eligibility_text, "pd-1") or find_snippet(eligibility_text, "pd-l1") or find_snippet(eligibility_text, "2 prior lines"),
            "rule_reference": "Population accessibility / standard-of-care mismatch heuristic",
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


def generate_ai_summary(trial_id: str, eligibility_text: str, findings: list[dict]) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "AI summary is not available because ANTHROPIC_API_KEY is not set on this runtime."

    findings_text = "\n".join(
        [
            f"- {f['title']} | Risk: {f['risk_level']} | Why: {f['why_flagged']} | Rule: {f['rule_reference']}"
            for f in findings
        ]
    ) or "- No deterministic findings triggered."

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = (
        "You are an assistive reviewer summarizer for clinical trial eligibility criteria. "
        "You must summarize only the deterministic findings provided to you. "
        "Do not invent new findings. "
        "Do not state PASS or FAIL. "
        "Do not state the criteria are approved, feasible, or compliant. "
        "Keep the output concise, practical, and plain-English. "
        "End by stating that human review is required."
    )

    user_prompt = f"""
Trial identifier:
{trial_id or "Not provided"}

Eligibility text:
{eligibility_text}

Deterministic findings:
{findings_text}

Please produce:
1. A short summary of the main review concerns
2. A short section called "Likely reviewer focus"
3. A short section called "Suggested next step"

Do not add findings beyond what is listed above.
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=700,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    parts = []
    for block in message.content:
        block_text = getattr(block, "text", None)
        if block_text:
            parts.append(block_text)

    return "\n".join(parts).strip() or "AI summary returned no text."



def build_transparency_report_text(trial_id: str = "") -> str:
    trial_id = (trial_id or "").strip() or "Not provided"
    report_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "TRANSPARENCY & OVERSIGHT REPORT",
        "",
        f"Generated: {report_date}",
        "",
        "1. SYSTEM IDENTITY",
        "- System: Trial-Eligibility-Watchdog",
        "- Deterministic layer: source of truth for findings in the public demo",
        "- AI layer: optional assistive summary only; it does not replace deterministic findings",
        "",
        "2. STRUCTURED INPUT",
        f"- Trial identifier / NCT ID: {trial_id}",
        "",
        "3. HOW THE SYSTEM WORKS",
        "- The deterministic engine checks eligibility text against a fixed heuristic ruleset.",
        "- The AI layer summarizes deterministic findings in plain language.",
        "- Human review remains required.",
        "",
        "4. CLINICAL LOGIC USED IN THIS DEMO",
        "- Eligibility tightening / screening-impact heuristics",
        "- Performance status restriction detection",
        "- CNS-related exclusion detection",
        "- Timeline conflict / logistical deadlock heuristic",
        "- Population accessibility / standard-of-care mismatch heuristic",
        "",
        "5. HUMAN OVERSIGHT",
        "- This tool is assistive only.",
        "- It does not determine feasibility, protocol approval, or regulatory acceptability.",
        "- A qualified human reviewer must review all output before use.",
        "",
        "6. DATA HANDLING",
        "- Public demo inputs are processed to generate the current output.",
        "- Do not submit patient, personal, or confidential commercial data.",
        "- This report is a transparency artifact, not a declaration of conformity.",
        "",
        "7. PUBLIC DEMO LIMITS",
        "- Paste plain text only",
        "- English only",
        "- Deterministic review up to 12,000 characters",
        "- AI summary limited to smaller public-demo inputs",
        "- No PDF or DOCX support in the public demo",
        "",
        "8. ACCOUNTABILITY",
        "- Final accountability remains with the deploying organization and human reviewer.",
        "",
        "9. SUPPORT",
        "- Having issues? drop us an email: hello@lippershey.co",
        "",
    ]
    return "\n".join(lines)


def build_transparency_report_pdf(trial_id: str = "") -> bytes:
    report_text = build_transparency_report_text(trial_id)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left = 18 * mm
    top = height - 18 * mm
    line_height = 6 * mm
    y = top

    c.setTitle("Trial-Eligibility-Watchdog Transparency & Oversight Report")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left, y, "Trial-Eligibility-Watchdog Transparency & Oversight Report")
    y -= 10 * mm

    c.setFont("Helvetica", 10)

    for raw_line in report_text.splitlines():
        line = raw_line if raw_line.strip() else " "
        wrapped = []
        max_chars = 95

        while len(line) > max_chars:
            split_at = line.rfind(" ", 0, max_chars)
            if split_at == -1:
                split_at = max_chars
            wrapped.append(line[:split_at].rstrip())
            line = line[split_at:].lstrip()
        wrapped.append(line)

        for part in wrapped:
            if y < 18 * mm:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = top
            c.drawString(left, y, part)
            y -= line_height

    c.save()
    buffer.seek(0)
    return buffer.read()


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



with st.expander("Transparency & oversight", expanded=False):
    st.markdown("""
This app can generate a **Transparency & Oversight Report** describing:

- the system identity
- deterministic vs AI summary roles
- human oversight expectations
- public-demo limits
- data-handling cautions
- support contact

This is a transparency artifact for stakeholders.  
It is **not** a declaration of conformity and **not** a legal approval.
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

    transparency_pdf = build_transparency_report_pdf(last_trial_id)

    st.download_button(
        label="Download Transparency & Oversight Report (PDF)",
        data=transparency_pdf,
        file_name="trial_eligibility_watchdog_transparency_report.pdf",
        mime="application/pdf"
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
            with st.spinner("Generating AI summary..."):
                try:
                    st.session_state.tew_ai_summary = generate_ai_summary(last_trial_id, last_text, findings)
                    st.rerun()
                except Exception as e:
                    st.warning(f"AI summary is temporarily unavailable. Deterministic review remains available. Details: {e}")
        else:
            st.caption("AI summary is available for this input under current public-demo limits.")

        if st.session_state.tew_ai_summary:
            st.info(st.session_state.tew_ai_summary)
    else:
        st.warning(ai_message)

    with st.expander("Preview pasted eligibility text"):
        st.write(last_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
st.markdown("[Having issues? drop us an email](mailto:hello@lippershey.co)")
