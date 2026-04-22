import streamlit as st
from difflib import ndiff


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


st.set_page_config(page_title="Onco-Label-Delta", layout="wide")

st.title("Onco-Label-Delta")
st.caption("Compare two oncology label texts and highlight meaningful changes.")

with st.expander("Public demo policy", expanded=False):
    st.markdown("""
- Testing only
- English only
- Paste text only in v1
- Maximum 12,000 characters per text
- No confidential, patient, or business-sensitive data
- Human review required
    """)

col1, col2 = st.columns(2)

with col1:
    text_a = st.text_area(
        "Label Text A",
        height=300,
        placeholder="Paste the first label version here..."
    )
    st.caption(f"Characters: {len(text_a)}/12000")

with col2:
    text_b = st.text_area(
        "Label Text B",
        height=300,
        placeholder="Paste the second label version here..."
    )
    st.caption(f"Characters: {len(text_b)}/12000")

compare_clicked = st.button("Compare label versions")

st.divider()

if compare_clicked:
    if not text_a.strip() or not text_b.strip():
        st.warning("Please paste both label texts before comparing.")
    elif len(text_a) > 12000 or len(text_b) > 12000:
        st.error("One or both text inputs exceed the 12,000 character limit.")
    else:
        lines_a, lines_b, added, removed = compare_lines(text_a, text_b)

        st.success("Comparison complete.")

        metric1, metric2, metric3, metric4 = st.columns(4)
        metric1.metric("Lines in Text A", len(lines_a))
        metric2.metric("Lines in Text B", len(lines_b))
        metric3.metric("Added lines", len(added))
        metric4.metric("Removed lines", len(removed))

        st.subheader("Added lines")
        if added:
            for item in added:
                st.markdown(f"- {item}")
        else:
            st.info("No added lines detected.")

        st.subheader("Removed lines")
        if removed:
            for item in removed:
                st.markdown(f"- {item}")
        else:
            st.info("No removed lines detected.")

        with st.expander("Preview normalized Text A"):
            st.write(lines_a)

        with st.expander("Preview normalized Text B"):
            st.write(lines_b)

st.divider()
st.markdown("**Run locally via GitHub**")
st.markdown("For private or extended use, run the tool locally from the Standard Agentics repository.")
