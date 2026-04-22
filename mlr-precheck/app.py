import streamlit as st

st.set_page_config(page_title="MLR-PreCheck", layout="wide")

st.title("MLR-PreCheck")
st.caption("Review promotional text for possible medical, legal, and regulatory risk signals.")

with st.expander("How to use", expanded=True):
    st.markdown("""
1. Paste promotional text into the input box
2. Click **Run pre-check**
3. Review the output
    """)

with st.expander("Public demo policy", expanded=False):
    st.markdown("""
- Testing only
- English only
- Paste text only in v1
- No PDF or DOCX support in this first demo step
- Maximum 12,000 characters
- No confidential, patient, or business-sensitive data
- Human review required
    """)

promo_text = st.text_area(
    "Promotional text",
    height=320,
    placeholder="Paste promotional copy here..."
)
st.caption(f"Characters: {len(promo_text)}/12000")

run_clicked = st.button("Run pre-check")

st.divider()

if not run_clicked and not promo_text.strip():
    st.info("Start by pasting promotional text to evaluate.")

if run_clicked:
    if not promo_text.strip():
        st.warning("Please paste promotional text before running the pre-check.")
    elif len(promo_text) > 12000:
        st.error("The pasted text exceeds the 12,000 character limit.")
    else:
        st.success("Input accepted. MLR-PreCheck engine coming next.")
        st.info("This public demo does not yet perform a real MLR review. Human review is required.")
        st.caption("Scope limits: text-only demo, no PDF or DOCX support in this step, no determination of compliance.")

        st.subheader("Input preview")
        st.write(f"Promotional text length: {len(promo_text)} characters")

        with st.expander("Preview pasted promotional text"):
            st.write(promo_text[:1200])

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
st.markdown("[Open the Standard Agentics repository](https://github.com/lippershey-co/standard-agentics)")
