# Collection Postman — WatchList

Un seul fichier à importer : [`WatchList.postman_collection.json`](WatchList.postman_collection.json).
Tout est dedans (variables, auth, doc) — pas d'environnement séparé à importer.

## Importer
Postman → **Import** → glisse `WatchList.postman_collection.json`.

## Utiliser
1. Lance l'API : `./scripts/run.sh dev` (et au besoin `./scripts/seed.sh` pour les données de démo).
2. Ouvre **🔐 Auth → Login (Alice)** puis **Send**.
   Le script de test enregistre le JWT dans la variable de collection `accessToken`.
3. Toutes les autres requêtes héritent de l'auth **Bearer `{{accessToken}}`** :
   rien à copier-coller. Rejoue **Login (Bob)** pour changer d'utilisateur courant.

## Comptes de démo (créés par `./scripts/seed.sh`)
| email | mot de passe |
|---|---|
| `alice@watchlist.dev` | `Password_1` |
| `bob@watchlist.dev` | `Password_1` |

## Bon à savoir
- **`DELETE /watched/{tmdb_id}`** = route de l'**exercice 1**, pas encore codée :
  la requête est prête et renverra **204** une fois implémentée (aujourd'hui 404/405).
- **`GET /movies/`** : pas de clé API ? `./scripts/infra.sh start` démarre un mock
  TMDB/OMDB local et l'app l'utilise automatiquement — l'endpoint renvoie un catalogue
  réaliste. Inutile pour les exercices.
- Le token expire après `EXPIRE_TIME` minutes (`.env`) — rejoue un Login si besoin.
