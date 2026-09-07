import pytest

from tests.conftest import OTHER_USER, bearer

# Both lists run through the same three functions in app/movie_lists.py, so every
# test below is written once and parametrized over the two paths.
LISTS = ["/favorites", "/watch-later"]

ARRIVAL = {
    "tmdb_id": 329865,
    "title": "Arrival",
    "release_date": "2016-11-11",
    "poster_path": "/arrival.jpg",
    "imdb_id": "tt2543164",
    "imdb_rating": 7.9,
}


# --- 1. The gate: no token, no list -----------------------------------------
@pytest.mark.parametrize("path", LISTS)
@pytest.mark.parametrize("method", ["get", "post", "delete"])
def test_a_saved_list_needs_a_token(client, path, method):
    """Every verb on both lists is refused without an Authorization header."""
    url = path + "/329865" if method == "delete" else path
    body = {"json": ARRIVAL} if method == "post" else {}

    response = getattr(client, method)(url, **body)

    assert response.status_code == 401


# --- 2. Adding a film -------------------------------------------------------
@pytest.mark.parametrize("path", LISTS)
def test_add_then_read_back(authorized_client, path):
    """What the POST stored is what the GET returns."""
    created = authorized_client.post(path, json=ARRIVAL)
    assert created.status_code == 201
    assert created.json() == ARRIVAL

    listed = authorized_client.get(path)
    assert listed.status_code == 200
    assert listed.json() == [ARRIVAL]


# ------------
@pytest.mark.parametrize("path", LISTS)
def test_the_same_film_twice_is_refused(authorized_client, path):
    """The unique (user_id, tmdb_id) pair is what answers 409."""
    authorized_client.post(path, json=ARRIVAL)

    assert authorized_client.post(path, json=ARRIVAL).status_code == 409


# ------------
@pytest.mark.parametrize("path", LISTS)
def test_a_film_without_imdb_data_is_accepted(authorized_client, path):
    """OMDB does not carry every title, and that must not block saving one."""
    unknown = {"tmdb_id": 1, "title": "Unknown", "release_date": None}
    # Only tmdb_id and title are required: everything else has a default.

    response = authorized_client.post(path, json=unknown)

    assert response.status_code == 201
    assert response.json()["imdb_rating"] is None


# --- 3. One user never reads another user's rows ----------------------------
@pytest.mark.parametrize("path", LISTS)
def test_a_list_holds_only_its_owner_rows(authorized_client, other_user, path):
    """The regression test for the leak the public endpoint used to have."""
    authorized_client.post(path, json=ARRIVAL)

    seen_by_other = authorized_client.get(path, headers=bearer(OTHER_USER["email"]))

    assert seen_by_other.status_code == 200
    assert seen_by_other.json() == []


# ------------
@pytest.mark.parametrize("path", LISTS)
def test_one_user_cannot_delete_another_users_row(authorized_client, other_user, path):
    """The delete filters on user_id too, so the row is invisible, not merely unowned."""
    authorized_client.post(path, json=ARRIVAL)
    target = str(ARRIVAL["tmdb_id"])

    refused = authorized_client.delete(
        path + "/" + target, headers=bearer(OTHER_USER["email"])
    )

    assert refused.status_code == 404
    assert authorized_client.get(path).json() == [ARRIVAL]


# --- 4. Removing a film -----------------------------------------------------
@pytest.mark.parametrize("path", LISTS)
def test_delete_empties_the_list(authorized_client, path):
    """204 and no body: there is nothing to add to "the row is gone"."""
    authorized_client.post(path, json=ARRIVAL)

    removed = authorized_client.delete(path + "/" + str(ARRIVAL["tmdb_id"]))

    assert removed.status_code == 204
    assert authorized_client.get(path).json() == []


# ------------
@pytest.mark.parametrize("path", LISTS)
def test_deleting_a_film_that_is_not_there(authorized_client, path):
    """404 and not 204: the caller asked to remove something that never existed."""
    assert authorized_client.delete(path + "/999999").status_code == 404


# --- 5. The two lists are independent ---------------------------------------
def test_the_lists_do_not_share_rows(authorized_client):
    """Two tables, not one with a flag: adding to one leaves the other empty."""
    authorized_client.post("/favorites", json=ARRIVAL)

    assert authorized_client.get("/favorites").json() == [ARRIVAL]
    assert authorized_client.get("/watch-later").json() == []
