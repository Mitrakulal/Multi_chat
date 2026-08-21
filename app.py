from __future__ import annotations

import streamlit as st

from app.rag import HotelRAG

st.set_page_config(page_title="Hotel Deepa Comforts Assistant", page_icon="🏨", layout="wide")

st.markdown("""
<style>
:root { --deepa-red: #a62d3c; --deepa-gold: #c89b55; --deepa-cream: #fff8ef; }
.stApp { background: linear-gradient(135deg, #fffaf3 0%, #f8eee2 100%); }
.hero { padding: 2rem 2.25rem; border-radius: 18px; background: linear-gradient(120deg, #701e2c, #b74a4a); color: white; margin-bottom: 1.5rem; box-shadow: 0 12px 35px rgba(112,30,44,.18); }
.hero h1 { margin: 0; font-family: Georgia, serif; letter-spacing: .02em; }
.hero p { margin: .5rem 0 0; font-size: 1.05rem; }
.warning { border-left: 5px solid #b71c1c; background: #fff0ef; padding: 1rem 1.1rem; border-radius: 8px; color: #5d1818; }
.source-card { padding: .75rem 1rem; border: 1px solid #ead7bc; border-radius: 10px; background: rgba(255,255,255,.65); margin-bottom: .5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>Hotel Deepa Comforts</h1>
  <p>Official guest information assistant · M.G. Road, Mangalore</p>
</div>
<div class="warning"><strong>Booking safety:</strong> The official website warns about fraudulent booking activity. For reservations, use official channels and call <strong>0824-2497101</strong>. Do not send payment to an unverified number.</div>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="Loading the hotel knowledge base and embedding model…")
def load_rag() -> HotelRAG:
    return HotelRAG()

try:
    rag = load_rag()
except Exception as exc:
    st.error("The embedding model could not be loaded. Run `pip install -r requirements.txt` and try again.")
    st.exception(exc)
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("Ask about the hotel")
    st.caption("Answers are grounded in the official Hotel Deepa Comforts website corpus bundled with this project.")
    st.markdown("**Try these questions**")
    examples = [
        "What rooms do you have?",
        "How do I book a banquet hall?",
        "What is the restaurant timing?",
        "How do I reach the hotel from the airport?",
        "Is this phone number official?",
    ]
    for example in examples:
        if st.button(example, use_container_width=True):
            st.session_state.pending_question = example
    st.divider()
    st.markdown("**Official contacts**")
    st.write("0824-2497101 (reservations)")
    st.write("0824 411 7101 / 02 / 03")
    st.write("info@hoteldeepacomforts.com")
    st.write("M.G. Road, Mangalore - 575 003")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources used"):
                for source in message["sources"]:
                    st.markdown(f"**{source['title']}** · similarity {source['score']}  \\\n[{source['url']}]({source['url']})")

question = st.chat_input("Ask about rooms, Chutney, banquets, travel desk, amenities, or booking safety…")
question = question or st.session_state.pop("pending_question", None)
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Checking the official hotel information…"):
            result = rag.ask(question)
        st.markdown(result["answer"])
        with st.expander("Sources used"):
            for source in result["sources"]:
                st.markdown(f"**{source['title']}** · similarity {source['score']}  \\\n[{source['url']}]({source['url']})")
    st.session_state.messages.append({"role": "assistant", "content": result["answer"], "sources": result["sources"]})
