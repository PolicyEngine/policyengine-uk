import streamlit as st

STYLE = """
<style>
header {
    display: none !important;
}
footer {
    display: none !important;
}
section > div.block-container {
    padding-top: 0px !important;
    padding-bottom: 0px !important;
}
html, body, [class*="css"] {
  font-family: "Roboto Serif", !important;
  font-weight: 500;
}
[data-baseweb="slider"] {
    padding-left: 10px !important;
}
#MainMenu {
    visibility: hidden;
}
footer {
    visibility: hidden;
}
.modebar{
      display: none !important;
}
</style>
"""
st.write(STYLE, unsafe_allow_html=True)

st.title("PolicyEngine UK documentation")

st.markdown(
    """
    This is the documentation for PolicyEngine UK, an open-source microsimulation model of the UK tax and benefit system.
    """
)
