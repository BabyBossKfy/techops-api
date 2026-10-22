"""Assistant de procédures basé sur le RAG (Retrieval-Augmented Generation).

1. Récupération : les procédures (fichiers Markdown) sont découpées en extraits puis
   indexées avec TF-IDF ; on retient les extraits les plus proches de la question.
2. Génération (optionnelle) : si ASSISTANT_USE_LLM=true, Claude rédige une réponse
   à partir de ces seuls extraits. Sinon, ou en cas d'erreur du service, l'assistant
   renvoie l'extrait le plus pertinent (mode extractif) : le service reste disponible.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Mots vides français, sans accents car TF-IDF retire les accents avant de comparer.
FRENCH_STOP_WORDS = [
    "au", "aux", "avec", "ce", "ces", "cette", "comment", "dans", "de", "des", "doit",
    "du", "elle", "en", "est", "et", "faire", "faut", "il", "je", "la", "le", "les",
    "leur", "mon", "ne", "nous", "on", "ou", "par", "pas", "pour", "quand", "que",
    "quel", "quelle", "quels", "qui", "sa", "se", "ses", "son", "sur", "un", "une", "vous",
]

SYSTEM_PROMPT = (
    "Tu es l'assistant des équipes techniques. Réponds en français, de façon concise et "
    "structurée, uniquement à partir des extraits de procédures fournis. Si les extraits "
    "ne contiennent pas la réponse, dis-le clairement et n'invente rien. Termine en "
    "citant le ou les documents utilisés."
)


@dataclass(frozen=True)
class Chunk:
    document: str
    text: str


def split_markdown(document: str, content: str, max_chars: int = 800) -> list[Chunk]:
    """Découpe un document en extraits d'environ max_chars caractères, par paragraphes."""
    chunks: list[Chunk] = []
    buffer = ""
    for paragraph in (p.strip() for p in content.split("\n\n")):
        if not paragraph:
            continue
        if buffer and len(buffer) + len(paragraph) + 2 > max_chars:
            chunks.append(Chunk(document, buffer))
            buffer = paragraph
        else:
            buffer = f"{buffer}\n\n{paragraph}" if buffer else paragraph
    if buffer:
        chunks.append(Chunk(document, buffer))
    return chunks


class ProcedureAssistant:
    MIN_SCORE = 0.05

    def __init__(
        self,
        chunks: list[Chunk],
        use_llm: bool = False,
        model: str = "claude-opus-5-5",
        top_k: int = 3,
    ) -> None:
        if not chunks:
            raise ValueError("La base de connaissances est vide.")
        self.chunks = chunks
        self.use_llm = use_llm
        self.model = model
        self.top_k = top_k
        self._vectorizer = TfidfVectorizer(
            strip_accents="unicode", lowercase=True, stop_words=FRENCH_STOP_WORDS
        )
        self._matrix = self._vectorizer.fit_transform([chunk.text for chunk in chunks])
        self._client = None

    @classmethod
    def from_directory(cls, directory: Path, **kwargs) -> "ProcedureAssistant":
        chunks: list[Chunk] = []
        for path in sorted(Path(directory).glob("*.md")):
            chunks.extend(split_markdown(path.stem, path.read_text(encoding="utf-8")))
        return cls(chunks, **kwargs)

    def search(self, question: str) -> list[tuple[Chunk, float]]:
        scores = cosine_similarity(self._vectorizer.transform([question]), self._matrix)[0]
        best = scores.argsort()[::-1][: self.top_k]
        return [(self.chunks[i], float(scores[i])) for i in best if scores[i] >= self.MIN_SCORE]

    def answer(self, question: str) -> dict:
        hits = self.search(question)
        if not hits:
            return {
                "answer": "Aucune procédure pertinente n'a été trouvée. Reformulez la question "
                "ou contactez votre superviseur.",
                "mode": "aucun_resultat",
                "sources": [],
            }
        sources = [
            {"document": chunk.document, "extrait": chunk.text[:300], "score": round(score, 3)}
            for chunk, score in hits
        ]
        if self.use_llm:
            generated = self._generate(question, hits)
            if generated is not None:
                return {"answer": generated, "mode": "generatif", "sources": sources}
        return {"answer": hits[0][0].text, "mode": "extractif", "sources": sources}

    def _generate(self, question: str, hits: list[tuple[Chunk, float]]) -> str | None:
        """Rédige la réponse avec Claude. Renvoie None en cas d'échec (repli extractif)."""
        import anthropic

        if self._client is None:
            # Les identifiants sont lus dans l'environnement (ANTHROPIC_API_KEY).
            self._client = anthropic.Anthropic(timeout=30.0, max_retries=2)

        context = "\n\n".join(
            f'<extrait document="{chunk.document}">\n{chunk.text}\n</extrait>'
            for chunk, _ in hits
        )
        try:
            response = self._client.beta.messages.create(
                model=self.model,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                output_config={"effort": "low"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                messages=[{"role": "user", "content": f"{context}\n\nQuestion : {question}"}],
            )
        except anthropic.RateLimitError:
            logger.warning("Assistant IA : limite de débit atteinte, repli extractif.")
            return None
        except anthropic.APIStatusError as exc:
            logger.warning("Assistant IA : erreur HTTP %s, repli extractif.", exc.status_code)
            return None
        except anthropic.APIConnectionError:
            logger.warning("Assistant IA : service injoignable, repli extractif.")
            return None

        if response.stop_reason == "refusal":
            logger.warning("Assistant IA : requête refusée, repli extractif.")
            return None
        text = "".join(block.text for block in response.content if block.type == "text")
        return text.strip() or None
