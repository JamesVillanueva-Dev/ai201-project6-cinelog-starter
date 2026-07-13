# PR Response Doc - CineLog Watchlist Feature

## AI Usage
I used Codex for codebase orientation and verification planning. Before changing code, I had it summarize the responsibilities and patterns in `models.py`, `services/collection_service.py`, and `tests/test_collection.py`, then I verified those summaries directly against the files. I also used Codex to stress-test my Comment 4 and Comment 5 reasoning; the useful counterarguments were that private-by-default better protects user expectations and date-added order better reflects recent intent, so I acknowledged both tradeoffs explicitly. At the end, I used Codex to check the commit history against the conventional commit requirement.

## Comment 1 - Rename
**What I did:** Renamed `save_to_watchlist()` to `add_to_watchlist()` in `services/watchlist_service.py` so the watchlist service matches the existing `add_to_collection()` verb-to-noun convention. Updated the import and call site in `routes/watchlist/watchlist.py`.

**How I verified:** Ran `rg -n "save_to_watchlist|add_to_watchlist" -S` to confirm there were no remaining `save_to_watchlist` references and that the only call sites now use `add_to_watchlist`. Ran `python -m pytest tests/ -v`; all 7 tests passed.

## Comment 2 - Deduplication
**What I did:** Added `AlreadyInWatchlistError` and updated `add_to_watchlist()` to check `WatchlistEntry.query.filter_by(user_id=user_id, film_id=film_id).first()` before creating a new row. This mirrors the `add_to_collection()` duplicate-check pattern. I also updated the watchlist route to return a 409 response for duplicate watchlist adds, matching the collection route's conflict behavior.

**How I verified:** Added `test_add_to_watchlist_duplicate_raises`, which adds the same film twice, confirms `AlreadyInWatchlistError` is raised, and confirms only one `WatchlistEntry` exists. Ran `python -m pytest tests\test_watchlist.py -v`; all 3 watchlist tests passed. Ran `python -m pytest tests/ -v`; all 7 tests passed.

## Comment 3 - Missing test
**What I did:** Expanded `tests/test_watchlist.py` to match the service-test pattern in `tests/test_collection.py`. It now covers the happy path with `test_add_to_watchlist_creates_entry`, duplicate/conflict handling with `test_add_to_watchlist_duplicate_raises`, and nonexistent film IDs with `test_add_to_watchlist_nonexistent_film_raises`.

**How I verified:** Ran `python -m pytest tests\test_watchlist.py -v`; all 3 watchlist tests passed. Ran `python -m pytest tests/ -v`; all 7 tests passed.

## Comment 4 - Default visibility
**My position:** I would keep `public=True` as the default for new watchlist entries.

**Reasoning:** CineLog is framed as a community film tracking app, so the default should support sharing and discovery unless a user chooses otherwise. A public watchlist makes it easier for friends or other community members to see what someone is interested in watching next, which fits the social value of the feature. It also keeps the watchlist consistent with an additive, low-friction save flow: users can quickly save films without making a visibility decision every time.

**Tradeoff acknowledged:** The tradeoff is privacy. Some users may treat a watchlist as personal intent rather than a recommendation list, and a private-by-default model would better protect those expectations. If CineLog later adds per-entry controls in the UI, onboarding, or account-level privacy settings, the default should be revisited. For this version, I think public-by-default is reasonable because it matches the app's community orientation, but the product should make the public behavior clear to users.

## Comment 5 - Sort order
**My position:** I would keep alphabetical ordering for `get_watchlist()` in this version.

**Reasoning:** A watchlist is more like a saved reference list than a viewing history. Users may add films over weeks or months and then come back looking for a specific title; alphabetical order gives them a stable, predictable way to scan the list even before the app has search, filters, or UI controls for sorting. It also avoids making older saved films disappear below newer saves just because the user recently browsed and added several titles.

**Engagement with reviewer's point:** The reviewer's date-added suggestion is valid because recency captures intent: the most recently saved films may be the ones a user is most excited to watch next. I would choose alphabetical for now because the current API exposes one default order and no separate "recently added" view. If usage shows that users treat the watchlist as a queue rather than a lookup list, I would change this to `date_added.desc()` or add an explicit `sort=` query parameter so both behaviors are available.

## Comment 6 - Rebase
**What conflicted:** I ran `git fetch origin` and `git rebase origin/main`. The rebase stopped on an add/add conflict in `.gitignore` because both the branch and `main` had ignore-file changes. The main review conflict was the film ID refactor: the original watchlist branch was written around integer `film_id` values, while `main` had migrated `Film.id` and `CollectionEntry.film_id` to UUID strings.

**How I resolved it:** I resolved `.gitignore` by keeping the combined generated-file ignores, including `.pytest_cache/`, `.venv/`, and `venv/`. Then I restored `WatchlistEntry` in `models.py` with `film_id = db.Column(db.String(36), db.ForeignKey("film.id"), nullable=False)` so watchlist entries now reference UUID film IDs. I added `watchlist_entries` relationships for `User` and `Film`, kept `public=True`, and added a unique constraint on `(user_id, film_id)`. I also updated the watchlist service and route docstrings from integer film IDs to UUID film IDs.

**How I verified no conflict remains:** Ran `python -m pytest tests\test_watchlist.py -v`; all 3 watchlist tests passed. Ran `python -m pytest tests/ -v`; all 7 tests passed. Ran `git log --merges --oneline origin/main..HEAD`; it returned no merge commits.

## PR Description
This PR adds a watchlist feature so users can save films they want to watch later, separate from their watched collection. It adds a `WatchlistEntry` model, watchlist service logic, and `/watchlist/<user_id>` routes for adding and viewing saved films. The add flow now rejects nonexistent film IDs with `FilmNotFoundError` and rejects duplicate saves with a watchlist-specific conflict error.

Design decisions:

- New watchlist entries default to `public=True` because CineLog is a community film tracking app and the feature should support sharing and discovery by default. The privacy tradeoff is real, so the product should make this behavior clear and revisit the default if private watchlists become a stronger user expectation.
- `get_watchlist()` keeps alphabetical ordering for now because the current API exposes one default order and a watchlist often functions as a saved reference list. Date-added ordering is a valid future option, especially if users treat watchlists more like queues.

Manual testing steps:

1. Run `python app.py`.
2. Create or identify a user ID and film UUID in the local database.
3. Send `POST /watchlist/<user_id>/add` with JSON body `{ "film_id": "<film_uuid>" }` and confirm a `201` response with `film_id`, `date_added`, and `public`.
4. Send the same POST again and confirm a `409` duplicate response.
5. Send the POST with `00000000-0000-0000-0000-000000000000` and confirm a `404` film-not-found response.
6. Send `GET /watchlist/<user_id>` and confirm the saved film appears with watchlist metadata.

## Git Log Screenshot

![git log --oneline output](git-log-oneline.png)
