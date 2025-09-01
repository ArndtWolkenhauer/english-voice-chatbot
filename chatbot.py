import streamlit as st
import openai
import tempfile
import time
import base64

# OpenAI Client initialisieren
client = openai.OpenAI()

# System Prompt Vorlage für 8.-Klassen-Niveau
system_prompt_template = """
You are an English teacher conducting a speaking exercise with a student at 8th grade level.
- Speak slowly and clearly, encourage the student to speak as much as possible.
- Use simple vocabulary appropriate for 8th grade.
- Focus on fluency, pronunciation, grammar, and vocabulary.
- Engage in a conversation lasting up to 5 minutes (~10–15 exchanges).
- At the end of the conversation, provide detailed feedback in English:
  1. What the student did well.
  2. What can be improved.
  3. A final grade from 1 to 6 (1 = excellent, 6 = poor).
- Be friendly, supportive, and motivate the student.
"""

st.title("🎤 English Speaking Practice Bot (8th Grade)")

# Session-Variablen initialisieren
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "start_time" not in st.session_state:
    st.session_state["start_time"] = None
if "finished" not in st.session_state:
    st.session_state["finished"] = False
if "topic_set" not in st.session_state:
    st.session_state["topic_set"] = False

# Schüler wählt Thema am Anfang
if not st.session_state["topic_set"]:
    topic = st.text_input("Enter a topic for your conversation:")
    if topic:
        st.session_state["messages"].append({
            "role": "system",
            "content": system_prompt_template + f"\nThe student wants to talk about: {topic}"
        })
        st.session_state["topic_set"] = True
        st.session_state["start_time"] = time.time()
        st.success(f"Topic set: {topic}")

# Timer prüfen
if st.session_state["start_time"]:
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
        st.session_state["finished"] = True
        st.stop()

# Audio aufnehmen
audio_input = st.audio_input("🎙️ Record your answer")

if audio_input and not st.session_state["finished"] and st.session_state["topic_set"]:
    # Temporäre Datei speichern
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_input.getbuffer())
        temp_filename = f.name

    # Speech-to-Text mit Whisper
    with open(temp_filename, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )

    user_text = transcript.text
    st.write(f"**You said:** {user_text}")

    # Schülerbeitrag speichern
    st.session_state["messages"].append({"role": "user", "content": user_text})

    # GPT-4o Antwort generieren
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state["messages"]
    )
    assistant_response = response.choices[0].message.content
    st.session_state["messages"].append({"role": "assistant", "content": assistant_response})

    # Text anzeigen
    st.write(f"**Teacher:** {assistant_response}")

    # Text-to-Speech
    tts_response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=assistant_response
    )

    # Audio automatisch abspielen (HTML + Base64)
    audio_file = tts_response.read()
    b64_audio = base64.b64encode(audio_file).decode()
    st.markdown(f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
        </audio>
    """, unsafe_allow_html=True)
