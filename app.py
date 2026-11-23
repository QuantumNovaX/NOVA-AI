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
/* NOVA-AI — soft neutral theme with strong text contrast */
:root {
    color-scheme: light;
}
.stApp {
    background: #eef1f5;
    color: #182230;
}
[data-testid="stHeader"] {
    background: rgba(238, 241, 245, 0.96);
}
[data-testid="stSidebar"] {
    background: #e5eaf0;
    border-right: 1px solid #cbd3dd;
}
[data-testid="stSidebar"] * {
    color: #182230 !important;
}
.stApp, .stApp p, .stApp label, .stApp span,
.stApp li, .stApp [data-testid="stMarkdownContainer"] {
    color: #182230;
}
h1, h2, h3, h4 {
    color: #142235 !important;
}
.nova-title {
    text-align: center;
    font-size: clamp(36px, 5vw, 50px);
    font-weight: 750;
    letter-spacing: -1.5px;
    color: #142235 !important;
    margin-top: 0.25rem;
}
.subtitle {
    text-align: center;
    color: #526174 !important;
    letter-spacing: 2px;
    font-size: 11px;
    font-weight: 650;
}
div.stButton > button {
    background: #24445f;
    color: #ffffff !important;
    border: 1px solid #24445f;
    border-radius: 10px;
    min-height: 42px;
    font-weight: 600;
}
div.stButton > button:hover {
    background: #315c7d;
    border-color: #315c7d;
}
div[data-testid="stChatMessage"] {
    background: #f9fafb;
    border: 1px solid #d6dde6;
    border-radius: 14px;
    padding: 0.85rem 1rem;
}
div[data-testid="stChatMessage"] * {
    color: #182230 !important;
}
[data-testid="stChatInput"] {
    background: #ffffff;
    border: 1px solid #cbd3dd;
    border-radius: 12px;
}
[data-testid="stChatInput"] textarea {
    color: #182230 !important;
    -webkit-text-fill-color: #182230 !important;
}
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] div,
[data-testid="stFileUploader"] {
    color: #182230 !important;
}
[data-testid="stTextInput"] input,
[data-testid="stTextInput"] input::placeholder,
[data-testid="stChatInput"] textarea::placeholder {
    color: #526174 !important;
    -webkit-text-fill-color: #526174 !important;
    opacity: 1;
}
[data-testid="stFileUploader"] {
    background: #f9fafb;
    border: 1px dashed #aeb9c7;
    border-radius: 12px;
}
hr {
    border-color: #cbd3dd;
}
[data-testid="stCaptionContainer"] {
    color: #526174 !important;
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

# ---------- AI IMAGE UNDERSTANDING ----------
with st.expander("🖼️ NOVA AI Image Understanding", expanded=True):
    uploaded_image = st.file_uploader(
        "Upload a picture for NOVA to understand",
        type=["png", "jpg", "jpeg", "webp"],
        key="nova_image"
    )

    if uploaded_image:
        st.image(uploaded_image, caption="Uploaded image")

        image_question = st.text_input(
            "What would you like NOVA to know about this image?",
            placeholder="Describe this picture..."
        )

        if st.button("✨ Ask NOVA about this image"):
            try:
                image_bytes = uploaded_image.getvalue()
                base64_image = base64.b64encode(
                    image_bytes
                ).decode("utf-8")

                mime_type = uploaded_image.type or "image/jpeg"

                with st.spinner("NOVA is analyzing your image..."):
                    response = client.chat.completions.create(
                        model="qwen/qwen3.8-27b",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": image_question.strip()
                                        or "Describe this image in detail."
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": (
                                                f"data:{mime_type};base64,"
                                                f"{base64_image}"
                                            )
                                        }
                                    }
                                ]
                            }
                        ],
                        max_completion_tokens=1024
                    )

                image_answer = response.choices[0].message.content
                st.markdown("### ✨ NOVA's Image Analysis")
                st.write(image_answer)

            except Exception as error:
                st.error("Image analysis failed: " + str(error))

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

