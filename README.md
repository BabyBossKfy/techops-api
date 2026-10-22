# TechOps API

[![CI/CD](https://github.com/BabyBossKfy/techops-api/actions/workflows/ci.yml/badge.svg)](https://github.com/BabyBossKfy/techops-api/actions/workflows/ci.yml)

API de gestion des incidents techniques d'une direction technique, avec authentification JWT, contrôle des accès par rôle et un assistant IA (RAG) qui répond aux questions à partir des procédures de maintenance.

Projet de démonstration conçu pour montrer, sur un cas concret, le cycle complet d'une application métier : conception, développement, tests, conteneurisation et intégration/déploiement continus.

## Ce que montre le projet

| Compétence | Où la voir |
| --- | --- |
| API REST moderne (FastAPI) | `app/routers/` ; documentation interactive sur `/docs` |
| Sécurité des API | JWT signé à durée courte, mots de passe hachés (bcrypt), rôles agent / superviseur / admin, validation stricte des entrées |
| Bases de données | SQLAlchemy 2, PostgreSQL en production, SQLite en local |
| Intégration d'IA | `app/ai/assistant.py` : RAG avec recherche TF-IDF et génération par un modèle de langage (Claude), avec repli automatique |
| Tests | `tests/` : tests unitaires et d'intégration avec pytest, exécutés aussi sur PostgreSQL |
| DevOps | `Dockerfile`, `docker-compose.yml`, pipeline GitHub Actions dans `.github/workflows/ci.yml` |

## Architecture

```
Client (navigateur, application, Postman)
        │  HTTPS + Authorization: Bearer <JWT>
        ▼
┌──────────────────────── FastAPI ────────────────────────┐
│  /auth        inscription, connexion, rôles             │
│  /incidents   création, consultation, statut, suppression│
│  /assistant   questions sur les procédures (RAG)        │
│                                                          │
│  security.py  JWT + bcrypt + contrôle des rôles          │
└──────────────┬──────────────────────────┬───────────────┘
               │                          │
               ▼                          ▼
        PostgreSQL               Assistant IA
     (users, incidents)   1. TF-IDF sur knowledge/*.md
                          2. Claude rédige la réponse (optionnel)
                          3. Repli extractif si le service échoue
```

## Rôles et droits

| Action | Agent | Superviseur | Admin |
| --- | --- | --- | --- |
| Déclarer et consulter des incidents | oui | oui | oui |
| Interroger l'assistant IA | oui | oui | oui |
| Changer le statut d'un incident | non | oui | oui |
| Supprimer un incident | non | non | oui |
| Modifier le rôle d'un utilisateur | non | non | oui |

Toute inscription crée un agent. Le premier administrateur est créé au démarrage à partir des variables `ADMIN_USERNAME` et `ADMIN_PASSWORD`.

## Points d'accès

| Méthode | Route | Description |
| --- | --- | --- |
| POST | `/auth/register` | Créer un compte agent |
| POST | `/auth/login` | Obtenir un jeton JWT (formulaire OAuth2) |
| GET | `/auth/me` | Profil de l'utilisateur connecté |
| PATCH | `/auth/users/{id}/role` | Modifier un rôle (admin) |
| GET | `/incidents` | Lister, avec filtres `status`, `severity` et pagination |
| POST | `/incidents` | Déclarer un incident |
| GET | `/incidents/{id}` | Consulter un incident |
| PATCH | `/incidents/{id}/status` | Changer le statut (superviseur, admin) |
| DELETE | `/incidents/{id}` | Supprimer (admin) |
| POST | `/assistant/ask` | Poser une question sur les procédures |
| GET | `/health` | Vérification de l'état du service |

## Lancer le projet en local (Windows)

Prérequis : Python 3.12 ou plus récent.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Ouvrir ensuite http://localhost:8000/docs pour tester l'API depuis le navigateur. Les variables du fichier `.env` sont lues par docker-compose ; en local sans Docker, définissez-les dans votre terminal, par exemple `$env:ADMIN_USERNAME="admin"`.

## Lancer avec Docker (API + PostgreSQL)

```powershell
copy .env.example .env
docker compose up --build
```

## Tests et qualité

```powershell
ruff check .
pytest --cov=app --cov-report=term-missing
```

Les tests utilisent une base SQLite en mémoire et n'appellent aucun service externe : l'appel au modèle de langage est remplacé par un double de test.

## Pipeline CI/CD

À chaque `push` ou pull request sur `main`, GitHub Actions :

1. vérifie la qualité du code avec ruff ;
2. lance les tests avec mesure de couverture (le pipeline échoue sous 75 %) ;
3. relance les tests sur une vraie base PostgreSQL (tests d'intégration) ;
4. construit l'image Docker ;
5. sur `main` uniquement, publie l'image dans le registre GitHub (GHCR), étiquetée avec le commit pour la traçabilité.

Le déploiement sur un serveur n'est pas inclus : l'étape suivante serait de déployer l'image publiée sur un environnement de test, puis en production après validation manuelle.

## L'assistant IA (RAG)

1. **Indexation** : au démarrage, les procédures de `knowledge/` sont découpées en extraits et vectorisées avec TF-IDF.
2. **Recherche** : la question est comparée aux extraits (similarité cosinus) et les 3 plus proches sont retenus.
3. **Génération** : si `ASSISTANT_USE_LLM=true`, Claude rédige la réponse à partir de ces seuls extraits et cite ses sources.
4. **Repli** : sans modèle de langage, ou si le service est indisponible, limité ou refuse la requête, l'API renvoie l'extrait le plus pertinent. Le service reste toujours disponible.

La réponse indique son `mode` (`generatif`, `extractif` ou `aucun_resultat`) et ses sources, pour que l'utilisateur puisse vérifier.

Les procédures fournies sont fictives et servent uniquement à la démonstration.

## Choix de sécurité

- Jetons JWT signés (HS256), valables 30 minutes par défaut.
- Mots de passe hachés avec bcrypt, jamais stockés en clair.
- Même message d'erreur que l'utilisateur existe ou non, pour ne rien révéler.
- Requêtes SQL paramétrées par l'ORM, ce qui protège contre l'injection SQL.
- Validation de toutes les entrées par Pydantic (types, longueurs, formats).
- Secrets lus dans les variables d'environnement, jamais dans le code ; refus de démarrer en production avec le secret par défaut.
- Conteneur exécuté avec un utilisateur non root.

## Pistes d'amélioration

- Migrations de schéma avec Alembic au lieu de `create_all`.
- Jetons de rafraîchissement et authentification unique (OAuth2 / OpenID Connect avec Keycloak).
- Limitation du débit sur `/auth/login` contre les attaques par force brute.
- Recherche sémantique par embeddings et base vectorielle (pgvector).
- Journalisation structurée et supervision (Prometheus, Grafana).
- Déploiement automatisé sur Kubernetes.
