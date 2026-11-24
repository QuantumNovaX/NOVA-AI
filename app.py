
import os
import io
import json
import base64
import requests
import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
from streamlit_mic_recorder import speech_to_text

# =====================================================
# NOVA-AI
# =====================================================

st.set_page_config(
    page_title="NOVA-AI",
    page_icon="🌌",
    layout="wide"
)

# API CONFIGURATION

def get_secret(name):
    try:
        return st.secrets.get(name, os.getenv(name, ""))
    except Exception:
        return os.getenv(name, "")

GROQ_KEY = get_secret("GROQ_API_KEY")
TAVILY_KEY = get_secret("TAVILY_API_KEY")
HF_TOKEN = get_secret("HF_TOKEN")

if not GROQ_KEY:
    st.error("Add GROQ_API_KEY in Streamlit Secrets.")
    st.stop()

client = Groq(api_key=GROQ_KEY)

CHAT_MODEL = "openai/gpt-oss-120b"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# =====================================================
# SESSION STATE
# =====================================================

defaults = {
    "messages": [],
    "language": "English",
    "memory": "",
    "voice_enabled": True,
    "dark_mode": True,
    "last_voice_hash": "",
    "last_answer": "",
    "pending_prompt": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =====================================================
# DESIGN
# =====================================================

if st.session_state.dark_mode:
    bg = "#171717"
    panel = "#222222"
    fg = "#FFFFFF"
    border = "#393939"
else:
    bg = "#FFFFFF"
    panel = "#F2F2F2"
    fg = "#171717"
    border = "#DDDDDD"

st.markdown(f"""
<style>
.stApp {{
    background:{bg};
    color:{fg};
}}
[data-testid="stSidebar"] {{
    background:{panel};
}}
h1,h2,h3,p,label,span {{
    color:{fg};
}}
.stTextInput input,.stTextArea textarea {{
    background:{panel};
    color:{fg};
    border:1px solid {border};
    border-radius:18px;
}}
.stButton button {{
    background:{panel};
    color:{fg};
    border:1px solid {border};
    border-radius:20px;
    min-height:40px;
}}
[data-testid="stChatMessage"] {{
    background:transparent;
    border:0;
}}
.block-container {{
    max-width:950px;
    padding-bottom:5rem;
}}
</style>
""", unsafe_allow_html=True)

# =====================================================
# WEB SEARCH
# =====================================================

def web_search(query):
    if not TAVILY_KEY:
        return "Web search is not configured. Add TAVILY_API_KEY."

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": 5
            },
            timeout=30
        )
        response.raise_for_status()

        results = response.json().get("results", [])

        return "\n".join(
            f"Title: {r.get('title')}\n"
            f"URL: {r.get('url')}\n"
            f"Content: {r.get('content')}"
            for r in results
        ) or "No search results found."

    except Exception as error:
        return f"Search error: {error}"

# =====================================================
# IMAGE UNDERSTANDING
# =====================================================

def analyze_image(image):
    try:
        image_bytes = image.getvalue()
        encoded = base64.b64encode(image_bytes).decode()

        mime = image.type or "image/jpeg"

        result = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe and analyze this image."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{encoded}"
                            }
                        }
                    ]
                }
            ],
            max_completion_tokens=1024
        )

        return result.choices[0].message.content

    except Exception as error:
        return f"Image analysis error: {error}"

# =====================================================
# DOCUMENT READING
# =====================================================

def read_document(upload):
    try:
        name = upload.name.lower()

        if name.endswith(".txt"):
            return upload.getvalue().decode(
                "utf-8", errors="replace"
            )

        if name.endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(upload)
            return "\n".join(
                page.extract_text() or ""
                for page in reader.pages[:30]
            )

        if name.endswith(".docx"):
            from docx import Document
            document = Document(upload)
            return "\n".join(
                paragraph.text for paragraph in document.paragraphs
            )

        return "Unsupported document format."

    except Exception as error:
        return f"Document reading error: {error}"

# =====================================================
# IMAGE GENERATION
# =====================================================

def generate_image(prompt):
    try:
        hf_token = st.secrets["HF_TOKEN"]

        client = InferenceClient(api_key=hf_token)

        image = client.text_to_image(
            prompt=prompt,
            model="black-forest-labs/FLUX.1-dev"
        )

        return image

    except Exception as e:
        st.error(f"Image generation failed: {e}")
        return None
    if not HF_TOKEN:
        return None, "Add HF_TOKEN in Streamlit Secrets."

    try:
        response = requests.post(
            "https://router.huggingface.co/v1/images/generations",
            headers={
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "model": "black-forest-labs/FLUX.1-schnell",
                "prompt": prompt
            },
            timeout=180
        )

        response.raise_for_status()

        return response.content, None

    except Exception as error:
        return None, str(error)

# =====================================================
# TEXT TO SPEECH
# =====================================================

def make_speech(text):
    try:
        result = client.audio.speech.create(
            model="canopylabs/orpheus-v1-english",
            voice="troy",
            input=text[:1800],
            response_format="wav"
        )
        return result.read()
    except Exception:
        return None

# =====================================================
# AI CHAT
# =====================================================

def ask_nova(prompt, image=None, document_text=""):
    search_context = ""

    if st.session_state.search_enabled:
        search_context = web_search(prompt)

    system = f"""
You are NOVA-AI, a helpful intelligent AI assistant.

Respond in {st.session_state.language}.
Be accurate, friendly and clear.

User memory:
{st.session_state.memory}

Web search information:
{search_context}

Uploaded document:
{document_text[:12000]}
"""

    if image is not None:
        try:
            encoded = base64.b64encode(
                image.getvalue()
            ).decode()

            content = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image.type};base64,{encoded}"
                    }
                }
            ]

            messages = [
                {"role": "system", "content": system}
            ]

            for item in st.session_state.messages[-20:]:
                messages.append({
                    "role": item["role"],
                    "content": item["content"]
                })

            messages.append({
                "role": "user",
                "content": content
            })

            result = client.chat.completions.create(
                model=VISION_MODEL,
                messages=messages,
                max_completion_tokens=2048
            )

        except Exception as error:
            return f"Image question error: {error}"

    else:
        messages = [
            {"role": "system", "content": system}
        ]

        messages.extend([
            {
                "role": item["role"],
                "content": item["content"]
            }
            for item in st.session_state.messages[-20:]
        ])

        messages.append({
            "role": "user",
            "content": prompt
        })

        result = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            max_completion_tokens=2048
        )

    return result.choices[0].message.content

def send_message(prompt, image=None, document_text=""):
    if not prompt.strip():
        return

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    try:
        answer = ask_nova(
            prompt,
            image=image,
            document_text=document_text
        )
    except Exception as error:
        answer = f"NOVA-AI error: {error}"

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    st.session_state.last_answer = answer

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:
    st.title("🌌 NOVA-AI")
    st.caption("Your AI assistant")

    if st.button("＋ New chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_answer = ""
        st.rerun()

    st.divider()

    st.subheader("Settings")

    languages = [
        "English", "Tamil", "Hindi", "Telugu",
        "Malayalam", "French", "Spanish",
        "German", "Japanese", "Arabic"
    ]

    st.session_state.language = st.selectbox(
        "Language",
        languages,
        index=languages.index(st.session_state.language)
    )

    st.session_state.voice_enabled = st.toggle(
        "Voice responses",
        value=st.session_state.voice_enabled
    )

    st.session_state.search_enabled = st.toggle(
        "Web search",
        value=st.session_state.get("search_enabled", False)
    )

    st.session_state.dark_mode = st.toggle(
        "Dark theme",
        value=st.session_state.dark_mode
    )

    st.divider()

    st.subheader("Memory")

    memory = st.text_area(
        "Saved information",
        value=st.session_state.memory
    )

    if st.button("Save memory"):
        st.session_state.memory = memory
        st.success("Memory saved for this session.")

    if st.button("Clear memory"):
        st.session_state.memory = ""
        st.rerun()

    st.divider()

    chat_export = json.dumps(
        st.session_state.messages,
        ensure_ascii=False,
        indent=2
    )

    st.download_button(
        "Download chat history",
        chat_export,
        file_name="nova_chat.json",
        mime="application/json",
        use_container_width=True
    )

    st.caption("Powered by Groq")

# =====================================================
# MAIN INTERFACE
# =====================================================

st.title("NOVA-AI")

if not st.session_state.messages:
    st.markdown("### What can I help you with?")
    st.caption("Ask questions, create images, upload files or use voice.")

    col1, col2 = st.columns(2)

    if col1.button("💡 Explain something"):
        st.session_state.pending_prompt = "Explain an interesting topic."
        st.rerun()

    if col2.button("💻 Help me code"):
        st.session_state.pending_prompt = "Help me write code."
        st.rerun()

# =====================================================
# CHAT HISTORY
# =====================================================

for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            if st.button("Copy response", key=f"copy_{index}"):
                st.code(message["content"])

# =====================================================
# IMAGE CREATION
# =====================================================

with st.expander("🎨 Create an image"):
    image_prompt = st.text_area(
        "Describe the image you want",
        placeholder="A futuristic city at sunset..."
    )

    if st.button("Generate image"):
        if image_prompt.strip():
            with st.spinner("Creating your image..."):
                image_bytes, error = generate_image(image_prompt)

            if image_bytes:
                st.image(image_bytes, caption=image_prompt)
                st.download_button(
                    "Download image",
                    image_bytes,
                    file_name="nova_generated_image.png",
                    mime="image/png"
                )
            else:
                st.error(error)

# =====================================================
# UPLOADS
# =====================================================

with st.expander("📎 Upload image or document"):
    uploaded_image = st.file_uploader(
        "Upload an image",
        type=["png", "jpg", "jpeg", "webp"],
        key="nova_image"
    )

    uploaded_document = st.file_uploader(
        "Upload a document",
        type=["pdf", "txt", "docx"],
        key="nova_document"
    )

    if uploaded_image:
        st.image(uploaded_image, width=220)

    document_text = ""

    if uploaded_document:
        document_text = read_document(uploaded_document)
        st.success("Document loaded.")

# =====================================================
# CHAT COMPOSER
# =====================================================

col1, col2, col3 = st.columns([7, 1, 1])

with col1:
    user_text = st.text_input(
        "Message NOVA-AI",
        placeholder="Ask anything...",
        label_visibility="collapsed",
        key="nova_input"
    )

with col2:
    voice_text = speech_to_text(
        language=(
            "ta-IN"
            if st.session_state.language == "Tamil"
            else "en-US"
        ),
        start_prompt="🎙️",
        stop_prompt="⏹️",
        just_once=True,
        key="nova_mic"
    )

with col3:
    send = st.button("➤", use_container_width=True)

if st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
    send_message(prompt)
    st.rerun()

if send and user_text.strip():
    send_message(
        user_text,
        image=uploaded_image,
        document_text=document_text
    )
    st.rerun()

if voice_text:
    import hashlib

    voice_hash = hashlib.sha256(
        voice_text.encode()
    ).hexdigest()

    if voice_hash != st.session_state.last_voice_hash:
        st.session_state.last_voice_hash = voice_hash
        send_message(voice_text)
        st.rerun()

# =====================================================
# SPEECH PLAYBACK
# =====================================================

if st.session_state.last_answer:
    if st.session_state.voice_enabled:
        if st.button("🔊 Speak last answer"):
            if st.session_state.language == "English":
                audio = make_speech(
                    st.session_state.last_answer
                )

                if audio:
                    st.audio(audio, format="audio/wav")
                else:
                    st.warning("Speech generation unavailable.")
            else:
                safe_text = json.dumps(
                    st.session_state.last_answer
                )

                lang = (
                    "ta-IN"
                    if st.session_state.language == "Tamil"
                    else "en-US"
                )

                components.html(
                    f"""
                    <script>
                    const speech = new SpeechSynthesisUtterance(
                        {safe_text}
                    );
                    speech.lang = "{lang}";
                    speechSynthesis.cancel();
                    speechSynthesis.speak(speech);
                    </script>
                    """,
                    height=0
                )

