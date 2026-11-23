import os
import json
import hashlib
import tempfile
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

# ------------------------------------------------------------
# NOVA-AI | Streamlit + Groq
# Existing chat, memory, language selector and dark theme kept.
# Voice mode uses record -> transcribe -> answer -> speak.
# ------------------------------------------------------------

st.set_page_config(
    page_title="NOVA-AI",
    page_icon="🌌",
    layout="wide",
)

MODEL = "openai/gpt-oss-120b"
TRANSCRIPTION_MODEL = "whisper-large-v3-turbo"
TTS_MODEL = "canopylabs/orpheus-v1-english"
TTS_VOICE = "troy"


def get_api_key():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        try:
            key = st.secrets["GROQ_API_KEY"]
        except Exception:
            key = None
    return key


api_key = get_api_key()
if not api_key:
    st.error("GROQ_API_KEY is missing. Add it in Streamlit Community Cloud → App settings → Secrets.")
    st.stop()

client = Groq(api_key=api_key)


# -------------------- SESSION STATE --------------------

defaults = {
    "messages": [],
    "memory": [],
    "language": "English",
    "mode": "Chat",
    "quick_prompt": None,
    "last_voice_answer": "",
    "last_voice_transcript": "",
    "last_voice_audio": None,
    "last_audio_hash": "",
    "web_search": False,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -------------------- HELPERS --------------------

def make_system_prompt():
    memory_notes = "\n".join("- " + item for item in st.session_state.memory)
    return f"""
You are NOVA-AI, a helpful, friendly and capable AI assistant created by QuantumNovaX.

Reply in the selected language: {st.session_state.language}.
If Tamil is selected, reply in natural, clear Tamil.
If English is selected, reply in English.
Follow the user's language preference. If the user writes in a different language,
respond naturally while respecting the selected preference.

Use these user-approved memory notes when helpful:
{memory_notes}

Be accurate and honest. Do not claim to have performed an action you cannot perform.
For current information, use web search when it is enabled for the request.
Keep spoken answers natural and easy to understand.
"""


def get_ai_answer(user_text, use_search=False):
    api_messages = [
        {"role": "system", "content": make_system_prompt()}
    ] + st.session_state.messages[-30:]

    request_args = {
        "model": MODEL,
        "messages": api_messages,
        "max_completion_tokens": 2048,
        "stream": False,
    }

    if use_search:
        # Groq's built-in browser search is supported by GPT-OSS models.
        request_args["tools"] = [{"type": "browser_search"}]
        request_args["tool_choice"] = "required"
        request_args["reasoning_effort"] = "low"

    result = client.chat.completions.create(**request_args)
    return result.choices[0].message.content or "I couldn't generate a response."


def transcribe_audio(audio_file):
    audio_bytes = audio_file.getvalue()
    transcript = client.audio.transcriptions.create(
        file=("nova_voice.wav", audio_bytes, "audio/wav"),
        model=TRANSCRIPTION_MODEL,
        response_format="json",
        prompt=(
            "NOVA-AI assistant conversation. The speaker may use Tamil, English, "
            "or a mixture of Tamil and English. Preserve the spoken language."
        ),
        temperature=0.0,
    )
    return (transcript.text or "").strip()


def make_english_speech(text):
    # Groq's current Orpheus TTS supports English and Arabic, not Tamil.
    # Limit the spoken version to avoid very long audio-generation requests.
    clean_text = text[:3500].strip()
    if not clean_text:
        return None
    speech = client.audio.speech.create(
        model=TTS_MODEL,
        voice=TTS_VOICE,
        input=clean_text,
        response_format="wav",
    )
    # The Groq SDK documents write_to_file() for its binary speech response.
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        speech.write_to_file(temp_path)
        with open(temp_path, "rb") as audio_file:
            return audio_file.read()
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def browser_speech_button(text, language):
    # Device/browser speech synthesis is used for Tamil and as a fallback.
    # The user must tap the button because browsers may block autoplay.
    safe_text = json.dumps(text).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    lang = "ta-IN" if "Tamil" in language or "தமிழ்" in language else "en-US"
    html = f"""
    <div style="font-family:Arial,sans-serif;background:#101317;border:1px solid #343b46;
                border-radius:14px;padding:12px;color:#fff;text-align:center;">
      <button id="speakNova" style="background:#202733;color:#fff;border:1px solid #69788d;
        border-radius:24px;padding:11px 22px;font-size:15px;font-weight:600;cursor:pointer;">
        🔊 Speak NOVA's reply
      </button>
      <div id="speechStatus" style="color:#aab3bf;font-size:12px;margin-top:8px;">
        Uses a voice available on this device
      </div>
    </div>
    <script>
      const spokenText = {safe_text};
      const spokenLang = {json.dumps(lang)};
      const button = document.getElementById("speakNova");
      const status = document.getElementById("speechStatus");
      button.addEventListener("click", () => {{
        if (!("speechSynthesis" in window)) {{
          status.textContent = "Speech playback is not supported in this browser.";
          return;
        }}
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(spokenText);
        utterance.lang = spokenLang;
        utterance.rate = 1.0;
        utterance.onstart = () => status.textContent = "NOVA is speaking…";
        utterance.onend = () => status.textContent = "Finished speaking.";
        utterance.onerror = () => status.textContent = "Could not play this voice. Try another browser voice.";
        window.speechSynthesis.speak(utterance);
      }});
    </script>
    """
    components.html(html, height=92)


def handle_message(user_text, voice=False):
    user_text = user_text.strip()
    if not user_text:
        return

    st.session_state.messages.append({"role": "user", "content": user_text})
    try:
        answer = get_ai_answer(user_text, use_search=st.session_state.web_search)
        st.session_state.messages.append({"role": "assistant", "content": answer})

        if voice:
            st.session_state.last_voice_transcript = user_text
            st.session_state.last_voice_answer = answer
            st.session_state.last_voice_audio = None
            if st.session_state.language == "English":
                try:
                    st.session_state.last_voice_audio = make_english_speech(answer)
                except Exception:
                    # Browser speech button remains available if Groq TTS is unavailable.
                    st.session_state.last_voice_audio = None
    except Exception as exc:
        error_message = f"NOVA connection error: {exc}"
        st.session_state.messages.append({"role": "assistant", "content": error_message})
        if voice:
            st.session_state.last_voice_transcript = user_text
            st.session_state.last_voice_answer = error_message
            st.session_state.last_voice_audio = None


# -------------------- DESIGN --------------------

st.markdown("""
<style>
.stApp { background:#050607; color:#f5f7fa; }
[data-testid="stHeader"] { background:rgba(5,6,7,.96); }
[data-testid="stSidebar"] { background:#0b0d10; border-right:1px solid #252a31; }
[data-testid="stSidebar"] * { color:#f1f3f5 !important; }
.stApp p,.stApp label,.stApp li,.stApp [data-testid="stMarkdownContainer"] { color:#f1f3f5; }
h1,h2,h3,h4 { color:#fff !important; }
.nova-title {
  text-align:center;font-size:clamp(34px,5vw,52px);font-weight:900;
  background:linear-gradient(90deg,#a879ff,#48c9ff);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
}
.subtitle { text-align:center;color:#b8c0cc !important;letter-spacing:2px; }
div.stButton>button {
  background:#171b21;color:#fff !important;border:1px solid #343b46;
  border-radius:10px;width:100%;font-weight:600;min-height:42px;
}
div.stButton>button:hover { background:#252c35;border-color:#657184;color:#fff !important; }
div[data-testid="stChatMessage"] { background:#101317;border:1px solid #272d36;border-radius:14px; }
div[data-testid="stChatMessage"] * { color:#f1f3f5 !important; }
[data-testid="stChatInput"] { background:#101317;border:1px solid #343b46;border-radius:12px; }
[data-testid="stChatInput"] textarea { color:#fff !important;-webkit-text-fill-color:#fff !important; }
[data-testid="stTextInput"] input,[data-testid="stSelectbox"] div { color:#fff !important; }
[data-testid="stTextInput"] input::placeholder,[data-testid="stChatInput"] textarea::placeholder {
  color:#aab3bf !important;-webkit-text-fill-color:#aab3bf !important;opacity:1;
}
[data-testid="stFileUploader"] { background:#101317;border:1px dashed #414a57;border-radius:12px; }
hr { border-color:#292f38; }
[data-testid="stCaptionContainer"] { color:#aab3bf !important; }
.voice-panel {
  background:radial-gradient(circle at 50% 35%,#17152d 0%,#090b12 45%,#050607 78%);
  border:1px solid #29263d;border-radius:24px;padding:32px 16px 26px;
  text-align:center;margin:12px 0 20px;min-height:290px;
}
.voice-orb {
  width:150px;height:150px;margin:8px auto 22px;border-radius:50%;
  background:radial-gradient(circle at 35% 30%,#d8c5ff 0%,#8e68ff 20%,#3d5dd8 48%,#10152f 72%);
  box-shadow:0 0 24px #8764ff88,0 0 65px #426bff55,inset 0 0 24px #ffffff55;
  animation:novaPulse 2.6s ease-in-out infinite;
}
@keyframes novaPulse {
  0%,100% { transform:scale(.96);box-shadow:0 0 24px #8764ff88,0 0 55px #426bff44; }
  50% { transform:scale(1.04);box-shadow:0 0 35px #a879ffbb,0 0 85px #426bff77; }
}
.voice-hint { color:#aeb7c6 !important;font-size:14px; }
@media(max-width:600px) {
  .voice-panel { padding:24px 10px;min-height:260px; }
  .voice-orb { width:125px;height:125px; }
}
</style>
""", unsafe_allow_html=True)


# -------------------- SIDEBAR --------------------

with st.sidebar:
    st.markdown("## ✦ NOVA-AI")
    st.caption("YOUR PERSONAL AI ASSISTANT")
    st.divider()

    st.markdown("### Interface")
    st.session_state.mode = st.radio(
        "Choose interface",
        ["Chat", "Voice"],
        index=0 if st.session_state.mode == "Chat" else 1,
        horizontal=True,
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("### 🌐 Language")
    language_options = [
        "English", "தமிழ் (Tamil)", "Hindi", "French", "Spanish",
        "German", "Japanese", "Arabic", "Telugu", "Malayalam"
    ]
    current_index = language_options.index(st.session_state.language) if st.session_state.language in language_options else 0
    st.session_state.language = st.selectbox(
        "Choose your reply language",
        language_options,
        index=current_index,
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("### 🌍 Web search")
    st.session_state.web_search = st.toggle(
        "Search the web for this chat",
        value=st.session_state.web_search,
        help="Uses Groq's built-in browser search with the GPT-OSS model.",
    )

    st.divider()
    st.markdown("### 🧠 Personal Memory")
    memory_text = st.text_input(
        "Save something NOVA should remember",
        placeholder="Example: I like short answers",
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
        st.session_state.last_voice_answer = ""
        st.session_state.last_voice_transcript = ""
        st.session_state.last_voice_audio = None
        st.session_state.last_audio_hash = ""
        st.rerun()

    st.caption(f"{len(st.session_state.messages)} messages in this session")
    st.divider()
    st.markdown("💎 **NOVA PREMIUM DESIGN**")
    st.caption("Smarter. Kinder. Always here.")


# -------------------- MAIN HEADER --------------------

st.markdown('<div class="nova-title">✦ NOVA-AI ✦</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">YOUR SMART PERSONAL AI ASSISTANT</div>', unsafe_allow_html=True)
st.write("")


# -------------------- VOICE MODE --------------------

if st.session_state.mode == "Voice":
    st.markdown("""
    <div class="voice-panel">
      <div class="voice-orb"></div>
      <h2 style="margin:0;color:#fff;">NOVA Voice</h2>
      <p class="voice-hint">Speak naturally. NOVA will listen, think and reply.</p>
    </div>
    """, unsafe_allow_html=True)

    st.caption("1. Tap the microphone and record your message. 2. Stop recording. 3. Send it to NOVA.")
    audio_value = st.audio_input(
        "🎙️ Record your message",
        sample_rate=16000,
        key="nova_voice_recorder",
        help="Allow microphone access when your browser asks.",
    )

    send_col, clear_col = st.columns(2)
    with send_col:
        send_voice = st.button("Send to NOVA ➜", type="primary", use_container_width=True)
    with clear_col:
        clear_voice = st.button("Clear voice reply", use_container_width=True)

    if clear_voice:
        st.session_state.last_voice_answer = ""
        st.session_state.last_voice_transcript = ""
        st.session_state.last_voice_audio = None
        st.rerun()

    if send_voice:
        if audio_value is None:
            st.warning("Record a message first.")
        else:
            audio_hash = hashlib.sha256(audio_value.getvalue()).hexdigest()
            if audio_hash == st.session_state.last_audio_hash:
                st.info("This recording was already sent. Record a new message to continue.")
            else:
                with st.spinner("NOVA is listening…"):
                    try:
                        transcript_text = transcribe_audio(audio_value)
                        if not transcript_text:
                            st.warning("I couldn't hear clear speech. Please try recording again.")
                        else:
                            st.session_state.last_audio_hash = audio_hash
                            handle_message(transcript_text, voice=True)
                            st.rerun()
                    except Exception as exc:
                        st.error(f"Voice transcription failed: {exc}")

    if st.session_state.last_voice_answer:
        st.divider()
        st.markdown("#### You said")
        st.info(st.session_state.last_voice_transcript)
        st.markdown("#### NOVA replied")
        st.markdown(st.session_state.last_voice_answer)

        if st.session_state.last_voice_audio:
            st.caption("NOVA voice reply (English)")
            st.audio(st.session_state.last_voice_audio, format="audio/wav")
        else:
            browser_speech_button(
                st.session_state.last_voice_answer,
                st.session_state.language,
            )

    with st.expander("Recent conversation"):
        for message in st.session_state.messages[-10:]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


# -------------------- CHAT MODE --------------------

else:
    st.markdown("<h2 style='text-align:center'>Welcome to NOVA ✨</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:#bba9ed'>What would you like to explore today?</p>",
        unsafe_allow_html=True,
    )

    st.markdown("### ✨ Explore NOVA")
    col1, col2, col3 = st.columns(3)

    if col1.button("💡 Explain something"):
        st.session_state.quick_prompt = "Explain an interesting topic to me."
        st.rerun()
    if col2.button("✍️ Help me write"):
        st.session_state.quick_prompt = "Help me write something."
        st.rerun()
    if col3.button("💻 Coding help"):
        st.session_state.quick_prompt = "Help me with a coding problem."
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("✨ Message NOVA-AI...")
    if st.session_state.quick_prompt:
        prompt = st.session_state.quick_prompt
        st.session_state.quick_prompt = None

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("NOVA is thinking... ✨"):
                try:
                    answer = get_ai_answer(prompt, use_search=st.session_state.web_search)
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as exc:
                    st.error(f"NOVA connection error: {exc}")

