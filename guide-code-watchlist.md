# Guide de code — WatchList · companion interviewer

> **Pour toi, avant jeudi.** Objectif : connaître **son** code assez bien pour le piloter en live sans hésiter — savoir où tombe chaque tâche, avoir le corrigé en tête, et garder quelques bugs « en réserve » pour rebondir.
> Repères : `app.main:my_app`, stack **FastAPI + SQLAlchemy 2.0 (sync) + PostgreSQL + Redis + JWT**. Tout est déjà installé/lançable (`.venv`, `scripts/`).
> ⚠️ Ne pas rejouer en « découverte » ce qui a été vu au call du 03/07 : `unique=True` et le cache Redis.

---

## 0. Démarrer & tester en 30 s

```bash
cd github/WatchList
./scripts/infra.sh start     # postgres (5442) + redis (6379)
./scripts/infra.sh init      # migrations Alembic (déjà appliquées, idempotent)
./scripts/run.sh dev         # API → http://localhost:8000/docs
```

**Lancer ses tests** — via le lanceur dédié `scripts/test.sh` (crée la base de test au besoin) :
```bash
./scripts/test.sh                 # toute la suite
./scripts/test.sh delete          # -k "delete" → le(s) test(s) de la route DELETE
./scripts/test.sh tests/test_watched.py::test_delete_watched_movie   # un test précis
```
> `test_user.py` passe (9 tests). `tests/test_watched.py` ajoute l'**acceptance du DELETE** : **rouge par design** tant que la route n'est pas codée, verte une fois faite (cf. §5.1).
Deux pièges **déjà réglés pour toi** (mais bons à connaître — bons signes s'il les repère seul, cf. §6) :
- 🗄️ `conftest.py:12` vise une base **`watchlist_test`** (suffixe `_test`). `create_all` crée les *tables*, pas la *base* → il faut la créer une fois (`docker exec watchlist-postgres createdb -U postgres watchlist_test`). ✅ fait.
- 🔑 **passlib × bcrypt** : sur une machine 2026, `pip` tire `bcrypt 5.x`, **incompatible** avec son `passlib 1.7.4` → **tout hash de mot de passe plante** (« password cannot be longer than 72 bytes »), donc login + création d'user + toutes les routes protégées. Épinglé à **`bcrypt==4.0.1`** dans `requirements.txt`. ✅ fait.

> ⚠️ Sans ce pin, la **création d'utilisateur échouerait en live** → impossible de tester le DELETE/POST protégés. C'est réglé, mais garde-le en tête si tu recrées le venv.

---

## 1. Carte du code (les couches)

| Fichier | Rôle |
|---|---|
| `app/main.py` | Assemble l'app `my_app`, monte les 5 routers, route `GET /` |
| `app/config.py` | `Settings` (pydantic-settings) lues depuis `.env` → singleton `settings` |
| `app/database.py` | Engine SQLAlchemy **sync**, `session_local`, dépendance `get_db()` |
| `app/models.py` | Tables ORM : `users`, `watched movies`, `movies to be watched` |
| `app/schemas.py` | Modèles Pydantic (entrées/sorties HTTP) |
| `app/auth.py` | JWT : `create_access_token`, `verify_token`, dépendance `get_current_user` |
| `app/utils.py` | Hash bcrypt, force du mot de passe, appels async TMDB/OMDB |
| `app/routers/*.py` | Les endpoints (user, login, movie_list, watched_list, to_be_watched) |
| `alembic/` | 6 migrations (schéma de base versionné) |

**Flux d'une requête authentifiée** (ex. `POST /watched/`) :
```
client → router (watched_list.add_watched_movie)
         ├─ Depends(get_current_user) → verify_token(JWT) → charge User en base
         └─ Depends(get_db) → session
       → construit WatchedMovies(**schema) → db.commit() → réponse (schema WatchedMovie)
```

---

## 2. Le modèle de données — `app/models.py`

Trois tables, style SQLAlchemy 2.0 (`Mapped` / `mapped_column`) :

- **`User`** (`users`) — `user_id` PK, `email` unique, `password` (hash), `first_name`, `last_name`, `user_created_at`.
- **`WatchedMovies`** (`"watched movies"`) — `id` PK, `user_id` FK→users (**ON DELETE CASCADE**), `tmdb_id`, `title`, `release_date`, `imdb_id`, `imdb_rating`, `personal_rating`.
- **`ToBeWatched`** (`"movies to be watched"`) — idem sans `personal_rating`.

**Points sensibles à avoir en tête :**
- 🔴 **`unique=True` global** sur `tmdb_id` (`models.py:22` et `:34`) **et** `imdb_id` (`:25` et `:37`). Conséquence : **deux users ne peuvent pas suivre le même film** → le 2ᵉ prend un `IntegrityError` → 409. (cf. §5.3)
- ⚠️ **Noms de tables avec espaces** (`"watched movies"`, `"movies to be watched"`) — ça marche mais oblige à quoter partout ; **habitude** récurrente (pas une coquille). Angle de discussion développé en **§6**.
- ⚠️ `user_created_at` typé `Mapped[datetime]` mais colonne `DATE` — petite incohérence.

---

## 3. L'authentification (flux JWT) — `app/auth.py` + `app/routers/login.py`

- `POST /login/` (`login.py`) : vérifie email + `verify_password` (bcrypt). Renvoie **401 « Invalid credentials »** dans les 2 cas (user inconnu *ou* mauvais mot de passe) → 👍 pas d'énumération d'utilisateurs.
- Le token encode `{"user_email": ...}` (`login.py:17`) + une expiration (`auth.py:19`).
- `get_current_user` (`auth.py:32`) : décode le token, charge le `User` par email → 401 si token invalide, 404 si user absent. C'est **la dépendance à réutiliser** dans toute nouvelle route protégée.

---

## 4. Les endpoints (récap)

| Méthode | Chemin | Auth ? | Fichier | Note |
|---|---|:--:|---|---|
| GET | `/` | — | `main.py` | home |
| POST | `/users/` | — | `user.py:12` | + validation force mot de passe |
| PATCH | `/users/` | ✅ | `user.py:34` | exige **tout** le corps (voir §6) |
| POST | `/login/` | — | `login.py:9` | renvoie le JWT |
| GET | `/movies/` | ❌ | `movie_list.py:19` | **sans auth** + cache Redis + async (voir §6) |
| POST / GET | `/watched/` | ✅ | `watched_list.py` | **pas de DELETE** (voir §5.1) |
| POST / GET | `/to-watch/` | ✅ | `to_be_watched.py` | **pas de DELETE** |

---

## 5. Les tâches de live coding — localisation + corrigé

### 5.1 ⭐ Ajouter `DELETE /watched` — `app/routers/watched_list.py`
**État** : seulement `POST` (`:11`) et `GET` (`:29`). On ajoute un film « vu », on ne peut pas le retirer.

**Corrigé de référence :**
```python
@router.delete("/{tmdb_id}", status_code=204)
def delete_watched_movie(tmdb_id: int, db: Session = Depends(get_db),
                         current_user: models.User = Depends(auth.get_current_user)):
    movie = (db.query(models.WatchedMovies)
             .filter(models.WatchedMovies.user_id == current_user.user_id,   # ← appartenance !
                     models.WatchedMovies.tmdb_id == tmdb_id)
             .first())
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found in your watched list.")
    db.delete(movie)
    db.commit()
```

**Ce qui fait un bon passage :**
| ✅ | 🔴 |
|---|---|
| Filtre par **`user_id` ET `tmdb_id`** (on ne supprime que SES films) | Filtre par `tmdb_id` seul → on peut effacer la ligne d'un autre |
| **404** si absent, **204** en succès | Ne gère que le cas nominal / mauvais code retour |
| Calque le style des routes existantes (`get_current_user`, session) | Repart de zéro |

> 💡 Le point clé à provoquer s'il ne le voit pas : *« et si je passe le tmdb_id d'un film d'un autre user ? »*

> 🧪 **Test d'acceptance prêt** : `./scripts/test.sh delete` → `tests/test_watched.py`. `test_delete_watched_movie` est **rouge** aujourd'hui (route absente), **vert** quand c'est bon. Le fichier contient aussi `test_delete_watched_movie_only_owns_it` (**appartenance** : B ne peut pas supprimer le film de A) — à **révéler** en mode TDD (« rends ce test vert ») **ou** à garder pour toi si tu veux d'abord voir le réflexe `user_id` **spontané**.

### 5.2 Durcir `asyncio.gather` — `app/routers/movie_list.py:74`
**État** : `movie_details = await asyncio.gather(*tasks)`. Si **un seul** `get_movie_details` lève (OMDB muet), **toute** la requête tombe.

**Corrigé de référence :**
```python
movie_details = await asyncio.gather(*tasks, return_exceptions=True)
for i, result in enumerate(movie_details):
    if isinstance(result, Exception):
        film_list[i]["imdb_id"] = None
        film_list[i]["imdb_rating"] = None
    else:
        film_list[i]["imdb_id"], film_list[i]["imdb_rating"] = result
```
**On observe :** isole l'échec sans casser le lot, et **sait retester** (simuler un échec). 
> 🎯 Bonus à glisser : le `try/except RequestException` (`movie_list.py:6,42`) est **mort** — le code utilise **aiohttp**, dont les erreurs sont des `aiohttp.ClientError`, pas des `requests.RequestException`. Excellent test de lucidité s'il le remarque.

### 5.3 Corriger `unique=True` — `app/models.py` (déjà expliqué au call → tâche d'implémentation)
**Corrigé de référence :**
```python
from sqlalchemy import UniqueConstraint

class WatchedMovies(Base):
    __tablename__ = "watched movies"
    __table_args__ = (UniqueConstraint("user_id", "tmdb_id", name="uq_watched_user_tmdb"),)
    ...
    tmdb_id: Mapped[int] = mapped_column(nullable=False)   # ← on retire unique=True
    imdb_id: Mapped[str] = mapped_column(nullable=False)   # ← idem
```
**Réflexes attendus :** contrainte **composite** `(user_id, tmdb_id)` + **retirer** l'unicité de colonne, **penser migration Alembic** (`alembic revision --autogenerate -m "..."` → relire → `upgrade head`), ajuster le message **409**.
> ⚠️ À savoir toi : l'autogenerate peut mal voir les tables à espaces → **relire la migration**. Et des doublons existants bloqueraient la création de la contrainte.

### 5.4 Filet — `tests/test_login.py` (vide, 0 ligne)
`conftest.py` fournit déjà tout : `client`, `test_user`, `authorized_client`, base `_test` recréée à chaque test.
```python
def test_login_success(client, test_user):
    res = client.post("/login/", json={"email": test_user["email"], "password": test_user["password"]})
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"

def test_login_wrong_password(client, test_user):
    res = client.post("/login/", json={"email": test_user["email"], "password": "WrongPass_1"})
    assert res.status_code == 401
```
**On observe :** réutilise les **fixtures** existantes, teste un cas **OK** *et* un cas **d'échec** (401).

---

## 6. Bugs & angles de discussion « en réserve »

À sortir seulement si le courant passe et qu'on veut le pousser un cran plus loin — tous sont dans **son** code :

- 🗣️ **Noms de tables avec espaces** (`models.py:19,31`) — angle de **convention**, neutre et révélateur. C'est **délibéré et systématique** : il a écrit `__tablename__ = "watched movies"`, et ça contamine jusqu'aux noms de contraintes auto-générés (`'movies to be seen_pkey'`, `'..._tmdb_id_key'` dans les migrations).
    - **Pourquoi c'est un souci** : en PostgreSQL un identifiant sans quotes est replié en minuscules et **ne peut pas contenir d'espace** → une espace force le **double-quotage à vie** (`FROM "watched movies"`), casse plein d'outils, et sort de la convention. La norme, c'est `snake_case` : `watched_movies`, `movies_to_be_watched`.
    - **Question à poser** : *« Tes tables s'appellent `"watched movies"` avec une espace — raconte-moi ce choix. Un inconvénient ? Tu la nommerais comment aujourd'hui ? »*
    - **Corrigé** : `__tablename__ = "watched_movies"`. Renommer = **migration Alembic** `op.rename_table("watched movies", "watched_movies")` (⚠️ penser aussi à renommer les contraintes/index qui portent l'ancien nom).

    | ✅ Bon signe | 🔴 Moins bon |
    |---|---|
    | Tique aussitôt, cite `snake_case` + le quotage/outillage, propose un renommage | « Ça marche, donc pas de souci » — ne voit pas le problème |

- 🔴 **`GET /movies/` sans auth ET non filtré par user** (`movie_list.py:20,52`) : il lit `WatchedMovies).all()` (**tous** les users) pour calculer `already_seen`/`watch_later`. → Un film vu par **n'importe qui** apparaît « déjà vu » pour **tout le monde**. Même thème d'appartenance que le DELETE — bon fil rouge.
- ⚠️ **`GET` avec un corps de requête** (`movie_list.py:20`, `params: MovieSearch`) : accepté par FastAPI mais non idiomatique (des proxys/clients ignorent le body d'un GET).
- ⚠️ **PATCH `/users/` exige tout le corps** (`user.py:35`, schéma `CreateUser` où tous les champs sont requis) → ce n'est pas un vrai *partial update*.
- ⚠️ **Redis synchrone dans un endpoint async** (`movie_list.py:14,28,40`) : `red.get/set` bloquent la boucle d'événements (perf).
- 🧹 **Hygiène & dépendances** : `example.txt` (charabia commité), **pas de `requirements.txt`** d'origine, `.env` non fourni. Conséquence concrète, excellent angle : **sans dépendances épinglées**, une appli qui tournait en mars 2025 **ne démarre plus** en 2026 (bcrypt 5.x casse passlib — cf. §0). Bonne question : *« Comment tu garantis qu'un collègue — ou toi dans un an — puisse relancer ce projet à l'identique ? »* → attendu : `requirements.txt`/lockfile, versions figées, voire Docker.

> Rappel : ce sont des **munitions**, pas une checklist à dérouler. On juge sa **façon de raisonner et de réagir**, pas l'exhaustivité.

---

## 7. Ce que tu regardes (rappel express)

| Axe | 🟢 On veut voir |
|---|---|
| Appropriation | Retrouve vite ses marques dans **son** code (même sur ton poste/éditeur) |
| Réutilise ses patterns | Calque les routes/dépendances existantes |
| Cas limites / sécurité | **Appartenance `user_id`** + 404 **spontanés** |
| Pilotage de l'IA | Dirige, **relit**, corrige (l'IA est autorisée) |
| Réaction au feedback | « Bonne prise, je fais comme ça » plutôt que se justifier |
