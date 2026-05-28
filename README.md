# FIT Orchestrator

**FIT Orchestrator** je napredni multi-agentni sistem izgrađen na modularnoj i asinkronoj arhitekturi pomoću programskog jezika Python i radnog okvira **LangGraph**. Sistem koristi usmjereni aciklični graf (DAG) sa kontrolisanim povratnim petljama kako bi omogućio autonomnu pretragu, akademsku analizu, samorefleksiju i verifikaciju činjenica u realnom vremenu.

---

## 🌐 Pokretanje uživo (Live Demo)

Aplikacija je uspješno deployana na cloud infrastrukturu i možete je odmah testirati bez ikakve lokalne konfiguracije na sljedećem linku:

👉 **[fit-orchestrator.streamlit.app](https://fit-orchestrator.streamlit.app/)**

---

# 💻 Lokalno pokretanje projekta

Ukoliko želite pokrenuti projekat lokalno na svom računaru, pratite sljedeće korake:

## 1. Kloniranje repozitorija i pozicioniranje

Otvorite terminal (ili Command Prompt) i pozicionirajte se unutar foldera projekta:

```bash
cd fitcc-agent
```

---

## 2. Instalacija potrebnih biblioteka

Pokrenite sljedeću komandu kako biste instalirali sve potrebne zavisnosti (`dependencies`) navedene u `requirements.txt`:

```bash
pip install -r requirements.txt
```

Alternativno, biblioteke možete instalirati i direktno:

```bash
pip install streamlit langgraph langchain-groq chromadb sentence-transformers python-dotenv
```

---

## 3. Konfiguracija okruženja i API ključeva (Obavezno)

U korijenu projekta kreirajte datoteku pod nazivom `.env` (ili preimenujte postojeći `.env.example` u `.env`) i u nju unesite vaše važeće API ključeve:

```env
GROQ_API_KEY=vas_groq_api_key_ovdje
TAVILY_API_KEY=vas_tavily_api_key_ovdje
```

---

## 4. Pokretanje Streamlit aplikacije

Nakon uspješno instaliranih biblioteka i podešenih ključeva, pokrenite korisnički interfejs komandom:

```bash
streamlit run app.py
```

Aplikacija će se automatski otvoriti u vašem zadanom web pretraživaču na adresi:

```txt
http://localhost:8501
```

---

# 🏗️ Arhitektura sistema i tok podataka (Graph Workflow)

Aplikacija je dizajnirana kao deterministički graf stanja (`StateGraph`) sa sljedećim agentima:

## 🎯 Orchestrator Agent

Prima korisničku temu, analizira semantičku memoriju i generiše optimalne strategije i upite za pretragu.

## 🔍 Web Search Agent

Koristi Tavily API za paralelno prikupljanje najrelevantnijih podataka sa interneta.

## 📚 Academic Agent

Dubinski analizira prikupljene izvore, kontekstualizira ih i kreira strukturiranu akademsku sintezu.

## 🔄 Self-Reflection Agent

Vrši rigoroznu kritičku evaluaciju rada. Ako je ocjena kvaliteta manja od `7/10`, aktivira se povratna petlja i vraća Academic Agenta na doradu (maksimalno 2 iteracije).

## ✅ Fact Check Agent

Validira tvrdnje iz analize, procjenjuje nivo pouzdanosti i računa ukupni procenat tačnosti.

## 📝 Writer Agent

Kompajlira finalni, izvršni izvještaj sa referencama i trajno pohranjuje naučene obrasce.

---

# 🧠 Napredni sistemi memorije

Projekt implementira dvoslojni sistem perzistencije podataka:

## Vektorska memorija (ChromaDB)

Koristi `SentenceTransformers` za pretvaranje prethodnih pretraga u vektorske tekstualne embeddings. Prilikom pokretanja nove teme, sistem vrši semantičku pretragu (kosinusna sličnost) i omogućava agentima da uče iz prošlih istraživanja kako bi izbjegli ponavljanje i otkrili nove uglove.

## Strukturalna memorija (JSON log)

Pohranjuje analitiku, historiju učenja i frekvenciju domena za potrebe statističkog prikaza na Streamlit interfejsu.

---

# 🛠️ Tehnološki stack

* **Jezik:** Python 3.11+
* **Orkestracija agenata:** LangGraph (`StateGraph`)
* **LLM:** Groq API (Llama 3.1 8B / 70B)
* **Pretraga:** Tavily AI Search API
* **Vektorska memorija:** ChromaDB & SentenceTransformers (`all-MiniLM-L6-v2`)
* **Korisnički interfejs:** Streamlit (Reaktivni Cyberpunk Dark UI)
