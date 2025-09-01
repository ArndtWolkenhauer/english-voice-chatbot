import streamlit as st
import openai
import tempfile
import os
import time

st.set_page_config(page_title="Voice English Chatbot", page_icon="🎤")
st.title("🎙️ English Voice Chatbot")
st.write("Speak in English. After 15 minutes, you'll get a language assessment.")

# OpenAI API Key aus Secrets
openai.api_key = os.environ["OPENAI_API_KEY"]

# Chatverlauf speichern
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "system",
            "content": "You are an English teacher. Speak clearly, correct mistakes and give feedback at the end."
        }
    ]

# Startzeit für 15-Minuten-Timer
if "start_time" not in st.session_state:
    st.session_state["start_time"] = time.time()

# Mikrofonaufnahme
audio_file = st.audio_input("Speak in English:")

if audio_file is not None:
    # Temporäre WAV-Datei speichern
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        tmpfile.write(audio_file.read())
        audio_path = tmpfile.name

    # Speech-to-Text mit Whisper
    with open(audio_path, "rb") as f:
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    user_text = transcript.text
    st.write(f"**You said:** {user_text}")

    # GPT-Antwort generieren
    st.session_state["messages"].append({"role": "user", "content": user_text})
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state["messages"]
    )
    bot_text = response.choices[0].message.content
    st.write(f"**Bot:** {bot_text}")
    st.session_state["messages"].append({"role": "assistant", "content": bot_text})

    # Text-to-Speech mit gpt-4o-mini-tts
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tts_file:
       tts_response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="alloy",
    input=assistant_response
)

# Audio in Datei speichern
with open("assistant_response.mp3", "wb") as f:
    f.write(tts_response.read())
        tts_file.write(tts_audio.read())
        st.audio(tts_file.name, format="audio/mp3")

# 15-Minuten-Timer für Feedback
elapsed = time.time() - st.session_state["start_time"]
remaining = 900 - elapsed  # 900 Sekunden = 15 Minuten

if remaining > 0:
    st.info(f"Time remaining: {int(remaining // 60)} min {int(remaining % 60)} sec")
else:
    if "feedback_given" not in st.session_state:
        # GPT generiert Feedback
        feedback_prompt = (
            "Please give a concise CEFR English level assessment and tips "
            "based on this conversation:\n\n" +
            "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state["messages"]])
        )
        feedback_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": feedback_prompt}]
        )
        feedback_text = feedback_response.choices[0].message.content
        st.session_state["feedback_given"] = True
        st.success("📝 Conversation ended! Here's your feedback:")
        st.write(feedback_text)
