import streamlit as st
import openai
import tempfile
import time
from fpdf import FPDF

# OpenAI Client initialisieren
client = openai.OpenAI()

# System Prompt: Rolle festlegen
system_prompt_template = """
You are an English teacher conducting a speaking exercise with a student at 8th grade level.
- Speak slowly and clearly, encourage the student to speak as much as possible.
- Use simple vocabulary appropriate for 8th grade.
- Focus on fluency, pronunciation, grammar, and vocabulary.
- The student will first choose a topic for the conversation. 
- The student has been given the following text to discuss:
{conversation_text}
- During the conversation, ask approximately 2 questions about this text to check that the student has understood it.
- Engage in a conversation lasting up to 3 minutes (~10–15 exchanges).
- At the end of the conversation, provide detailed feedback in English:
  1. What the student did well.
  2. What can be improved.
  3. A final grade from 1 to 6 (1 = excellent, 6 = poor).
- Be friendly, supportive, and motivate the student.
"""

# Beispieltext für Gesprächsgrundlage
conversation_text = """
Here is the text you will discuss:
'A great summer vacation
I just returned from the greatest summer vacation! It was so fantastic, I never wanted it to end. I spent eight days in Paris, France. My best friends, Henry and Steve, went with me. We had a beautiful hotel room in the Latin Quarter, and it wasn’t even expensive. We had a balcony with a wonderful view.

We visited many famous tourist places. My favorite was the Louvre, a well-known museum. I was always interested in art, so that was a special treat for me. The museum is so huge, you could spend weeks there. Henry got tired walking around the museum and said “Enough! I need to take a break and rest.”

We took lots of breaks and sat in cafes along the river Seine. The French food we ate was delicious. The wines were tasty, too. Steve’s favorite part of the vacation was the hotel breakfast. He said he would be happy if he could eat croissants like those forever. We had so much fun that we’re already talking about our next vacation!'
"""

st.title("🎤 English Speaking Practice Bot by Wolkenhauer")

# Session-Variablen initialisieren
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "start_time" not in st.session_state:
    st.session_state["start_time"] = None
if "finished" not in st.session_state:
    st.session_state["finished"] = False
if "topic_set" not in st.session_state:
    st.session_state["topic_set"] = False

# Text anzeigen
st.subheader("📖 Conversation Text / Ausgangstext")
st.write(conversation_text)

# Schüler wählt Thema am Anfang
if not st.session_state["topic_set"]:
    topic = st.text_input("Enter a topic for your conversation:")
    if topic:
        system_prompt = system_prompt_template.format(conversation_text=conversation_text)
        system_prompt += f"\nThe student wants to talk about: {topic}"
        st.session_state["messages"].append({"role": "system", "content": system_prompt})
        st.session_state["topic_set"] = True
        st.session_state["start_time"] = time.time()
        st.success(f"Topic set: {topic}")

# Timer prüfen
if st.session_state.get("start_time"):
    elapsed = time.time() - st.session_state["start_time"]
    remaining = max(0, 180 - int(elapsed))  # 3 Minuten = 180 Sekunden
    minutes = remaining // 60
    seconds = remaining % 60
    st.info(f"⏱ Remaining time: {minutes:02d}:{seconds:02d}")

# Audio aufnehmen
if st.session_state["topic_set"] and not st.session_state["finished"]:
    audio_input = st.audio_input("🎙️ Record your answer")
    
    if audio_input:
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

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tts_file:
            tts_file.write(tts_response.read())
            tts_filename = tts_file.name

        st.audio(tts_filename)

# Am Ende der 3 Minuten: Feedback + PDF erzeugen
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

        # PDF erstellen mit Standardfont Helvetica
        def generate_pdf(messages, feedback_text, filename="conversation.pdf"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)

            pdf.cell(0, 10, "English Speaking Practice", ln=True, align="C")
            pdf.ln(10)

            for msg in messages:
                role = msg["role"].capitalize()
                content = msg["content"]
                pdf.multi_cell(0, 10, f"{role}: {content}")
                pdf.ln(2)

            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 10, "Final Feedback:", ln=True)
            pdf.set_font("Helvetica", size=12)
            pdf.multi_cell(0, 10, feedback_text)

            pdf.output(filename)
            return filename

        pdf_file = generate_pdf(st.session_state["messages"], feedback_text)

        if pdf_file:
            # Download-Button
            with open(pdf_file, "rb") as f:
                st.download_button(
                    label="📥 Download conversation as PDF",
                    data=f,
                    file_name="conversation.pdf",
                    mime="application/pdf"
                )

        st.session_state["finished"] = True
        st.stop()
