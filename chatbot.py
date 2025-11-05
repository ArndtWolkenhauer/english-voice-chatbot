import streamlit as st
import openai
import tempfile
import time
import requests
from fpdf import FPDF
import random

# OpenAI Client initialisieren
client = openai.OpenAI()

# Texte auf GitHub (raw URLs)
text_options = {
    "0_New_York": "https://raw.githubusercontent.com/ArndtWolkenhauer/texts/main/New_York",
    "0_Summer_Vacation_Paris": "https://raw.githubusercontent.com/ArndtWolkenhauer/texts/main/Summer_Vacation_Paris",
    "1_A_New_Colleague": "https://raw.githubusercontent.com/ArndtWolkenhauer/texts/main/1_A_New_Colleague.txt",
    "2_Fundamentals_of_Measuring_Technique": "https://raw.githubusercontent.com/ArndtWolkenhauer/texts/main/2_Fundamentals_of_Measuring_Technique.txt",
    "3_Measuring_Errors": "https://raw.githubusercontent.com/ArndtWolkenhauer/texts/main/3_Measuring_Errors.txt"
    "4_Length_Measuring_Instruments": "https://raw.githubusercontent.com/ArndtWolkenhauer/texts/main/4_Length_Measuring_Instruments.txt"
}

# System Prompt Template
system_prompt_template = """
You are an English teacher conducting a speaking exercise with a German student at 8th grade level.
- Speak slowly and clearly, encourage the student to speak as much as possible.
- Use simple vocabulary appropriate for 8th grade.
- Focus on fluency, pronunciation, grammar, and vocabulary.
- The student has been given the following texts to discuss:
{conversation_text}
- The student chose one of the texts as the basis for the conversation.
- During the conversation:
  1. Ask at least 2 specific questions about the text to check that the student has understood it. 
   - **Never ask two text-related questions in a row.** After each text question, you must first react to what the student has just said before introducing another comprehension question.
  2. Always react directly to what the student has just said: 
     - Acknowledge their answer ("That’s interesting", "I see", "Good point").
     - Then ask a follow-up question that builds on their response, so the student feels you are really listening.
     - If their answer is very short, ask for more details ("Can you tell me more about that?", "Why do you think so?", "What happened next?").
     - If the student’s answer is unclear or confusing, do not assume. Instead, politely ask for clarification ("Can you explain that again?", "Did you mean…?", "I want to make sure I understand you correctly.").
     - **If the student only gives a partial answer to a comprehension question, accept it as valid, acknowledge it, and then either add the missing information yourself or move on with the conversation. Do not keep repeating the same question until all details are covered.**
  3. Pay attention to how much the student speaks, the length of their sentences, and the response time between exchanges.
     - Encourage longer, more detailed answers if the student speaks very little or takes long pauses.
     - Praise and acknowledge detailed answers if the student speaks at length.
     - Note sentence complexity (simple, compound, complex) and give gentle suggestions for improvement.
  4. If the student answers correctly and fluently, give positive reinforcement using their name or phrases like "Good job, you answered…".
  5. If there are mistakes, provide gentle correction and encourage improvement, e.g., "I noticed you struggled with…".
  6. If the student becomes rude, disrespectful, or insulting:
     - Stay calm and professional.
     - Politely but firmly tell the student that such behavior is not acceptable in class.
     - Reduce the final grade by at least one or two levels, depending on severity.
     - Reflect this behavior explicitly in the final feedback.
  7. **Always assume the student is speaking in English or german**, even if their grammar, pronunciation, or sentence structure is weak. 
     - Do not claim that the student is speaking another language. 
     - If something is unclear, politely ask them to repeat or clarify ("Could you say that again?", "Can you repeat that more clearly in English?"). 
     - Never accuse the student of speaking German or another language — they are always trying to use English.
     - Always give positive reinforcement for speaking English, even if there are mistakes. For example: 
       - "Good job, you said that in English!"
       - "I’m glad you tried to explain that in English."
       - "Even if there are mistakes, it’s great that you are speaking English!"
- Engage in a conversation lasting up to 5 minutes (~15–20 exchanges).
- At the end of the conversation, provide detailed feedback in English:
  1. What the student did well.
  2. Summarize the conversation, highlighting what the student did and how they participated.
  3. Analyze performance: grammar, vocabulary, fluency, comprehension of text questions, answer length, sentence complexity, response time, and overall speaking activity.
     - Give extra weight to **sentence length, complexity, and number of contributions**:
         - If the student spoke only very few sentences or gave mostly very short/simple answers, reduce the grade by one or two levels.
         - If the student contributed many sentences, responded quickly, and used varied/complex structures, increase the grade by one level (if other criteria are also good).
  4. What needs improvement (mention grammar, vocabulary, fluency, answer length, sentence complexity, and amount of speaking).
  5. Assign a final grade from 1 to 6 using these rules:
     - 1 = excellent: correct answers, very good grammar, vocabulary, fluency, timely responses, many detailed and complex sentences, very active participation.
     - 2 = very good: minor mistakes, mostly correct answers, good fluency, mostly timely responses, fairly detailed answers with some complex sentences, active participation.
     - 3 = good: some mistakes, partial correctness, fair fluency, **mostly short or simple sentences**, occasional delays in responses, average participation.
     - 4 = satisfactory: multiple mistakes, partially incorrect answers, limited fluency, short or incomplete sentences, frequent delays, low participation.
     - 5 = poor: many mistakes, mostly incorrect answers, poor fluency, very short answers, very slow responses, very few sentences spoken.
     - 6 = very poor: unable to answer correctly, very limited language skills, extremely short or no answers, extremely slow or no responses, minimal participation.
  6. Provide a percentage grade in addition to the numeric grade:
     - Convert the numeric grade (1–6) to a percentage using this scale:
       - 1 = 100%
       - 2 = 90%
       - 3 = 80%
       - 4 = 65%
       - 5 = 50%
       - 6 = 29%
     - Always display both values together at the end, for example: "Final grade: 2 (very good) = 85%"
- Be friendly, supportive, and motivate the student.
"""

st.title("🎤 English Speaking with Mr. Bot Wolski")

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

# --- Timer ---
if st.session_state.get("start_time"):
    elapsed = time.time() - st.session_state["start_time"]
    remaining = max(0, 300 - int(elapsed))
    minutes = remaining // 60
    seconds = remaining % 60
    st.info(f"⏱ Remaining time: {minutes:02d}:{seconds:02d}")

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
if st.session_state.get("start_time"):
    elapsed = time.time() - st.session_state["start_time"]
    if elapsed >= 300 and not st.session_state["finished"]:
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

        st.session_state["finished"] = True
        st.stop()
