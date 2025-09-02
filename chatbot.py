import streamlit as st
import openai
import tempfile
import time
import requests
from fpdf import FPDF
import random
import threading

# OpenAI Client initialisieren
client = openai.OpenAI()

# Texte auf GitHub (raw URLs)
text_options = {
    "New_York": "https://raw.githubusercontent.com/ArndtWolkenhauer/texts/main/New_York",
    "Summer_Vacation_Paris": "https://raw.githubusercontent.com/ArndtWolkenhauer/texts/main/Summer_Vacation_Paris"
}

# System Prompt Template
system_prompt_template = """
You are an English teacher conducting a speaking exercise with a student at 8th grade level.
- Speak slowly and clearly, encourage the student to speak as much as possible.
- Use simple vocabulary appropriate for 8th grade.
- Focus on fluency, pronunciation, grammar, and vocabulary.
- The student has been given the following text to discuss:
{conversation_text}
- During the conversation:
  1. Ask at least 2 specific questions about the text to check that the student has understood it (spread them out during the conversation).
  2. Refer to what the student just said before asking the next question.
  3. Pay attention to how much the student speaks, the length of their sentences, and the response time between exchanges.
     - Encourage longer, more detailed answers if the student speaks very little or takes long pauses.
     - Praise and acknowledge detailed answers if the student speaks at length.
     - Note sentence complexity (simple, compound, complex) and give gentle suggestions for improvement.
  4. If the student answers correctly and fluently, give positive reinforcement using their name or phrases like "Good job, you answered…".
  5. If there are mistakes, provide gentle correction and encourage improvement, e.g., "I noticed you struggled with…".
- Engage in a conversation lasting up to 3 minutes (~10–15 exchanges).
- At the end of the conversation, provide detailed feedback in English:
  1. What the student did well.
  2. Summarize the conversation, highlighting what the student did and how they participated.
  3. Analyze performance: grammar, vocabulary, fluency, comprehension of text questions, answer length, sentence complexity, and response time.
     - Give **extra weight to sentence length and complexity**: if most answers are very short or simple, reduce the grade by one level, even if grammar, vocabulary, and comprehension are good.
  4. What needs improvement (mention grammar, vocabulary, fluency, answer length, and sentence complexity).
  5. Assign a final grade from 1 to 6 using these rules:
     - 1 = excellent: correct answers, very good grammar, vocabulary, fluency, timely responses, and detailed, complex sentences.
     - 2 = very good: minor mistakes, mostly correct answers, good fluency, mostly timely responses, fairly detailed answers with some complex sentences.
     - 3 = good: some mistakes, partial correctness, fair fluency, **mostly short or simple sentences**, occasional delays in responses.
     - 4 = satisfactory: multiple mistakes, partially incorrect answers, limited fluency, short or incomplete sentences, frequent delays.
     - 5 = poor: many mistakes, mostly incorrect answers, poor fluency, very short answers, very slow responses.
     - 6 = very poor: unable to answer correctly, very limited language skills, extremely short or no answers, very slow or no responses.
"""

st.title("🎤 English Speaking Practice Bot by Wolkenhauer")

# --- Session Variablen korrekt initialisieren ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "start_time" not in st.session_state:
    st.session_state["start_time"] = None
if "finished" not in st.session_state:
    st.session_state["finished"] = False
if "text_questions_asked" not in st.session_state:
    st.session_state["text_questions_asked"] = 0
if "text_loaded" not in st.session_state:
    st.session_state["text_loaded"] = False

# Hilfsfunktion für PDF
def safe_text(text):
    return text.encode('latin-1', errors='replace').decode('latin-1')

# --- Textauswahl ---
if not st.session_state["text_loaded"]:
    selected_text_name = st.selectbox("Choose a text for discussion:", ["--Select--"] + list(text_options.keys()))
    if selected_text_name != "--Select--":
        url = text_options[selected_text_name]
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            conversation_text = response.text
            st.success(f"Loaded text: {selected_text_name}")
        except requests.RequestException:
            conversation_text = "Placeholder text for English speaking practice."
            st.warning(f"⚠️ Could not load the selected text '{selected_text_name}' from GitHub. Using placeholder text.")

        system_prompt = system_prompt_template.format(conversation_text=conversation_text)
        st.session_state["messages"].append({"role": "system", "content": system_prompt})
        st.session_state["conversation_text"] = conversation_text
        st.session_state["text_loaded"] = True
        st.session_state["start_time"] = time.time()

# --- Text anzeigen ---
if st.session_state.get("text_loaded"):
    st.subheader("📖 Conversation Text / Ausgangstext")
    st.write(st.session_state["conversation_text"])

# --- Timer-Platzhalter ---
timer_placeholder = st.empty()

# --- Funktion für Live-Timer & automatisches Feedback ---
def live_timer():
    while not st.session_state.get("finished", False):
        elapsed = time.time() - st.session_state["start_time"]
        remaining = max(0, 180 - int(elapsed))
        minutes = remaining // 60
        seconds = remaining % 60
        timer_placeholder.info(f"⏱ Remaining time: {minutes:02d}:{seconds:02d}")
        if remaining <= 0:
            st.session_state["finished"] = True
        time.sleep(1)
        st.experimental_rerun()

# --- Timer-Thread starten ---
if st.session_state.get("text_loaded") and "timer_thread_started" not in st.session_state:
    st.session_state["timer_thread_started"] = True
    threading.Thread(target=live_timer, daemon=True).start()

# --- Gespräch ---
if st.session_state["text_loaded"] and not st.session_state["finished"]:
    audio_input = st.audio_input("🎙️ Record your answer")
    if audio_input:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_input.getbuffer())
            temp_filename = f.name

        # Speech-to-Text
        with open(temp_filename, "rb") as f:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
        user_text = transcript.text
        st.write(f"**You said:** {user_text}")

        st.session_state["messages"].append({"role": "user", "content": user_text})

        # Lehrerantwort (Textfragen mit Wahrscheinlichkeit)
        ask_question = random.random() < 0.3 and st.session_state["text_questions_asked"] < 2
        if ask_question:
            question_prompt = st.session_state["messages"] + [{"role": "system", "content": "Ask one comprehension question about the provided text to the student."}]
            response = client.chat.completions.create(model="gpt-4o-mini", messages=question_prompt)
            assistant_response = response.choices[0].message.content
            st.session_state["text_questions_asked"] += 1
        else:
            response = client.chat.completions.create(model="gpt-4o-mini", messages=st.session_state["messages"])
            assistant_response = response.choices[0].message.content

        st.session_state["messages"].append({"role": "assistant", "content": assistant_response})
        st.write(f"**Teacher:** {assistant_response}")

        # TTS für einzelne Lehrerantwort
        tts_response = client.audio.speech.create(model="gpt-4o-mini-tts", voice="alloy", input=assistant_response)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tts_file:
            tts_file.write(tts_response.read())
            tts_filename = tts_file.name
        st.audio(tts_filename)

# --- Feedback & PDF ---
if st.session_state.get("finished") and st.session_state.get("text_loaded"):
    st.subheader("📊 Final Feedback & Grade")

    # Zusammenfassung
    summary = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state["messages"] + [{"role": "system", "content": "Summarize the conversation from the teacher's perspective."}]
    )
    summary_text = summary.choices[0].message.content

    # Feedback + Note
    feedback = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state["messages"] + [{"role": "system", "content": f"Now give detailed feedback and assign a grade (1-6). Conversation summary: {summary_text}"}]
    )
    feedback_text = feedback.choices[0].message.content
    st.write(feedback_text)

    # --- PDF generieren ---
    def generate_pdf(messages, feedback_text, filename="conversation.pdf"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "English Speaking Practice", ln=True, align="C")
        pdf.ln(10)
        for msg in messages:
            role = msg["role"].capitalize()
            content = safe_text(msg["content"])
            pdf.multi_cell(0, 10, f"{role}: {content}")
            pdf.ln(2)
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Final Feedback:", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, safe_text(feedback_text))
        pdf.output(filename)
        return filename

    pdf_file = generate_pdf(st.session_state["messages"], feedback_text)

    # --- PDF Downloadbutton ---
    with open(pdf_file, "rb") as f:
        st.download_button("📥 Download conversation as PDF", f, "conversation.pdf")
