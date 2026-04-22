import streamlit as st

st.set_page_config(page_title="Trial-Eligibility-Watchdog", layout="wide")

st.title("Trial-Eligibility-Watchdog")
st.caption("Track and review clinical trial eligibility criteria changes.")

with st.expander("How to use", expanded=True):
    st.markdown("""
1. Enter a ClinicalTrials.gov **NCT ID** or paste eligibility criteria text
2. Click **Run check**
3. Review the output
    """)

with st.expander("Public demo policy", expanded=False):
    st.markdown("""
- Testing only
- English only
- No PDF support in v1
- One NCT ID or one pasted text block only
- No confidential, patient, or business-sensitive data
- Human review required
    """)

mode = st.radio(
    "Choose input type",
    ["NCT ID", "Pasted eligibility text"],
    horizontal=True
)

if mode == "NCT ID":
    nct_id = st.text_input(
        "ClinicalTrials.gov NCT ID",
        placeholder="Example: NCT01234567"
    )
    pasted_text = ""
else:
    pasted_text = st.text_area(
        "Eligibility criteria text",
        height=300,
        placeholder="Paste eligibility criteria here..."
    )
    st.caption(f"Characters: {len(pasted_text)}/12000")
    nct_id = ""

run_clicked = st.button("Run check")

st.divider()

if not run_clicked and not nct_id.strip() and not pasted_text.strip():
    st.info("Start by entering an NCT ID or pasting eligibility criteria text.")

if run_clicked:
    if mode == "NCT ID" and not nct_id.strip():
        st.warning("Please enter an NCT ID before running the check.")
    elif mode == "Pasted eligibility text" and not pasted_text.strip():
        st.warning("Please paste eligibility criteria text before running the check.")
    elif len(pasted_text) > 12000:
        st.error("The pasted text exceeds the 12,000 character limit.")
    else:
        st.success("Input accepted. Trial-Eligibility-Watchdog engine coming next.")
        st.info("This public demo does not yet fetch or compare live ClinicalTrials.gov records. Human review is required.")

        st.subheader("Input preview")
        if mode == "NCT ID":
            st.write(f"NCT ID submitted: {nct_id}")
        else:
            st.write(f"Eligibility text length: {len(pasted_text)} characters")
            with st.expander("Preview pasted eligibility text"):
                st.write(pasted_text[:1000])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
