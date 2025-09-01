import streamlit as st
from openai import OpenAI

# OpenAI Client
client = OpenAI()

st.title("🎙️ English Voice Chatbot")
st.write("Sprich Englisch direkt ins Mikrofon. Der Bot antwortet mit Text und Stimme.")

# ====== 1. Sprachaufnahme ======
audio_input = st.audio_input("🎤 Record your voice")

if audio_input is not None:
    st.audio(audio_input)

    # ====== 2. Speech-to-Text (Whisper) ======
    with open("user_input.wav", "wb") as f:
        f.write(audio_input.getbuffer())

    with open("user_input.wav", "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )

    user_text = transcript.text
    st.write(f"**You said:** {user_text}")

    # ====== 3. GPT-4o Antwort ======
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an English teacher. Speak simply and clearly."},
            {"role": "user", "content": user_text}
        ]
    )

    assistant_response = response.choices[0].message.content
    st.write(f"**Assistant:** {assistant_response}")

    # ====== 4. Text-to-Speech ======
    tts_response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=assistant_response
    )

    with open("assistant_response.mp3", "wb") as tts_file:
        tts_file.write(tts_response.read())

    st.audio("assistant_response.mp3")
