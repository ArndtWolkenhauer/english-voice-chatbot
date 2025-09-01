import streamlit as st
from openai import OpenAI

# OpenAI Client initialisieren
client = OpenAI()

st.title("🎙️ English Voice Chatbot")
st.write("Sprich Englisch: Lade eine Sprachaufnahme hoch, der Bot antwortet mit Stimme.")

# Upload eines Audio-Files
audio_file = st.file_uploader("Upload your spoken answer (mp3 or wav)", type=["mp3", "wav"])

if audio_file is not None:
    st.audio(audio_file, format="audio/mp3")

    # ====== 1. Speech-to-Text (Whisper) ======
    with open("user_input.mp3", "wb") as f:
        f.write(audio_file.getbuffer())

    with open("user_input.mp3", "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )

    user_text = transcript.text
    st.write(f"**You said:** {user_text}")

    # ====== 2. GPT-4o Antwort generieren ======
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an English teacher. Speak simply and clearly."},
            {"role": "user", "content": user_text}
        ]
    )

    assistant_response = response.choices[0].message.content
    st.write(f"**Assistant:** {assistant_response}")

    # ====== 3. Text-to-Speech ======
    tts_response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=assistant_response
    )

    with open("assistant_response.mp3", "wb") as tts_file:
        tts_file.write(tts_response.read())

    st.audio("assistant_response.mp3")
