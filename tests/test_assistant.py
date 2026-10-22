from app.ai.assistant import ProcedureAssistant, split_markdown
from app.config import settings


def _assistant(**kwargs) -> ProcedureAssistant:
    return ProcedureAssistant.from_directory(settings.knowledge_dir, **kwargs)


def test_split_markdown_respects_max_size():
    content = "\n\n".join(f"Paragraphe numéro {i} " + "x" * 100 for i in range(20))
    chunks = split_markdown("doc", content, max_chars=300)
    assert len(chunks) > 1
    assert all(len(chunk.text) <= 300 for chunk in chunks)


def test_search_finds_the_relevant_procedure():
    hits = _assistant().search("Le groupe électrogène ne démarre pas, que faire ?")
    assert hits
    assert hits[0][0].document == "panne-groupe-electrogene"


def test_unrelated_question_returns_no_result():
    result = _assistant().answer("Quelle est la meilleure recette de gâteau au chocolat ?")
    assert result["mode"] == "aucun_resultat"
    assert result["sources"] == []


def test_llm_answer_is_used_when_available(monkeypatch):
    assistant = _assistant(use_llm=True)
    monkeypatch.setattr(assistant, "_generate", lambda question, hits: "Réponse générée.")
    result = assistant.answer("Que faire si le groupe électrogène ne démarre pas ?")
    assert result["mode"] == "generatif"
    assert result["answer"] == "Réponse générée."


def test_falls_back_to_extract_when_llm_fails(monkeypatch):
    assistant = _assistant(use_llm=True)
    monkeypatch.setattr(assistant, "_generate", lambda question, hits: None)
    result = assistant.answer("Que faire si le groupe électrogène ne démarre pas ?")
    assert result["mode"] == "extractif"
    assert "groupe électrogène" in result["answer"]


def test_ask_endpoint_returns_sources(client, agent_headers):
    response = client.post(
        "/assistant/ask",
        json={"question": "Quelle est la fréquence de maintenance d'un onduleur ?"},
        headers=agent_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "extractif"
    assert body["sources"][0]["document"] == "maintenance-onduleur"


def test_ask_endpoint_requires_authentication(client):
    response = client.post("/assistant/ask", json={"question": "Comment tester un onduleur ?"})
    assert response.status_code == 401
