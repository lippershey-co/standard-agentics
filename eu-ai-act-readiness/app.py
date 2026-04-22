import streamlit as st

SAMPLE_USE_CASE = """We use an AI system to screen oncology trial candidates based on structured patient data and clinical notes.
The system ranks likely eligible patients for manual review by the study team.
Outputs are reviewed by humans before any enrollment decision is made.
"""


st.set_page_config(page_title="EU-AI-Act-Readiness", layout="wide")

if "eu_ai_text" not in st.session_state:
    st.session_state.eu_ai_text = ""

st.title("EU-AI-Act-Readiness")
st.caption("Assess an AI use case against a limited public-demo readiness workflow.")

with st.expander("How to use", expanded=True):
    st.markdown("""
1. Paste an AI use-case description into the input box
2. Click **Run readiness check**
3. Review the output
    """)

with st.expander("Public demo policy", expanded=False):
    st.markdown("""
- Testing only
- English only
- Paste text only in this first demo step
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
        st.success("Input accepted. EU-AI-Act-Readiness engine coming next.")
        st.info("This public demo does not yet perform a real readiness assessment. Human review is required.")
        st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no legal determination.")

        st.subheader("Input preview")
        st.write(f"Use-case description length: {len(use_case_text)} characters")

        with st.expander("Preview pasted use-case description"):
            st.write(use_case_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
