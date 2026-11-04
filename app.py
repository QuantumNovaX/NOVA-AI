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
.stApp {
    background: radial-gradient(circle at top, #211344, #080814 65%);
    color: #ffffff;
}
[data-testid="stSidebar"] {
    background: #0c0a1b;
    border-right: 1px solid #5735a5;
}
h1, h2, h3, p, label {
    color: white;
}
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
    color: #c3b5e8;
    letter-spacing: 2px;
}
div.stButton > button {
    background: linear-gradient(90deg,#713bdb,#246cdb);
    color: white;
    border: 1px solid #a17aff;
    border-radius: 12px;
    width: 100%;
}
div[data-testid="stChatMessage"] {
    background: rgba(70,50,120,0.18);
    border: 1px solid rgba(150,120,255,0.2);
    border-radius: 15px;
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

