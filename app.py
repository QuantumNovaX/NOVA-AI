
import os
import json
import hashlib
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
from streamlit_mic_recorder import speech_to_text

st.set_page_config(
    page_title="NOVA-AI",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- API ----------------

API_KEY = os.environ.get("GROQ_API_KEY")

if not API_KEY:
    try:
        API_KEY = st.secrets["GROQ_API_KEY"]
    except Exception:
        st.error("GROQ_API_KEY is missing from Streamlit Secrets.")
        st.stop()

client = Groq(api_key=API_KEY)
MODEL = "openai/gpt-oss-120b"

# ---------------- STATE ----------------

defaults = {
    "messages": [],
    "memory": "",
    "language": "English",
    "auto_speak": True,
    "web_search": False,
    "last_voice_hash": "",
    "last_answer": "",
    "show_voice": False
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------- STYLE ----------------

st.markdown("""
<style>
.stApp {
    background: #212121;
    color: #f5f5f5;
}

header[data-testid="stHeader"] {
    background: #212121;
}

section[data-testid="stSidebar"] {
    background: #171717;
    border-right: 1px solid #303030;
}

h1,h2,h3,p,label,span {
    color: #f5f5f5;
}

.block-container {
    max-width: 900px;
    padding-top: 1.5rem;
    padding-bottom: 7rem;
}

.stTextInput input, .stTextArea textarea {
    background: #303030 !important;
    color: white !important;
    border: 1px solid #444 !important;
    border-radius: 18px !important;
}

.stButton button {
    background: #303030;
    color: white;
    border: 1px solid #454545;
    border-radius: 22px;
    min-height: 42px;
}

.stButton button:hover {
    background: #444;
    border-color: #777;
}

[data-testid="stChatMessage"] {
    background: transparent;
    border: none;
    padding: 12px 4px;
}

[data-testid="stChatMessageContent"] {
    color: #f5f5f5;
}

[data-testid="stBottom"] {
    background: #212121;
}

footer {
    visibility: hidden;
}

.nova-brand {
    font-size: 27px;
    font-weight: 750;
    letter-spacing: -1px;
}

.nova-subtitle {
    color: #a5a5a5;
    font-size: 14px;
}

.nova-center {
    text-align: center;
    padding-top: 65px;
    padding-bottom: 25px;
}

.nova-orb {
    width: 82px;
    height: 82px;
    margin: auto;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 30%,
        #ffffff, #a8baff 20%, #536dff 45%, #171b48 75%);
    box-shadow: 0 0 45px #536dff66;
}

div[data-testid="stHorizontalBlock"] {
    gap: 8px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- AI ----------------

def get_system_prompt():
    return f"""
You are NOVA-AI, an advanced helpful AI assistant.
Respond in {st.session_state.language}.
Be intelligent, friendly, accurate and clear.
Explain difficult topics in simple steps.

User memory:
{st.session_state.memory}
"""

def get_answer(prompt):
    messages = [
        {"role": "system", "content": get_system_prompt()}
    ]

    messages.extend(st.session_state.messages[-30:])

    messages.append({
        "role": "user",
        "content": prompt
    })

    result = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
        max_completion_tokens=2048
    )

    return result.choices[0].message.content

def send_message(prompt):
    if not prompt or not prompt.strip():
        return

    prompt = prompt.strip()

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    try:
        answer = get_answer(prompt)
    except Exception as error:
        answer = f"Something went wrong: {error}"

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    st.session_state.last_answer = answer

# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.markdown('<div class="nova-brand">🌌 NOVA-AI</div>',
                unsafe_allow_html=True)
    st.caption("Your AI workspace")

    if st.button("＋  New chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_answer = ""
        st.session_state.show_voice = False
        st.rerun()

    st.divider()

    st.subheader("Settings")

    languages = [
        "English", "Tamil", "Hindi", "Telugu",
        "Malayalam", "French", "Spanish",
        "German", "Japanese", "Arabic"
    ]

    st.session_state.language = st.selectbox(
        "Response language",
        languages,
        index=languages.index(st.session_state.language)
    )

    st.session_state.auto_speak = st.toggle(
        "Voice responses",
        value=st.session_state.auto_speak
    )

    st.session_state.web_search = st.toggle(
        "Web search",
        value=st.session_state.web_search
    )

    st.divider()
    st.subheader("Memory")

    memory = st.text_area(
        "What should NOVA remember?",
        value=st.session_state.memory,
        height=100
    )

    if st.button("Save memory", use_container_width=True):
        st.session_state.memory = memory
        st.success("Saved for this session.")

    if st.button("Clear memory", use_container_width=True):
        st.session_state.memory = ""
        st.rerun()

    st.divider()
    st.caption(f"{len(st.session_state.messages)} messages")
    st.caption("Powered by Groq")

# ---------------- HEADER ----------------

left, right = st.columns([5, 1])

with left:
    st.markdown("### NOVA-AI")

with right:
    if st.button("🎙️ Voice"):
        st.session_state.show_voice = not st.session_state.show_voice
        st.rerun()

st.divider()

# ---------------- VOICE SCREEN ----------------

if st.session_state.show_voice:
    st.markdown("""
    <div class="nova-center">
        <div class="nova-orb"></div>
        <h2>Voice mode</h2>
        <p class="nova-subtitle">
            Speak to NOVA-AI using your microphone
        </p>
    </div>
    """, unsafe_allow_html=True)

    voice_text = speech_to_text(
        language="ta-IN" if st.session_state.language == "Tamil"
        else "en-US",
        start_prompt="🎙️ Start speaking",
        stop_prompt="⏹️ Stop recording",
        just_once=True,
        key="nova_voice_screen"
    )

    if voice_text:
        voice_hash = hashlib.sha256(
            voice_text.encode("utf-8")
        ).hexdigest()

        if voice_hash != st.session_state.last_voice_hash:
            st.session_state.last_voice_hash = voice_hash
            send_message(voice_text)
            st.rerun()

    if st.button("← Back to chat"):
        st.session_state.show_voice = False
        st.rerun()

# ---------------- CHAT SCREEN ----------------

else:

    if not st.session_state.messages:
        st.markdown("""
        <div class="nova-center">
            <div class="nova-orb"></div>
            <h2>What can I help with?</h2>
            <p class="nova-subtitle">
                Ask questions, learn, create and explore.
            </p>
        </div>
        """, unsafe_allow_html=True)

        prompts = [
            "Explain something difficult",
            "Help me write code",
            "Give me creative ideas",
            "Teach me something new"
        ]

        for row in range(2):
            c1, c2 = st.columns(2)

            for col, index in zip(
                [c1, c2],
                [row * 2, row * 2 + 1]
            ):
                with col:
                    if st.button(
                        prompts[index],
                        use_container_width=True
                    ):
                        send_message(prompts[index])
                        st.rerun()

    # Chat history
    for index, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                if st.button(
                    "📋 Copy response",
                    key=f"copy_{index}"
                ):
                    st.code(message["content"])

    # Composer
    st.divider()

    text_col, mic_col, send_col = st.columns([7, 1, 1])

    with text_col:
        user_text = st.text_input(
            "Message",
            placeholder="Message NOVA-AI...",
            label_visibility="collapsed",
            key="nova_chat_input"
        )

    with mic_col:
        voice_text = speech_to_text(
            language="ta-IN" if st.session_state.language == "Tamil"
            else "en-US",
            start_prompt="🎙️",
            stop_prompt="⏹️",
            just_once=True,
            key="nova_chat_mic"
        )

    with send_col:
        send = st.button("➤", use_container_width=True)

    if send and user_text.strip():
        send_message(user_text)
        st.rerun()

    if voice_text:
        voice_hash = hashlib.sha256(
            voice_text.encode("utf-8")
        ).hexdigest()

        if voice_hash != st.session_state.last_voice_hash:
            st.session_state.last_voice_hash = voice_hash
            send_message(voice_text)
            st.rerun()

# ---------------- SPEECH ----------------

if (
    st.session_state.auto_speak
    and st.session_state.last_answer
):
    st.divider()

    if st.session_state.language == "English":
        if st.button("🔊 Play last answer"):
            try:
                audio = client.audio.speech.create(
                    model="canopylabs/orpheus-v1-english",
                    voice="troy",
                    input=st.session_state.last_answer[:1800],
                    response_format="wav"
                )

                st.audio(audio.read(), format="audio/wav")

            except Exception as error:
                st.warning(f"Speech unavailable: {error}")

    else:
        if st.button("🔊 Speak last answer"):
            speech_text = json.dumps(
                st.session_state.last_answer
            )

            lang = (
                "ta-IN" if st.session_state.language == "Tamil"
                else "en-US"
            )

            components.html(
                f"""
                <script>
                const u = new SpeechSynthesisUtterance({speech_text});
                u.lang = "{lang}";
                speechSynthesis.cancel();
                speechSynthesis.speak(u);
                </script>
                """,
                height=0
                )
            
