"""
Tests for the watchlist service.
"""

import pytest
from app import create_app, db
from models import User, Film, WatchlistEntry
from services.collection_service import FilmNotFoundError
from services.watchlist_service import (
    add_to_watchlist,
    remove_from_watchlist,
    update_watchlist_visibility,
    AlreadyInWatchlistError,
    NotInWatchlistError,
)


@pytest.fixture
def app():
    """Create an isolated test app with an in-memory database."""
    app = create_app(config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_user(app):
    """A user to use in tests."""
    with app.app_context():
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def sample_film(app):
    """A film to use in tests."""
    with app.app_context():
        film = Film(title="Paddington 2", year=2017, genre="Comedy")
        db.session.add(film)
        db.session.commit()
        return film.id


def test_add_to_watchlist_creates_entry(app, sample_user, sample_film):
    """
    Adding a valid film should create a WatchlistEntry in the database.
    """
    with app.app_context():
        entry = add_to_watchlist(user_id=sample_user, film_id=sample_film)

        assert entry is not None
        assert entry.user_id == sample_user
        assert entry.film_id == sample_film
        assert entry.public is True

        in_db = WatchlistEntry.query.filter_by(
            user_id=sample_user, film_id=sample_film
        ).first()
        assert in_db is not None


def test_add_to_watchlist_duplicate_raises(app, sample_user, sample_film):
    """
    Adding the same film twice should raise AlreadyInWatchlistError,
    not silently create a duplicate entry.
    """
    with app.app_context():
        add_to_watchlist(user_id=sample_user, film_id=sample_film)

        with pytest.raises(AlreadyInWatchlistError):
            add_to_watchlist(user_id=sample_user, film_id=sample_film)

        count = WatchlistEntry.query.filter_by(
            user_id=sample_user, film_id=sample_film
        ).count()
        assert count == 1


def test_add_to_watchlist_nonexistent_film_raises(app, sample_user):
    """
    Adding a film_id that doesn't exist in the database should raise
    FilmNotFoundError, not a database integrity error.
    """
    with app.app_context():
        fake_film_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(FilmNotFoundError):
            add_to_watchlist(user_id=sample_user, film_id=fake_film_id)


def test_remove_from_watchlist_deletes_entry(app, sample_user, sample_film):
    """
    Removing a saved film should delete its WatchlistEntry.
    """
    with app.app_context():
        add_to_watchlist(user_id=sample_user, film_id=sample_film)

        removed = remove_from_watchlist(user_id=sample_user, film_id=sample_film)

        assert removed is True
        entry = WatchlistEntry.query.filter_by(
            user_id=sample_user, film_id=sample_film
        ).first()
        assert entry is None


def test_remove_from_watchlist_missing_entry_raises(app, sample_user, sample_film):
    """
    Removing a film that is not saved should raise NotInWatchlistError.
    """
    with app.app_context():
        with pytest.raises(NotInWatchlistError):
            remove_from_watchlist(user_id=sample_user, film_id=sample_film)


def test_update_watchlist_visibility_makes_entry_private(
    app, sample_user, sample_film
):
    """
    Updating visibility should persist the requested public value.
    """
    with app.app_context():
        add_to_watchlist(user_id=sample_user, film_id=sample_film)

        entry = update_watchlist_visibility(
            user_id=sample_user,
            film_id=sample_film,
            public=False,
        )

        assert entry.public is False
        in_db = WatchlistEntry.query.filter_by(
            user_id=sample_user, film_id=sample_film
        ).first()
        assert in_db.public is False


def test_update_visibility_endpoint_rejects_non_boolean_public(
    app, sample_user, sample_film
):
    """
    The visibility endpoint should only accept true or false for public.
    """
    with app.app_context():
        add_to_watchlist(user_id=sample_user, film_id=sample_film)

    response = app.test_client().patch(
        f"/watchlist/{sample_user}/visibility",
        json={"film_id": sample_film, "public": "false"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "public must be a boolean"


def test_update_visibility_endpoint_updates_public(app, sample_user, sample_film):
    """
    The visibility endpoint should return the updated WatchlistEntry.
    """
    with app.app_context():
        add_to_watchlist(user_id=sample_user, film_id=sample_film)

    response = app.test_client().patch(
        f"/watchlist/{sample_user}/visibility",
        json={"film_id": sample_film, "public": False},
    )

    assert response.status_code == 200
    assert response.get_json()["public"] is False
