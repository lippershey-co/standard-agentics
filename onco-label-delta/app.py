import streamlit as st
from difflib import ndiff


SAMPLE_TEXT_A = """INDICATIONS AND USAGE
Drug X is indicated for adult patients with advanced solid tumors.
WARNINGS AND PRECAUTIONS
Monitor liver function during treatment.
"""

SAMPLE_TEXT_B = """INDICATIONS AND USAGE
Drug X is indicated for adult patients with advanced or metastatic solid tumors.
WARNINGS AND PRECAUTIONS
Monitor liver function during treatment.
ADVERSE REACTIONS
The most common adverse reactions were fatigue and nausea.
"""


def normalize_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        cleaned = " ".join(line.strip().split())
        if cleaned:
            lines.append(cleaned)
    return lines


def compare_lines(text_a: str, text_b: str):
    lines_a = normalize_lines(text_a)
    lines_b = normalize_lines(text_b)

    diff = list(ndiff(lines_a, lines_b))
    added = [line[2:] for line in diff if line.startswith("+ ")]
    removed = [line[2:] for line in diff if line.startswith("- ")]

    return lines_a, lines_b, added, removed


def render_lines(lines: list[str]):
    if not lines:
        st.info("No lines to display.")
    else:
        for line in lines:
            st.markdown(f"- {line}")


def build_report(lines_a, lines_b, added, removed) -> str:
    report = []
    report.append("ONCO-LABEL-DELTA REPORT")
    report.append("")
    report.append("This output is a line-level text comparison only.")
    report.append("It does not determine regulatory significance.")
    report.append("Human review is required.")
    report.append("PDF support is not included in this public demo.")
    report.append("")
    report.append("COMPARISON SUMMARY")
    report.append(f"Lines in Text A: {len(lines_a)}")
    report.append(f"Lines in Text B: {len(lines_b)}")
    report.append(f"New lines: {len(added)}")
    report.append(f"Removed lines: {len(removed)}")
    report.append("")
    report.append("NEW CONTENT DETECTED")
    if added:
        for item in added:
            report.append(f"- {item}")
    else:
        report.append("No new content detected.")
    report.append("")
    report.append("REMOVED CONTENT DETECTED")
    if removed:
        for item in removed:
            report.append(f"- {item}")
    else:
        report.append("No removed content detected.")
    report.append("")
    return "\n".join(report)


st.set_page_config(page_title="Onco-Label-Delta", layout="wide")

if "text_a" not in st.session_state:
    st.session_state.text_a = ""
if "text_b" not in st.session_state:
    st.session_state.text_b = ""

st.title("Onco-Label-Delta")
st.caption("Compare two oncology label texts and surface meaningful line-level changes.")

with st.expander("How to use", expanded=True):
    st.markdown("""
1. Paste an earlier label version into **Label Text A**
2. Paste a newer label version into **Label Text B**
3. Click **Run comparison**
4. Review new and removed content
    """)

with st.expander("Public demo policy", expanded=False):
    st.markdown("""
- Testing only
- English only
- Paste text only in v1
- Maximum 12,000 characters per text
- No confidential, patient, or business-sensitive data
- Human review required
    """)

top_col1, top_col2, top_col3 = st.columns([1, 1, 3])

with top_col1:
    if st.button("Load sample comparison"):
        st.session_state.text_a = SAMPLE_TEXT_A
        st.session_state.text_b = SAMPLE_TEXT_B
        st.rerun()

with top_col2:
    if st.button("Reset"):
        st.session_state.text_a = ""
        st.session_state.text_b = ""
        st.rerun()

with top_col3:
    st.caption("Use the sample texts for a quick demo, or reset both fields.")

col1, col2 = st.columns(2)

with col1:
    text_a = st.text_area(
        "Label Text A",
        height=300,
        placeholder="Paste the first label version here...",
        key="text_a"
    )
    st.caption(f"Characters: {len(text_a)}/12000")

with col2:
    text_b = st.text_area(
        "Label Text B",
        height=300,
        placeholder="Paste the second label version here...",
        key="text_b"
    )
    st.caption(f"Characters: {len(text_b)}/12000")

compare_clicked = st.button("Run comparison")

st.divider()

if not compare_clicked and not text_a.strip() and not text_b.strip():
    st.info("Start by loading the sample texts or pasting two label versions to compare.")

if compare_clicked:
    if not text_a.strip() or not text_b.strip():
        st.warning("Please paste both label texts before comparing.")
    elif len(text_a) > 12000 or len(text_b) > 12000:
        st.error("One or both text inputs exceed the 12,000 character limit.")
    else:
        lines_a, lines_b, added, removed = compare_lines(text_a, text_b)
        report_text = build_report(lines_a, lines_b, added, removed)

        st.success("Comparison complete.")
        st.info("This output is a line-level text comparison only. It does not determine regulatory significance. Human review is required.")
        st.caption("Scope limits: text-only demo, no PDF support in v1, no assessment of regulatory materiality.")

        st.download_button(
            label="Download text report",
            data=report_text,
            file_name="onco_label_delta_report.txt",
            mime="text/plain"
        )

        st.subheader("Comparison summary")
        metric1, metric2, metric3, metric4 = st.columns(4)
        metric1.metric("Lines in Text A", len(lines_a))
        metric2.metric("Lines in Text B", len(lines_b))
        metric3.metric("New lines", len(added))
        metric4.metric("Removed lines", len(removed))

        st.subheader("New content detected")
        if added:
            render_lines(added)
        else:
            st.info("No new content detected.")

        st.subheader("Removed content detected")
        if removed:
            render_lines(removed)
        else:
            st.info("No removed content detected.")

        with st.expander("Preview normalized Text A"):
            render_lines(lines_a)

        with st.expander("Preview normalized Text B"):
            render_lines(lines_b)

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
