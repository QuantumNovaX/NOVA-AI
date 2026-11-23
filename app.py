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
/* NOVA-AI — clean, understated, premium interface */
:root {
    color-scheme: light;
}
.stApp {
    background: #f5f7fa;
    color: #172033;
}
[data-testid="stHeader"] {
    background: rgba(245, 247, 250, 0.92);
}
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e5e9f0;
}
[data-testid="stSidebar"] * {
    color: #263247;
}
h1, h2, h3, p, label, [data-testid="stMarkdownContainer"] {
    color: #172033;
}
.nova-title {
    text-align: center;
    font-size: clamp(36px, 5vw, 50px);
    font-weight: 750;
    letter-spacing: -1.8px;
    color: #14243a;
    margin-top: 0.25rem;
}
.subtitle {
    text-align: center;
    color: #68778d;
    letter-spacing: 2.4px;
    font-size: 11px;
    font-weight: 650;
}
div.stButton > button {
    background: #183b56;
    color: #ffffff;
    border: 1px solid #183b56;
    border-radius: 10px;
    min-height: 42px;
    font-weight: 600;
    transition: background 150ms ease, border-color 150ms ease;
}
div.stButton > button:hover {
    background: #245675;
    border-color: #245675;
    color: #ffffff;
}
div[data-testid="stChatMessage"] {
    background: #ffffff;
    border: 1px solid #e6ebf1;
    border-radius: 14px;
    padding: 0.85rem 1rem;
    box-shadow: 0 2px 10px rgba(24, 43, 67, 0.035);
}
[data-testid="stChatInput"] {
    background: #ffffff;
    border: 1px solid #dce3ec;
    border-radius: 12px;
}
[data-testid="stFileUploader"] {
    background: #ffffff;
    border: 1px dashed #cbd5e1;
    border-radius: 12px;
    padding: 0.5rem;
}
hr {
    border-color: #e6ebf1;
}
small, [data-testid="stCaptionContainer"] {
    color: #718096 !important;
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

