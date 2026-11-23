
import os
import json
import hashlib
import tempfile
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
from streamlit_mic_recorder import speech_to_text

st.set_page_config(
    page_title="NOVA-AI",
    page_icon="🌌",
    layout="wide"
)

# ---------------- CONFIGURATION ----------------

MODEL = "openai/gpt-oss-120b"
TRANSCRIPTION_MODEL = "whisper-large-v3-turbo"
TTS_MODEL = "canopylabs/orpheus-v1-english"

api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        st.error("GROQ_API_KEY is missing. Add it in Streamlit Secrets.")
        st.stop()

client = Groq(api_key=api_key)

# ---------------- SESSION STATE ----------------

defaults = {
    "messages": [],
    "memory": "",
    "language": "English",
    "auto_speak": True,
    "web_search": False,
    "quick_prompt": None,
    "last_voice_hash": "",
    "last_spoken_text": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------- AI SYSTEM ----------------

def system_prompt():
    return f"""
You are NOVA-AI, a helpful and intelligent AI assistant.

Respond in {st.session_state.language}.
Be friendly, clear, accurate and useful.
Explain difficult things simply.
Use the user's saved memory when relevant.

Saved memory:
{st.session_state.memory}
"""

def get_ai_answer(user_text):
    conversation = [
        {"role": "system", "content": system_prompt()}
    ]

    for message in st.session_state.messages[-30:]:
        conversation.append({
            "role": message["role"],
            "content": message["content"]
        })

    conversation.append({
        "role": "user",
        "content": user_text
    })

    response = client.chat.completions.create(
        model=MODEL,
        messages=conversation,
        temperature=0.7,
        max_completion_tokens=2048
    )

    return response.choices[0].message.content

# ---------------- TEXT TO SPEECH ----------------

def make_speech(text):
    try:
        response = client.audio.speech.create(
            model=TTS_MODEL,
            voice="troy",
            input=text[:1800],
            response_format="wav"
        )

        audio_bytes = response.read()
        return audio_bytes

    except Exception:
        return None

# ---------------- CHAT HANDLER ----------------

def handle_message(user_text):
    if not user_text or not user_text.strip():
        return

    user_text = user_text.strip()

    st.session_state.messages.append({
        "role": "user",
        "content": user_text
    })

    try:
        answer = get_ai_answer(user_text)

    except Exception as error:
        answer = f"Sorry, I encountered an error: {error}"

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    st.session_state.last_spoken_text = answer

# ---------------- DESIGN ----------------

st.markdown("""
<style>
.stApp {
    background: #080808;
    color: #ffffff;
}

header[data-testid="stHeader"] {
    background: #080808;
}

section[data-testid="stSidebar"] {
    background: #111111;
}

h1, h2, h3, p, label, span {
    color: #ffffff;
}

.stTextInput input {
    background: #171717;
    color: white;
    border: 1px solid #444444;
    border-radius: 20px;
}

.stButton button {
    background: #242424;
    color: white;
    border: 1px solid #444444;
    border-radius: 20px;
}

.stButton button:hover {
    background: #383838;
    border-color: #888888;
}

[data-testid="stChatMessage"] {
    background: #151515;
    border-radius: 16px;
    padding: 12px;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.title("🌌 NOVA-AI")

    st.subheader("Settings")

    st.session_state.language = st.selectbox(
        "Language",
        [
            "English",
            "Tamil",
            "Hindi",
            "Telugu",
            "Malayalam",
            "French",
            "Spanish",
            "German",
            "Japanese",
            "Arabic"
        ],
        index=[
            "English", "Tamil", "Hindi", "Telugu",
            "Malayalam", "French", "Spanish",
            "German", "Japanese", "Arabic"
        ].index(st.session_state.language)
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

    if st.button("＋ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_spoken_text = ""
        st.rerun()

    st.subheader("Memory")

    memory_input = st.text_area(
        "Your saved information",
        value=st.session_state.memory
    )

    if st.button("Save Memory"):
        st.session_state.memory = memory_input
        st.success("Memory saved for this session.")

    if st.button("Clear Memory"):
        st.session_state.memory = ""
        st.success("Memory cleared.")

    st.divider()
    st.caption("NOVA-AI • Powered by Groq")

# ---------------- MAIN CHAT ----------------

st.title("🌌 NOVA-AI")

st.caption("Your intelligent AI assistant")

if not st.session_state.messages:
    st.markdown("### Hello! How can I help you today?")

    prompts = [
        "Explain a difficult topic",
        "Help me write code",
        "Give me creative ideas",
        "Teach me something new"
    ]

    columns = st.columns(2)

    for index, prompt in enumerate(prompts):
        if columns[index % 2].button(
            prompt,
            use_container_width=True
        ):
            handle_message(prompt)
            st.rerun()

# ---------------- MESSAGE HISTORY ----------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------- CHAT INPUT ----------------

st.divider()

col1, col2, col3 = st.columns([7, 1, 1])

with col1:
    user_input = st.text_input(
        "Message NOVA-AI",
        placeholder="Ask anything...",
        label_visibility="collapsed",
        key="nova_message"
    )

with col2:
    voice_text = speech_to_text(
        language="ta-IN" if st.session_state.language == "Tamil"
        else "en-US",
        start_prompt="🎙️",
        stop_prompt="⏹️",
        just_once=True,
        key="nova_voice"
    )

with col3:
    send = st.button("➤", use_container_width=True)

if send and user_input.strip():
    handle_message(user_input)
    st.rerun()

# ---------------- VOICE MESSAGE ----------------

if voice_text:
    voice_hash = hashlib.sha256(
        voice_text.encode("utf-8")
    ).hexdigest()

    if voice_hash != st.session_state.last_voice_hash:
        st.session_state.last_voice_hash = voice_hash
        handle_message(voice_text)
        st.rerun()

# ---------------- SPEAK RESPONSE ----------------

if (
    st.session_state.auto_speak
    and st.session_state.last_spoken_text
):
    answer = st.session_state.last_spoken_text

    if st.session_state.language == "English":
        audio = make_speech(answer)

        if audio:
            st.audio(audio, format="audio/wav")

    if st.button("🔊 Speak response"):
        safe_text = json.dumps(answer)

        language = (
            "ta-IN"
            if st.session_state.language == "Tamil"
            else "en-US"
        )

        components.html(
            f"""
            <script>
            const text = {safe_text};
            const speech = new SpeechSynthesisUtterance(text);
            speech.lang = "{language}";
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(speech);
            </script>
            """,
            height=0
)
    
