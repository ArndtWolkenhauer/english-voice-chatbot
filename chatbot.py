import streamlit as st
import openai
import tempfile
import time

# OpenAI Client initialisieren
client = openai.OpenAI()

# System Prompt: Rolle festlegen
system_prompt_template = """
You are an English teacher conducting a speaking exercise with a student at 8th grade level.
- Speak slowly and clearly, encourage the student to speak as much as possible.
- Use simple vocabulary appropriate for 8th grade.
- Focus on fluency, pronunciation, grammar, and vocabulary.
- The student will first choose a topic for the conversation. 
- Engage in a conversation lasting up to 3 minutes (~10–15 exchanges).
- At the end of the conversation, provide detailed feedback in English:
  1. What the student did well.
  2. What can be improved.
  3. A final grade from 1 to 6 (1 = excellent, 6 = poor).
- Be friendly, supportive, and motivate the student.
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
    st.ses
