import json
import streamlit as st
from app.rag import HotelRAG, CONFIG

st.set_page_config(
    page_title=f"{CONFIG['name']} Assistant",
    page_icon="🏨",
    layout="wide",
)

primary, accent = CONFIG["colors"]

st.markdown(
    f"""<style>
.stApp {{ background: #101820; }}
.hotel-bg {{ position: fixed; inset: 0; z-index: 0; background: linear-gradient(135deg, {primary} 0%, #0d1720 65%, {accent} 180%); }}
.hotel-bg iframe {{ width:100%; height:100%; border:0; opacity:.24; }}
.block-container {{ position:relative; z-index:1; max-width: 1180px; padding-top: 2rem; }}
.hero {{ background: linear-gradient(110deg, {primary}f2, {accent}dc); color:white; padding:1.8rem 2rem; border-radius:20px; box-shadow:0 14px 40px #0008; }}
.hero h1 {{ margin:0; font-family:Georgia,serif; }}
.hero p {{ margin:.5rem 0 0; }}
.chat-shell {{ background:#fffffff0; border-radius:18px; padding:1rem; box-shadow:0 15px 50px #0007; }}
.notice {{ border-left:5px solid {accent}; background:#fff8e9; padding:.85rem 1rem; border-radius:8px; color:#362a18; }}
</style>""",
    unsafe_allow_html=True,
)

if CONFIG.get("url"):
    st.markdown(
        f"<div class='hotel-bg'><iframe src='{CONFIG['url']}' title='{CONFIG['name']} website preview'></iframe></div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown("<div class='hotel-bg'></div>", unsafe_allow_html=True)

st.markdown(
    f"<div class='hero'><h1>{CONFIG['name']}</h1><p>{CONFIG['tagline']}</p></div>",
    unsafe_allow_html=True,
)

if CONFIG.get("verification_needed"):
    st.markdown(
        "<div class='notice'><strong>Verification-needed demo:</strong> This folder uses lead-report context only where no verified official website was supplied. Replace the URL and refresh the knowledge base before production or outreach.</div>",
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner="Loading the approved hotel knowledge base…")
def load_rag():
    return HotelRAG()


try:
    rag = load_rag()
except Exception as exc:
    st.error("Install requirements and ensure the embedding model is available.")
    st.exception(exc)
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("Ask about the hotel")
    st.caption("Answers are grounded in the bundled approved content pack. Rates, availability and payments require staff confirmation.")
    for q in CONFIG.get(
        "examples",
        [
            "What rooms or stays are available?",
            "What dining or event facilities are listed?",
            "How do I contact reservations?",
        ],
    ):
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q
    st.divider()
    st.markdown("**Website / source**")
    st.write(CONFIG.get("url") or "No verified official URL supplied")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("sources"):
            with st.expander("Sources used"):
                for s in m["sources"]:
                    st.markdown(f"**{s['title']}** · [{s['url']}]({s['url']})")

q = st.chat_input("Ask about rooms, dining, amenities, events, directions or policies…") or st.session_state.pop("pending_question", None)
if q:
    st.session_state.messages.append({"role": "user", "content": q})
    st.chat_message("user").markdown(q)
    with st.chat_message("assistant"):
        with st.spinner("Checking approved hotel information…"):
            result = rag.ask(q)
        st.markdown(result["answer"])
        with st.expander("Sources used"):
            for s in result["sources"]:
                st.markdown(f"**{s['title']}** · [{s['url']}]({s['url']})")
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
        }
    )
