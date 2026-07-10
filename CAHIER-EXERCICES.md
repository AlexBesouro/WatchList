# Cahier d'exercices — Pair-programming · WatchList

Salut Oleksandr 👋

Bienvenue dans **ton** projet WatchList. On va passer ~50 min ensemble (14h40–15h30) à
coder dessus, en pair-programming. Ce fichier, c'est ta trame : tu as tout sous la main,
tu peux le garder ouvert à côté pendant qu'on avance.

Quelques repères pour être au clair :

- **Format détendu.** Le but, c'est de te voir raisonner et coder sur ton propre code —
  pas de te piéger. Un tâtonnement, une hésitation, c'est normal et attendu.
- **Pense à voix haute.** Ce qui m'intéresse, c'est ton cheminement autant que le résultat.
- **L'IA est autorisée** (comme dans ta vraie vie de dev). Sers-t'en si tu veux ; je regarde
  surtout comment tu la diriges et relis.
- **Tu codes sur mon poste**, avec mon éditeur. Prends les 5 premières minutes pour prendre
  tes marques tranquillement — aucun chrono là-dessus.
- **On ne fera pas forcément tout.** On avisera ensemble selon le temps et l'envie.

---

## 🚀 Pour démarrer (le pratique)

Tout est déjà installé et prêt à tourner. Depuis la racine du projet :

```bash
# 1. Infra (PostgreSQL + Redis + mock TMDB/OMDB)
./scripts/infra.sh start
./scripts/infra.sh init        # migrations Alembic (idempotent, déjà appliquées)

# 2. Données de démo (2 users + leurs films) — idempotent, remet l'état initial
./scripts/seed.sh

# 3. Lancer l'API
./scripts/run.sh dev           # → http://localhost:8000/docs  (Swagger, pour tester à la main)

# 4. Lancer les tests
./scripts/test.sh              # toute la suite
./scripts/test.sh delete       # filtre par mot-clé (-k "delete")
```

👉 **Le Swagger `/docs`** est ton meilleur ami pour essayer une route en live
(créer un user, se logger, appeler un endpoint).

**Comptes de démo** (créés par `seed.sh`, même mot de passe `Password_1`) :
`alice@watchlist.dev` et `bob@watchlist.dev`. Alice a déjà des films « vus » et
« à voir » — pratique pour tester la suppression de l'exercice 1.

**`GET /movies/` sans clé API** : `./scripts/infra.sh start` démarre aussi un mock
TMDB/OMDB local, et l'app détecte automatiquement l'absence de clés réelles — l'endpoint
renvoie donc un catalogue de films réaliste, sans rien de plus à faire.

Tu préfères Postman ? Une collection prête à l'emploi (le token se garde tout
seul après le login) est dans `postman/` — voir `postman/README.md`.

---

## 🗺️ La carte du projet (petit rappel)

C'est ton code, mais un coup d'œil pour te resituer vite :

| Fichier | Rôle |
|---|---|
| `app/main.py` | Assemble l'app, monte les routers |
| `app/config.py` | Réglages lus depuis `.env` |
| `app/database.py` | Connexion SQLAlchemy + dépendance `get_db()` |
| `app/models.py` | Les tables ORM (`users`, watched, to-watch) |
| `app/schemas.py` | Les modèles Pydantic (entrées / sorties HTTP) |
| `app/auth.py` | JWT + dépendance `get_current_user` |
| `app/utils.py` | Hash mot de passe + appels TMDB / OMDB |
| `app/routers/` | Les endpoints (`user`, `login`, `movie_list`, `watched_list`, `to_be_watched`) |
| `tests/` | La suite Pytest (`conftest.py` fournit les fixtures) |
| `alembic/` | Les migrations (schéma de base versionné) |

**Le flux d'une requête authentifiée**, en une ligne :
`client → router → Depends(get_current_user) + Depends(get_db) → models / API → réponse (schema)`

---

## 🔥 Échauffement — le tour du projet

Avant de coder, refais-moi le tour de WatchList à voix haute :

- à quoi sert chaque dossier / couche,
- et le **flux** quand un utilisateur cherche un film, du clic à la réponse.

Rien à écrire ici — c'est juste pour se remettre dedans ensemble.

---

## 🧭 Comment on va s'y prendre

Un seul exercice est vraiment au programme : **l'exercice 1**. On le fait ensemble,
tranquillement, sans chrono.

Les trois autres (robustesse, unicité, tests) sont des **bonus** : on les explore
seulement **si on a le temps et l'envie**. Aucune obligation d'aller au bout de la liste —
on choisit au fil de l'eau, ensemble.

Et si tu bloques ou qu'un truc n'est pas clair, **dis-le** : poser une question, chercher,
t'appuyer sur l'IA, c'est exactement ce qu'on fait au quotidien. 👍

---

## ✏️ Exercice 1 — Ajouter la suppression d'un film « vu » *(le seul au programme)*

Aujourd'hui, dans WatchList, on peut **ajouter** un film à sa liste des « vus »
(`POST /watched/`) et **lister** ses films vus (`GET /watched/`)… mais on ne peut pas
en **retirer** un.

> **Énoncé : ajoute la route qui permet de supprimer un film de la liste des « vus ».**

Vas-y en live, à ta main, en pensant à voix haute.

- 📂 Ça se passe dans `app/routers/watched_list.py`.
- 🧭 Tu peux t'appuyer sur tes routes existantes (`POST` / `GET`) comme modèle.
- 🧪 Teste ton résultat via le Swagger `/docs`.

💡 *Comme toujours quand tu ajoutes une route : code d'abord le scénario qui marche (le
cas normal), puis demande-toi tranquillement **ce qui peut mal se passer** et ce que tu
veux renvoyer dans ces cas-là.*

---

## ✏️ Bonus (optionnel) — Rendre l'affichage des films plus robuste

Dans `GET /movies/`, on va chercher les infos de plusieurs films **en parallèle**
(TMDB + OMDB) via `asyncio.gather` — regarde `app/routers/movie_list.py` (et `app/utils.py`).

> **Énoncé : fais en sorte qu'un film sans note OMDB — parce que le service ne répond pas
> pour lui — s'affiche quand même, sans casser l'affichage des autres films.**

- 📂 `app/routers/movie_list.py` (l'appel `asyncio.gather`).
- 🎯 L'idée : qu'un souci sur **un** film n'entraîne pas la chute de **toute** la requête.
- 🧪 Bonus : comment tu t'y prendrais pour **vérifier** que c'est bien robuste ?

---

## ✏️ Bonus (optionnel) — Corriger l'unicité sur les films *(on en a parlé au call)*

On l'a évoqué ensemble : aujourd'hui **deux utilisateurs différents ne peuvent pas suivre
le même film**, à cause du `unique=True` posé sur `tmdb_id` (et `imdb_id`) dans les modèles.

> **Énoncé : corrige-le proprement, pour que chaque utilisateur puisse avoir le film dans
> SA liste, sans se marcher dessus.**

- 📂 `app/models.py` pour le modèle.
- 🧭 Pense la correction **de bout en bout** : du modèle jusqu'à la base réelle.
- 🗣️ Dis-moi aussi comment tu ajusterais le message d'erreur renvoyé au client.

---

## ✏️ Bonus (optionnel) — Deux petits tests de login

Ton fichier `tests/test_login.py` est vide.

> **Énoncé : écris deux tests — un login qui réussit, et un login avec un mauvais mot de passe.**

- 📂 `tests/test_login.py`.
- 🧰 Jette un œil à `tests/conftest.py` : les fixtures dont tu as besoin y sont déjà.
- ▶️ Lance-les avec `./scripts/test.sh` (ou `./scripts/test.sh login`).
