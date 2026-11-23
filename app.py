import os
import json
import base64
import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="NOVA-AI",
    page_icon="🌌",
    layout="wide"
)

# ---------- PREMIUM DESIGN ----------
st.markdown("""
<style>
/* NOVA-AI — clean black theme, crisp white typography */
.stApp {
    background: #050607;
    color: #f5f7fa;
}
[data-testid="stHeader"] {
    background: rgba(5, 6, 7, 0.96);
}
[data-testid="stSidebar"] {
    background: #0b0d10;
    border-right: 1px solid #252a31;
}
[data-testid="stSidebar"] * {
    color: #f1f3f5 !important;
}
.stApp p, .stApp label, .stApp li,
.stApp [data-testid="stMarkdownContainer"] {
    color: #f1f3f5;
}
h1, h2, h3, h4 {
    color: #ffffff !important;
}
/* Keep the existing NOVA-AI logo/title styling untouched. */
.nova-title {
    text-align: center;
    font-size: 52px;
    font-weight: 900;
    background: linear-gradient(90deg,#a879ff,#48c9ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.subtitle {
    text-align: center;
    color: #b8c0cc !important;
    letter-spacing: 2px;
}
div.stButton > button {
    background: #171b21;
    color: #ffffff !important;
    border: 1px solid #343b46;
    border-radius: 10px;
    width: 100%;
    font-weight: 600;
}
div.stButton > button:hover {
    background: #252c35;
    border-color: #657184;
    color: #ffffff !important;
}
div[data-testid="stChatMessage"] {
    background: #101317;
    border: 1px solid #272d36;
    border-radius: 14px;
}
div[data-testid="stChatMessage"] * {
    color: #f1f3f5 !important;
}
[data-testid="stChatInput"] {
    background: #101317;
    border: 1px solid #343b46;
    border-radius: 12px;
}
[data-testid="stChatInput"] textarea {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] div {
    color: #ffffff !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stChatInput"] textarea::placeholder {
    color: #aab3bf !important;
    -webkit-text-fill-color: #aab3bf !important;
    opacity: 1;
}
[data-testid="stFileUploader"] {
    background: #101317;
    border: 1px dashed #414a57;
    border-radius: 12px;
}
hr {
    border-color: #292f38;
}
[data-testid="stCaptionContainer"] {
    color: #aab3bf !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- API CONNECTION ----------
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    try: 
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        st.error("GROQ_API_KEY is missing. Configure your existing secret.")
        st.stop()

client = Groq(api_key=api_key)

MODEL = "openai/gpt-oss-120b"

# ---------- SESSION DATA ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    st.session_state.memory = []

if "language" not in st.session_state:
    st.session_state.language = "English"

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("## ✦ NOVA-AI")
    st.caption("YOUR PERSONAL AI ASSISTANT")
    st.divider()

    st.markdown("### 🌐 Language")
    st.session_state.language = st.selectbox(
        "Choose your reply language",
        [
            "English", "தமிழ் (Tamil)", "Hindi",
            "French", "Spanish", "German",
            "Japanese", "Arabic", "Telugu",
            "Malayalam"
        ],
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown("### 🧠 Personal Memory")

    memory_text = st.text_input(
        "Save something NOVA should remember",
        placeholder="Example: I like short answers"
    )

    if st.button("＋ Save Memory"):
        if memory_text.strip():
            st.session_state.memory.append(memory_text.strip())
            st.success("Memory saved!")

    for item in st.session_state.memory:
        st.caption("• " + item)

    if st.button("Clear Memory"):
        st.session_state.memory = []
        st.rerun()

    st.divider()
    st.markdown("### 📚 Chat History")

    if st.button("＋ New Chat"):
        st.session_state.messages = []
        st.rerun()

    st.caption(f"{len(st.session_state.messages)} messages in this session")

    st.divider()
    st.markdown("💎 **NOVA PREMIUM DESIGN**")
    st.caption("Smarter. Kinder. Always here.")

# ---------- MAIN SCREEN ----------
st.markdown(
    '<div class="nova-title">✦ NOVA-AI ✦</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">YOUR SMART PERSONAL AI ASSISTANT</div>',
    unsafe_allow_html=True
)

st.write("")
st.markdown(
    "<h2 style='text-align:center'>Welcome to NOVA ✨</h2>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align:center;color:#bba9ed'>"
    "What would you like to explore today?</p>",
    unsafe_allow_html=True
)

# ---------- QUICK PROMPTS ----------
st.markdown("### ✨ Explore NOVA")

col1, col2, col3 = st.columns(3)

if col1.button("💡 Explain something"):
    st.session_state.quick_prompt = "Explain an interesting topic to me."

if col2.button("✍️ Help me write"):
    st.session_state.quick_prompt = "Help me write something."

if col3.button("💻 Coding help"):
    st.session_state.quick_prompt = "Help me with a coding problem."

# ---------- CHAT DISPLAY ----------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------- CHAT INPUT ----------
prompt = st.chat_input("✨ Message NOVA-AI...")

if "quick_prompt" in st.session_state:
    prompt = st.session_state.pop("quick_prompt")

if prompt:
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    language = st.session_state.language

    memory_notes = "\n".join(
        "- " + item for item in st.session_state.memory
    )

    system_prompt = f"""
You are NOVA-AI, a helpful, friendly and capable AI assistant.
You were created by QuantumNovax.

Reply in this selected language:
{language}

If Tamil is selected, reply in natural Tamil.
If English is selected, reply in English.
Follow the user's language preference.

Use these user-approved memory notes when helpful:
{memory_notes}

Be accurate and honest. Never claim to have performed
an action you cannot perform.
"""

    api_messages = [
        {"role": "system", "content": system_prompt}
    ] + st.session_state.messages[-30:]

    with st.chat_message("assistant"):
        with st.spinner("NOVA is thinking... ✨"):
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=api_messages
                )

                answer = response.choices[0].message.content
                st.markdown(answer)

                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )

            except Exception as error:
                st.error("NOVA connection error: " + str(error))

