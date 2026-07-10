"""
Tests d'acceptance pour la route DELETE /watched/{tmdb_id}.

⚠️ CONTEXTE ENTRETIEN — cette route N'EXISTE PAS encore : c'est la tâche de
live coding (cf. plan-pair-programming §1 / guide-code §5.1).

Les trois tests sont **rouges tant que la route n'est pas écrite** : chacun
s'appuie sur au moins une suppression réussie (204), que seule une vraie route
peut produire. Ils passent au vert dès que le DELETE est implémenté correctement.

  - `test_delete_watched_movie`            → nominal : ajout puis suppression (204).
  - `test_delete_watched_movie_not_found`  → re-supprimer un film déjà retiré → 404.
  - `test_delete_watched_movie_only_owns_it` → 🔒 SÉCURITÉ : B ne peut pas supprimer
    le film de A ; A, si. Vire au ROUGE si le candidat oublie le filtre user_id.

Contrat visé (solution de référence) :
    DELETE /watched/{tmdb_id}
      → 204 si supprimé (filtré par user_id + tmdb_id)
      → 404 si le film n'est pas dans la liste de CE user

Lancer :  ./scripts/test.sh delete
"""

from app.auth import create_access_token

WATCHED_URL = "/watched/"

SAMPLE_MOVIE = {
    "tmdb_id": 550,
    "title": "Fight Club",
    "release_date": "1999-10-15",
    "imdb_id": "tt0137523",
    "imdb_rating": 8.8,
    "personal_rating": 9.0,
}


def _auth_headers(email):
    """En-tête Bearer pour un email donné (réutilise le helper de l'app)."""
    return {"authorization": f"bearer {create_access_token({'user_email': email})}"}


def _register(client, email):
    """Crée un utilisateur valide (mot de passe conforme à la politique de force)."""
    client.post("/users", json={
        "email": email, "password": "Password_1",
        "first_name": "Test", "last_name": "User",
    })


def test_delete_watched_movie(authorized_client, test_user):
    """Cas nominal : on ajoute un film vu, puis on le supprime → 204, liste vide."""
    res = authorized_client.post(WATCHED_URL, json=SAMPLE_MOVIE)
    assert res.status_code == 201

    res = authorized_client.delete(f"/watched/{SAMPLE_MOVIE['tmdb_id']}")
    assert res.status_code == 204

    res = authorized_client.get(WATCHED_URL)
    assert res.status_code == 200
    assert res.json() == []


def test_delete_watched_movie_not_found(authorized_client, test_user):
    """Re-supprimer un film déjà retiré → 404 (et non 500).

    Rouge d'abord : le premier delete exige un 204, donc une route existante —
    ce n'est pas le 404 générique d'une route absente qu'on teste ici.
    """
    authorized_client.post(WATCHED_URL, json=SAMPLE_MOVIE)
    assert authorized_client.delete(f"/watched/{SAMPLE_MOVIE['tmdb_id']}").status_code == 204   # route requise

    res = authorized_client.delete(f"/watched/{SAMPLE_MOVIE['tmdb_id']}")   # désormais absent
    assert res.status_code == 404


def test_delete_watched_movie_only_owns_it(client, test_user):
    """🔒 Sécurité : le user B ne doit PAS pouvoir supprimer le film du user A."""
    # user A (test_user) ajoute un film
    res = client.post(WATCHED_URL, json=SAMPLE_MOVIE, headers=_auth_headers(test_user["email"]))
    assert res.status_code == 201

    # user B tente de supprimer le film de A par tmdb_id → interdit
    _register(client, "userb@gmail.com")
    res = client.delete(f"/watched/{SAMPLE_MOVIE['tmdb_id']}", headers=_auth_headers("userb@gmail.com"))
    assert res.status_code == 404          # pas dans la liste de B

    # le film de A est toujours là
    res = client.get(WATCHED_URL, headers=_auth_headers(test_user["email"]))
    assert res.status_code == 200
    assert len(res.json()) == 1

    # ...et A, lui, PEUT le supprimer → prouve que le 404 de B venait de
    # l'appartenance, pas d'une route absente (rend ce test rouge-d'abord).
    res = client.delete(f"/watched/{SAMPLE_MOVIE['tmdb_id']}", headers=_auth_headers(test_user["email"]))
    assert res.status_code == 204
