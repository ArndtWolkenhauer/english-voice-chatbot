import streamlit as st
import openai
import tempfile
import time

# OpenAI Client
client = openai.OpenAI()

# System Prompt: Rolle festlegen
system_prompt = """
You are an English teacher having a short speaking exercise with a student. 
- Keep the conversation simple, friendly, and interactive.
- The conversation should last about 5 minutes (~10–15 exchanges).
- At the end of the conversation, give the student feedback in English:
  1. What they did well.
  2. What they can improve.
  3. A final grade (1–6, where 1 = excellent, 6 = poor).
"""

# Streamlit Titel
st.title("🎤 English Speaking Practice Bot")

# Gesprächsverlauf speichern
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": system_prompt}]
if "start_time" not in st.session_state:
    st.session_state["start_time"] = time.time()
if "finished" not in st.session_state:
    st.session_state["finished"] = False

# Timer prüfen
elapsed = time.time() - st.session_state["start_time"]

if elapsed >= 300 and not st.session_state["finished"]:  # 5 Minuten = 300 Sekunden
    st.subheader("📊 Final Feedback & Grade")

    feedback = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state["messages"] + [
            {"role": "system", "content": "Now, as the English teacher, summarize the conversation and give final feedback with a grade (1–6)."}
        ]
    )

    st.write(feedback.choices[0].message.content)

    # Reset
    st.session_state["finished"] = True
    st.stop()

# Audio aufnehmen
audio = st.audio_input("🎙️ Record your answer")

if audio and not st.session_state["finished"]:
    # Temporäre Datei speichern
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio.getbuffer())
        temp_filename = f.name

    # Speech-to-Text mit Whisper
    with open(temp_filename, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )

    user_text = transcript.text
    st.write(f"**You said:** {user_text}")

    # Schülerbeitrag in Nachrichten speichern
    st.session_state["messages"].append({"role": "user", "content": user_text})

    # Chatbot-Antwort erzeugen
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state["messages"]
    )
    assistant_response = response.choices[0].message.content
    st.session_state["messages"].append({"role": "assistant", "content": assistant_response})

    # Text anzeigen
    st.write(f"**Teacher:** {assistant_response}")

   # Text-to-Speech Antwort
tts_response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="alloy",
    input=assistant_response
)

with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tts_file:
    tts_file.write(tts_response.read())
    tts_filename = tts_file.name

st.audio(tts_filename)


st.audio(tts_filename)

