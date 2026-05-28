# FIT Orchestrator - Uputstvo za pokretanje

## 1. Instalacija potrebnih biblioteka
Pokrenite sljedeću komandu u terminalu unutar foldera projekta:
pip install streamlit langgraph langchain-groq chromadb sentence-transformers

## 2. Postavljanje API ključeva (Obavezno)
U korijenu projekta kreirajte datoteku pod nazivom `.env` i u nju unesite vaše API ključeve:
GROQ_API_KEY=vaš_groq_api_key_ovdje
TAVILY_API_KEY=vaš_tavily_api_key_ovdje

## 3. Pokretanje aplikacije
Nakon što ste instalirali biblioteke i podesili ključeve, pokrenite interfejs komandom:
streamlit run app.py