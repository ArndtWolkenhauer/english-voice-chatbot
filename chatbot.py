import streamlit as st
import openai
import tempfile
import time
from fpdf import FPDF

# OpenAI Client initialisieren
client = openai.OpenAI()

# System Prompt Template
system_prompt_template = """
You are an English teacher conducting a speaking exercise with a student at 8th grade level.
- Speak slowly and clearly, encourage the student to speak as much as possible.
- Use simple vocabulary appropriate for 8th grade.
- Focus on fluency, pronunciation, grammar, and vocabulary.
- The student will first choose a topic for the conversation. 
- The student has been given the following text to discuss:
{conversation_text}
- During the conversation:
  1. Ask at least 2 specific questions about the text to check that the student has understood it (spread them out during the conversation).
  2. If the student answers correctly and fluently, give positive reinforcement.
  3. If there are mistakes, provide gentle correction and encourage improvement.
  4. Refer to what the student just said before asking the next question.
- Engage in a conversation lasting up to 3 minutes (~10–15 exchanges).
- At the end of the conversation, provide detailed feedback in English:
  1. What the student did well.
  2. What needs improvement (mention grammar, vocabulary, fluency, and answers to the text questions).
  3. Assign a final grade from 1 to 6 using these rules:
     - 1 = excellent: student answered text questions correctly, with very good grammar, vocabulary, and fluency.
     - 2 = very good: minor mistakes, answers mostly correct, good fluency.
     - 3 = good: some mistakes, partial correctness, fair fluency.
     - 4 = satisfactory: multiple mistakes, partially incorrect answers, limited fluency.
     - 5 = poor: many mistakes, mostly incorrect answers, poor fluency.
     - 6 = very poor: unable to answer correctly, very limited language skills.
- Be friendly, supportive, and motivate the student.
"""

# Beispieltext
conversation_text = """
'A great summer vacation
I just returned from the greatest summer vacation! It was so fantastic, I never wanted it to end. I spent eight days in Paris, France. My best friends, Henry and Steve, went with me. We had a beautiful hotel room in the Latin Quarter, and it wasn’t even expensive. We had a balcony with a wonderful view.

We visited many famous tourist places. My favorite was the Louvre, a well-known museum. I was always interested in art, so that was a special treat for me. The museum is so huge, you could spend weeks there. Henry got tired walking around the museum and said “Enough! I need to take a break and rest.”

We took lots of breaks and sat in cafes along the river Seine. The French food we ate was delicious. The wines were tasty, too. Steve’s favorite part of the vacation was the hotel breakfast. He said he would be happy if he could eat croissants like those forever. We had so much fun that we’re already talking about our next vacation!'
"""

st.title("🎤 English Speaking Practice Bot by Wolkenhauer")

# Session Variablen
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "start_time" not in st.session_state:
    st.session_state["start_time"] = None
if "finished" not in st.session_state:
    st.session_state["finished"] = False
if "topic_set" not in st.session_state:
    st.session_state["topic_set"] = False
if "text_questions_asked" not in st.session_state:
    st.session_state["text_questions_asked"] = 0

# Hilfsfunktion für PDF
def safe_text(text):
    return text.encode('latin-1', errors='replace').decode('latin-1')

# Text anzeigen
st.subheader("📖 Conversation Text / Ausgangstext")
st.write(conversation_text)

# Thema wählen
if not st.session_state["topic_set"]:
    topic = st.text_input("Enter a topic for your conversation:")
    if topic:
        system_prompt = system_prompt_template.format(conversation_text=conversation_text)
        system_prompt += f"\nThe student wants to talk about: {topic}"
        st.session_state["messages"].append({"role": "system", "content": system_prompt})
        st.session_state["topic_set"] = True
        st.session_state["start_time"] = time.time()
        st.success(f"Topic set: {topic}")

# Timer
if st.session_state.get("start_time"):
    elapsed = time.time() - st.session_state["start_time"]
    remaining = max(0, 180 - int(elapsed))
    minutes = remaining // 60
    seconds = remaining % 60
    st.info(f"⏱ Remaining time: {minutes:02d}:{seconds:02d}")

# Gespräch
if st.session_state["topic_set"] and not st.session_state["finished"]:
    audio_input = st.audio_input("🎙️ Record your answer")
    
    if audio_input:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_input.getbuffer())
            temp_filename = f.name

        # Speech-to-Text
        with open(temp_filename, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        user_text = transcript.text
        st.write(f"**You said:** {user_text}")

        # Speichern
        st.session_state["messages"].append({"role": "user", "content": user_text})

        # Lehrerantwort (mit Textfragen)
        if st.session_state["text_questions_asked"] < 2:
            question_prompt = st.session_state["messages"] + [
                {"role": "system", "content": "Ask one comprehension question about the provided text to the student."}
            ]
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=question_prompt
            )
            assistant_response = response.choices[0].message.content
            st.session_state["text_questions_asked"] += 1
        else:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state["messages"]
            )
            assistant_response = response.choices[0].message.content

        st.session_state["messages"].append({"role": "assistant", "content": assistant_response})
        st.write(f"**Teacher:** {assistant_response}")

        # Einzelne TTS-Ausgabe nur zur Kontrolle
        tts_response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=assistant_response
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tts_file:
            tts_file.write(tts_response.read())
            tts_filename = tts_file.name
        st.audio(tts_filename)

# Am Ende: Feedback, PDF + Gesamte MP3
if st.session_state.get("start_time"):
    elapsed = time.time() - st.session_state["start_time"]
    if elapsed >= 180 and not st.session_state["finished"]:
        st.subheader("📊 Final Feedback & Grade")
        feedback = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state["messages"] + [
                {"role": "system", "content": "Now, as the English teacher, summarize the conversation and give final feedback with a grade (1–6)."}
            ]
        )
        feedback_text = feedback.choices[0].message.content
        st.write(feedback_text)

        # PDF speichern
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
        with open(pdf_file, "rb") as f:
            st.download_button("📥 Download conversation as PDF", f, "conversation.pdf")

        # Gesamte Unterhaltung als MP3
        full_dialog = ""
        for msg in st.session_state["messages"]:
            if msg["role"] == "user":
                full_dialog += f"Student: {msg['content']}\n"
            elif msg["role"] == "assistant":
                full_dialog += f"Teacher: {msg['content']}\n"

        tts_full = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=full_dialog
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(tts_full.read())
            full_mp3 = f.name

        with open(full_mp3, "rb") as f:
            st.download_button("🎧 Download full conversation as MP3", f, "conversation.mp3")

        st.session_state["finished"] = True
        st.stop()
