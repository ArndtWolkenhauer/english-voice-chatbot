import streamlit as st
import openai
import tempfile
import time

# OpenAI Client initialisieren
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

st.title("🎤 English Speaking Practice Bot")

# Session-Variablen initialisieren
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": system_prompt}]
if "start_time" not in st.session_state:
    st.session_state["start_time"] = time.time()
if "finished" not in st.session_state:
    st.session_state["finished"] = False

# Timer prüfen
elapsed = time.time() - st.session_state["start_time"]

if elapsed >=
