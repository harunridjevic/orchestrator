import os
import json
import time
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import operator

load_dotenv()

# ─────────────────────────────────────────────
# LLM & TOOLS
# ─────────────────────────────────────────────
def get_llm(temperature: float = 0.3, model_name: str = "llama-3.1-8b-instant") -> ChatGroq:
    """Inicijalizira Groq LLM s mogućnošću odabira modela."""
    return ChatGroq(
        model=model_name,
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=temperature,
    )

def safe_llm_invoke(llm: ChatGroq, messages: list, retries: int = 4, delay: float = 5.0):
    """LLM poziv s poboljšanom retry logikom za rate limit greške (HTTP 429)."""
    last_error = None
    for attempt in range(retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            if "rate" in error_str or "429" in error_str:
                # Eksponencijalni backoff: 5s, 10s, 20s, 40s
                wait = delay * (2 ** attempt)
                print(f"[Rate Limit] Čekam {wait}s prije ponovnog pokušaja ({attempt + 1}/{retries})...")
                time.sleep(wait)
            else:
                print(f"[Greška] {e}. Pokušavam ponovo...")
                time.sleep(delay)
                
    raise RuntimeError(f"LLM poziv nije uspio nakon {retries} pokušaja. Zadnja greška: {last_error}")

search_tool = TavilySearchResults(
    max_results=5,
    api_key=os.getenv("TAVILY_API_KEY"),
)

# ─────────────────────────────────────────────
# VEKTORSKA MEMORIJA (ChromaDB)
# ─────────────────────────────────────────────
MEMORY_FILE = "agent_memory.json"
CHROMA_DIR  = "./chroma_memory"

def _get_chroma_collection():
    """Inicijalizira ChromaDB kolekciju s lokalnim embedding modelom."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        client = chromadb.PersistentClient(path=CHROMA_DIR)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        collection = client.get_or_create_collection(
            name="research_memory",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"}
        )
        return collection
    except Exception:
        return None

def find_related_memories_vector(topic: str, n_results: int = 3) -> list:
    """
    Semantička pretraga memorije putem vektorskih embeddings.
    Vraća najsrodnije prethodne sesije rangirane po kosinusnoj sličnosti.
    """
    collection = _get_chroma_collection()
    if collection is None:
        return _find_related_memories_fallback(topic)

    try:
        count = collection.count()
        if count == 0:
            return []

        results = collection.query(
            query_texts=[topic],
            n_results=min(n_results, count),
            include=["documents", "metadatas", "distances"]
        )

        related = []
        for i, doc in enumerate(results["documents"][0]):
            distance = results["distances"][0][i]
            similarity = 1.0 - distance  # cosine distance → similarity
            if similarity > 0.25:        # prag relevantnosti
                meta = results["metadatas"][0][i]
                related.append({
                    "topic": meta.get("topic", ""),
                    "key_findings": meta.get("key_findings", ""),
                    "queries_used": json.loads(meta.get("queries_used", "[]")),
                    "timestamp": meta.get("timestamp", ""),
                    "similarity": round(similarity, 3)
                })

        related.sort(key=lambda x: x["similarity"], reverse=True)
        return related

    except Exception:
        return _find_related_memories_fallback(topic)

def _find_related_memories_fallback(topic: str) -> list:
    """Keyword fallback ako ChromaDB nije dostupan."""
    memory = _load_json_memory()
    topic_words = set(topic.lower().split())
    related = []
    for past in memory.get("researched_topics", []):
        past_words = set(past["topic"].lower().split())
        overlap = len(topic_words & past_words)
        if overlap >= 1:
            related.append({**past, "similarity": overlap / max(len(topic_words), 1)})
    related.sort(key=lambda x: x["similarity"], reverse=True)
    return related[:3]

def save_memory_vector(topic: str, queries: list, findings: str, timestamp: str):
    """Sprema novu sesiju u ChromaDB kao vektor."""
    collection = _get_chroma_collection()
    if collection is None:
        return

    doc_id = hashlib.md5(f"{topic}{timestamp}".encode()).hexdigest()[:12]
    document = f"{topic}. {findings[:300]}"

    collection.upsert(
        ids=[doc_id],
        documents=[document],
        metadatas=[{
            "topic": topic,
            "key_findings": findings[:500],
            "queries_used": json.dumps(queries),
            "timestamp": timestamp,
        }]
    )

# ─────────────────────────────────────────────
# JSON MEMORIJA (statistika i log)
# ─────────────────────────────────────────────
def _load_json_memory() -> dict:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "researched_topics": [],
        "query_patterns": {},
        "total_researches": 0,
        "learning_log": []
    }

def _save_json_memory(memory: dict):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def update_memory_after_research(topic: str, queries: list, findings: str):
    """Ažurira obje memorije: ChromaDB (vektori) + JSON (statistika)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 1. Vektorska memorija
    save_memory_vector(topic, queries, findings, timestamp)

    # 2. JSON statistika
    memory = _load_json_memory()
    memory["total_researches"] += 1
    memory["researched_topics"].append({
        "topic": topic,
        "timestamp": timestamp,
        "queries_used": queries,
        "key_findings": findings[:500],
    })
    memory["researched_topics"] = memory["researched_topics"][-20:]

    domain = topic.split()[0].lower()
    memory["query_patterns"].setdefault(domain, [])
    memory["query_patterns"][domain].extend(queries)

    memory["learning_log"].append({
        "timestamp": timestamp,
        "event": f"Naučio o temi: '{topic}' — {len(queries)} upita"
    })
    memory["learning_log"] = memory["learning_log"][-50:]

    _save_json_memory(memory)

def get_memory_stats() -> dict:
    memory = _load_json_memory()
    collection = _get_chroma_collection()
    vector_count = collection.count() if collection else 0
    return {
        "total_researches": memory.get("total_researches", 0),
        "topics_count": len(memory.get("researched_topics", [])),
        "vector_memories": vector_count,
        "recent_topics": [t["topic"] for t in memory.get("researched_topics", [])[-5:]],
        "learning_log": memory.get("learning_log", [])[-5:],
        "domains_learned": list(memory.get("query_patterns", {}).keys())
    }


# ─────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────
class ResearchState(TypedDict):
    topic: str
    search_queries: List[str]
    search_results: List[dict]
    academic_analysis: str
    fact_check: str
    fact_check_done: str  # Osigurano mapiranje za stanja
    final_report: str
    messages: Annotated[List, operator.add]
    current_step: str
    orchestrator_reasoning: str
    related_memories: List[dict]
    memory_context: str
    total_researches_done: int
    reflection_score: int
    reflection_feedback: str
    reflection_attempts: int


# ─────────────────────────────────────────────
# AGENT 1: ORCHESTRATOR
# ─────────────────────────────────────────────
def orchestrator_agent(state: ResearchState) -> ResearchState:
    # Koristimo lakši model za Orchestrator kako bismo izbjegli rate limit
    llm = get_llm(temperature=0.3, model_name="llama-3.1-8b-instant")
    topic = state["topic"]

    # Semantička pretraga memorije
    related = find_related_memories_vector(topic)

    memory_context = ""
    if related:
        memory_context = "PRETHODNO ISTRAŽENE SEMANTIČKI SLIČNE TEME:\n"
        for r in related:
            sim_pct = int(r.get("similarity", 0) * 100)
            memory_context += f"- Tema: '{r['topic']}' (sličnost: {sim_pct}%, istraživano: {r['timestamp']})\n"
            memory_context += f"  Korišteni upiti: {', '.join(r.get('queries_used', []))}\n"
            memory_context += f"  Ključni nalazi: {r.get('key_findings', '')[:200]}\n\n"

    # Faza 1: Razmišljanje
    reasoning_response = safe_llm_invoke(llm, [
        SystemMessage(content="Ti si ekspertni istraživački orchestrator koji objašnjava svoju strategiju."),
        HumanMessage(content=f"""Ti si Orchestrator Agent. Tema: {topic}

{memory_context if memory_context else "Nema prethodnih sličnih istraživanja u semantičkoj memoriji."}

Opiši strategiju u 3-4 rečenice: zašto si odabrao određene upite, koje aspekte pokriva svaki upit, 
i kako semantički slične prethodne teme (ako postoje) utječu na tvoj pristup.""")
    ])
    orchestrator_reasoning = reasoning_response.content

    # Faza 2: Generisanje upita
    query_response = safe_llm_invoke(llm, [
        SystemMessage(content="Vrati SAMO JSON niz stringova, bez ikakvog drugog teksta."),
        HumanMessage(content=f"""Generiši 4 precizna upita za pretraživanje za temu: {topic}

{memory_context if memory_context else ""}

Pravila:
- Ako postoje slične teme u memoriji, generiši upite koji pokrivaju NOVE aspekte
- Vrati SAMO JSON niz: ["upit 1", "upit 2", "upit 3", "upit 4"]""")
    ])

    import re
    raw = query_response.content.strip()
    match = re.search(r'\[.*?\]', raw, re.DOTALL)
    queries = json.loads(match.group()) if match else [
        topic, f"{topic} analiza", f"{topic} primjena", f"{topic} izazovi"
    ]

    memory = _load_json_memory()
    return {
        **state,
        "search_queries": queries,
        "current_step": "orchestrator_done",
        "orchestrator_reasoning": orchestrator_reasoning,
        "related_memories": related,
        "memory_context": memory_context,
        "total_researches_done": memory.get("total_researches", 0),
        "reflection_attempts": 0,
        "messages": [AIMessage(content=f"🎯 Orchestrator: {len(queries)} upita, {len(related)} semantički srodnih tema pronađeno.")]
    }


# ─────────────────────────────────────────────
# AGENT 2: WEB SEARCH
# ─────────────────────────────────────────────
def web_search_agent(state: ResearchState) -> ResearchState:
    queries = state["search_queries"]
    all_results = []

    for query in queries:
        for attempt in range(3):
            try:
                results = search_tool.invoke(query)
                for r in results:
                    url = r.get("url", "")
                    content = r.get("content", "")
                    if url and content:
                        all_results.append({
                            "query": query,
                            "url": url,
                            "content": content[:800],
                        })
                break
            except Exception as e:
                if attempt == 2:
                    all_results.append({
                        "query": query,
                        "url": "",
                        "content": f"Greška pretrage za '{query}': {str(e)[:100]}"
                    })
                time.sleep(1.5)

    return {
        **state,
        "search_results": all_results,
        "current_step": "web_search_done",
        "messages": [AIMessage(content=f"🔍 Web Search: {len(all_results)} rezultata iz {len(queries)} upita.")]
    }


# ─────────────────────────────────────────────
# AGENT 3: ACADEMIC ANALYSIS
# ─────────────────────────────────────────────
def academic_agent(state: ResearchState) -> ResearchState:
    # Ovdje i dalje koristimo 70b model za dublju analizu
    llm = get_llm(temperature=0.2)
    topic = state["topic"]
    results = state["search_results"]
    memory_context = state.get("memory_context", "")
    reflection_feedback = state.get("reflection_feedback", "")

    context = "\n\n".join([
        f"Izvor: {r['url']}\n{r['content']}"
        for r in results[:8] if r.get("content")
    ])

    memory_instruction = ""
    if memory_context:
        memory_instruction = f"""
ZNANJE IZ SEMANTIČKE MEMORIJE:
{memory_context}
Koristi ovo da: (1) izbjegneš ponavljanje poznatih zaključaka, (2) istakneš NOVE nalaze, 
(3) uspoređuješ s prethodnim istraživanjima.
"""

    reflection_instruction = ""
    if reflection_feedback:
        reflection_instruction = f"""
POVRATNA INFORMACIJA IZ SELF-REFLECTION PETLJE:
{reflection_feedback}
Poboljšaj analizu uzimajući u obzir ove primjedbe.
"""

    response = safe_llm_invoke(llm, [
        SystemMessage(content=f"""Ti si akademski istraživački analitičar s pristupom semantičkoj memoriji.
{memory_instruction}
{reflection_instruction}
Napiši temeljitu akademsku analizu koja uključuje:
1. Ključne nalaze i teme
2. Različite perspektive
3. Statistički podaci i dokazi
4. Istraživačke praznine
5. Šta je NOVO u odnosu na prethodna istraživanja (ako memorija postoji)"""),
        HumanMessage(content=f"Tema: {topic}\n\nIzvori:\n{context}")
    ])

    return {
        **state,
        "academic_analysis": response.content,
        "current_step": "academic_done",
        "messages": [AIMessage(content="📚 Academic Agent: analiza završena.")]
    }


# ─────────────────────────────────────────────
# AGENT 4: SELF-REFLECTION
# ─────────────────────────────────────────────
def reflection_agent(state: ResearchState) -> ResearchState:
    """
    Agent ocjenjuje kvalitet akademske analize (0-10) i odlučuje
    treba li je poboljšati. Ako score < 7 i attempts < 2, šalje nazad.
    """
    llm = get_llm(temperature=0.1)
    topic = state["topic"]
    analysis = state["academic_analysis"]
    attempts = state.get("reflection_attempts", 0)

    response = safe_llm_invoke(llm, [
        SystemMessage(content="""Ti si kritički recenzent istraživačkih analiza.
Ocijeni analizu i vrati SAMO JSON:
{"score": <0-10>, "feedback": "<konkretne primjedbe>", "strengths": "<što je dobro>"}"""),
        HumanMessage(content=f"""Tema: {topic}

Analiza za ocjenu:
{analysis[:2000]}

Ocijeni po kriterijima:
- Dubina i pokrivenost teme (0-3)
- Kvalitet argumenata i dokaza (0-3)  
- Struktura i jasnoća (0-2)
- Inovativnost i kritičnost (0-2)""")
    ])

    import re
    raw = response.content.strip()
    match = re.search(r'\{.*?\}', raw, re.DOTALL)

    score = 7
    feedback = ""
    if match:
        try:
            parsed = json.loads(match.group())
            score = int(parsed.get("score", 7))
            feedback = parsed.get("feedback", "")
        except Exception:
            pass

    return {
        **state,
        "reflection_score": score,
        "reflection_feedback": feedback,
        "reflection_attempts": attempts + 1,
        "messages": [AIMessage(content=f"🔄 Self-Reflection: ocjena {score}/10. {'Poboljšavam analizu...' if score < 7 and attempts < 2 else 'Analiza prihvaćena.'}")]
    }

def should_retry_analysis(state: ResearchState) -> str:
    """Router: odlučuje da li ponoviti analizu ili nastaviti."""
    score = state.get("reflection_score", 10)
    attempts = state.get("reflection_attempts", 0)
    if score < 7 and attempts < 2:
        return "retry"
    return "continue"


# ─────────────────────────────────────────────
# AGENT 5: FACT CHECK
# ─────────────────────────────────────────────
def fact_check_agent(state: ResearchState) -> ResearchState:
    llm = get_llm(temperature=0.1)
    topic = state["topic"]
    analysis = state["academic_analysis"]
    results = state["search_results"]
    reflection_score = state.get("reflection_score", 0)

    urls = list(set([r["url"] for r in results if r.get("url")]))

    response = safe_llm_invoke(llm, [
        SystemMessage(content="""Ti si specijalist za provjeru činjenica. Pregledaj akademsku analizu i:
1. Identificiraj 4-5 najvažnijih tvrdnji
2. Procijeni razinu pouzdanosti (Visoka/Srednja/Niska) za svaku tvrdnju
3. Označi neprovjerene tvrdnje
4. Ocijeni raznolikost izvora
5. Navedi ukupnu ocjenu pouzdanosti analize (%)
Budi koncizan i strukturiran."""),
        HumanMessage(content=f"Tema: {topic}\n\nAnaliza (Self-Reflection ocjena: {reflection_score}/10):\n{analysis}\n\nIzvori: {urls}")
    ])

    return {
        **state,
        "fact_check": response.content,
        "fact_check_done": "done",
        "current_step": "fact_check_done",
        "messages": [AIMessage(content="✅ Fact Check Agent: validacija završena.")]
    }


# ─────────────────────────────────────────────
# AGENT 6: WRITER
# ─────────────────────────────────────────────
def writer_agent(state: ResearchState) -> ResearchState:
    llm = get_llm(temperature=0.4)
    topic = state["topic"]
    analysis = state["academic_analysis"]
    fact_check = state["fact_check"]
    results = state["search_results"]
    queries = state["search_queries"]
    related_memories = state.get("related_memories", [])
    reflection_score = state.get("reflection_score", 0)
    reflection_attempts = state.get("reflection_attempts", 0)

    sources = list(set([r["url"] for r in results if r.get("url")]))[:6]
    sources_text = "\n".join([f"- {url}" for url in sources])

    memory_note = ""
    if related_memories:
        memory_note = f"\n\nNAPOMENA: Semantička memorija pronašla {len(related_memories)} srodnih tema. Napomeni kako se novi nalazi odnose na prethodno znanje."

    quality_note = f"\n\nKVALITET: Analiza prošla self-reflection ({reflection_score}/10, {reflection_attempts} iteracija)."

    response = safe_llm_invoke(llm, [
        SystemMessage(content=f"""Ti si ekspertni istraživački pisac. Sintetiziraj u sveobuhvatan izvještaj:

# Izvršni Sažetak
(2-3 rečenice pregleda)

# Ključni Nalazi  
(Bullet points najvažnijih otkrića)

# Detaljna Analiza
(3-4 paragrafa)

# Provjera Činjenica
(Pouzdanost ključnih tvrdnji)

# Zaključci i Preporuke
(Praktične implikacije){memory_note}{quality_note}

# Reference
(Navedi izvore)

Piši profesionalno i jasno."""),
        HumanMessage(content=f"Tema: {topic}\n\nAkademska Analiza:\n{analysis}\n\nFact Check:\n{fact_check}\n\nIzvori:\n{sources_text}")
    ])

    final_report = response.content

    # Ažuriraj obje memorije
    update_memory_after_research(topic, queries, analysis[:500] if analysis else "")

    return {
        **state,
        "final_report": final_report,
        "current_step": "complete",
        "messages": [AIMessage(content="📝 Writer: izvještaj kompajliran, memorija ažurirana (ChromaDB + JSON).")]
    }


# ─────────────────────────────────────────────
# BUILD GRAPH
# ─────────────────────────────────────────────
def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("orchestrator",     orchestrator_agent)
    graph.add_node("web_search",       web_search_agent)
    graph.add_node("academic",         academic_agent)
    graph.add_node("reflection",       reflection_agent)
    graph.add_node("fact_check_node",  fact_check_agent)  # Riješen konflikt preimenovanjem čvora
    graph.add_node("writer",           writer_agent)

    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "web_search")
    graph.add_edge("web_search",   "academic")
    graph.add_edge("academic",     "reflection")

    # Uvjetni ruter: retry ili nastavi prema novom imenu čvora
    graph.add_conditional_edges(
        "reflection",
        should_retry_analysis,
        {
            "retry":    "academic",
            "continue": "fact_check_node"
        }
    )

    graph.add_edge("fact_check_node", "writer")
    graph.add_edge("writer",          END)

    return graph.compile()


# ─────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────
def run_research(topic: str) -> dict:
    graph = build_graph()
    initial_state = ResearchState(
        topic=topic,
        search_queries=[],
        search_results=[],
        academic_analysis="",
        fact_check="",
        fact_check_done="start",
        final_report="",
        messages=[HumanMessage(content=f"Tema istraživanja: {topic}")],
        current_step="start",
        orchestrator_reasoning="",
        related_memories=[],
        memory_context="",
        total_researches_done=0,
        reflection_score=0,
        reflection_feedback="",
        reflection_attempts=0,
    )
    return graph.invoke(initial_state)


if __name__ == "__main__":
    result = run_research("vještačka inteligencija u obrazovanju")
    print(result["final_report"])