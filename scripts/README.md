# scripts/ — outillage local WatchList

Wrappers autour du venv du projet (`.venv`, Python 3.14) et de l'infra Docker.
**Tout se lance depuis la racine du projet**, ex. `./scripts/infra.sh start`.

| Script | Rôle | Prérequis |
|---|---|---|
| [`infra.sh`](infra.sh) | Infra locale (PostgreSQL + Redis + serveur mock) | Docker |
| [`run.sh`](run.sh) | Lancer l'API FastAPI (`app.main:my_app`) | infra up |
| [`seed.sh`](seed.sh) | (Re)seed des données de démo — remet l'état initial | infra up + migrations |
| [`mock.sh`](mock.sh) | Serveur mock TMDB/OMDB (pour `GET /movies/` sans clé API) | venv |
| [`test.sh`](test.sh) | Lancer la suite Pytest | Docker (crée `watchlist_test`) |
| [`mock_apis.py`](mock_apis.py) | App FastAPI du mock (lancée **via** `mock.sh`, pas à la main) | — |
| [`docker-compose.yml`](docker-compose.yml) | Définition des conteneurs postgres + redis | — |

---

## 🚀 Parcours type (l'ordre à suivre)

```bash
# 1. Infra (postgres + redis + mock TMDB/OMDB) + migrations
./scripts/infra.sh start
./scripts/infra.sh init

# 2. Données de démo (2 users + leurs films)
./scripts/seed.sh

# 3. Lancer l'API   (GET /movies/ marche sans clé API : mock auto)
./scripts/run.sh dev            # → http://localhost:8000/docs

# 4. Tests
./scripts/test.sh
```

**Comptes de démo** (créés par `seed.sh`, mot de passe commun `Password_1`) :
`alice@watchlist.dev` et `bob@watchlist.dev`.

---

## `infra.sh` — infra locale (point d'entrée unique)

Grammaire flexible **`<cible> <action>`** + raccourcis + commandes.

- **Cibles** : `all` · `postgres` (`pg`) · `redis` · `mock`
- **Actions** : `start` · `stop` · `restart` · `status` · `logs`  (défaut : `status`)

```bash
./scripts/infra.sh start            # démarre postgres + redis   (= all start)
./scripts/infra.sh all restart      # redémarre postgres + redis
./scripts/infra.sh redis logs       # suit les logs de redis seul
./scripts/infra.sh postgres status  # statut de postgres seul
./scripts/infra.sh mock start       # démarre le serveur mock (délègue à mock.sh)
```

`start|stop|restart|status|logs` seuls = raccourcis pour `all <action>`.

**Commandes hors cycle de vie :**

```bash
./scripts/infra.sh init    # migrations Alembic (upgrade head), idempotent
./scripts/infra.sh psql    # psql dans le conteneur postgres
./scripts/infra.sh cli     # redis-cli dans le conteneur redis
./scripts/infra.sh clean   # supprime conteneurs ET volumes (⚠️ efface la base)
./scripts/infra.sh info    # infos de connexion, sans rien démarrer
```

Ports : PostgreSQL `localhost:5442`, Redis `localhost:6379`.

---

## `run.sh` — lancer l'API

```bash
./scripts/run.sh dev       # premier plan, --reload (Ctrl+C pour arrêter)
./scripts/run.sh mock      # comme 'dev' mais force le mode mock (voir plus bas)
./scripts/run.sh start     # arrière-plan
./scripts/run.sh stop      # arrête l'instance d'arrière-plan
./scripts/run.sh status    # statut (défaut)
./scripts/run.sh logs      # suit le log d'arrière-plan
```

API sur `http://localhost:8000` (Swagger : `/docs`).
Variables : `WATCHLIST_PORT` (défaut 8000), `WATCHLIST_MOCK` (`1`/`0`), `WATCHLIST_MOCK_PORT` (défaut 9100).

`run.sh` **ne démarre jamais** le serveur mock (c'est le rôle de l'infra) : il ne fait
que *pointer* l'app vers lui quand le mode mock est actif.

---

## `mock.sh` — serveur mock TMDB/OMDB

Sert des réponses « canned » (même forme que TMDB/OMDB) pour que `GET /movies/`
fonctionne **sans clé API**. Ne modifie pas le code de l'app : `run.sh` redirige
juste `TMDB_URL`/`OMDB_URL` vers ce serveur (variables d'env qui priment sur `.env`).

**Le serveur mock fait partie de l'infra** : `./scripts/infra.sh start` le démarre
(inclus dans `all`). Pour le piloter seul :

```bash
./scripts/infra.sh mock start|stop|status|logs   # (délègue à mock.sh)
./scripts/mock.sh start|stop|status|logs|dev      # équivalent direct
```

Côté app : `./scripts/run.sh dev` l'utilise automatiquement tant que `.env` garde les
clés `CHANGE_ME` ; `./scripts/run.sh mock` force le mode ; `WATCHLIST_MOCK=0` le désactive.

---

## `seed.sh` — données de démo / reset

```bash
./scripts/seed.sh          # vide les 3 tables puis réinsère 2 users + leurs films
```

**Idempotent** : relancer redonne exactement le même état (pratique pour repartir
propre entre deux passages). Écrit dans la base **réelle** `watchlist` (pas
`watchlist_test`). Données : cf. [`seed.py`](seed.py).

---

## `test.sh` — suite Pytest

```bash
./scripts/test.sh                                  # toute la suite (toujours -v)
./scripts/test.sh delete                           # filtre -k "delete"
./scripts/test.sh tests/test_watched.py::test_delete_watched_movie   # un test précis
./scripts/test.sh -k "delete and not owns" -x      # args pytest bruts (1er token = -flag)
```

Crée la base `watchlist_test` si absente. Les tests utilisent un schéma frais à
chaque test (`drop_all`/`create_all`), indépendant des données de `seed.sh`.

---

## Fichiers générés (non versionnés)

`*.pid` / `*.log` (ex. `.watchlist.pid`, `.mock.log`) : PID et logs des instances
d'arrière-plan lancées par `run.sh` / `mock.sh`.
