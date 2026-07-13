# PR Response Doc - CineLog Watchlist Feature

## AI Usage
<!-- Fill in at the end - how you used AI tools during this project -->

## Comment 1 - Rename
**What I did:** Renamed `save_to_watchlist()` to `add_to_watchlist()` in `services/watchlist_service.py` so the watchlist service matches the existing `add_to_collection()` verb-to-noun convention. Updated the import and call site in `routes/watchlist/watchlist.py`.

**How I verified:** Ran `rg -n "save_to_watchlist|add_to_watchlist" -S` to confirm there were no remaining `save_to_watchlist` references and that the only call sites now use `add_to_watchlist`. Ran `python -m pytest tests/ -v`; all 4 existing tests passed.

## Comment 2 - Deduplication
**What I did:** Added `AlreadyInWatchlistError` and updated `add_to_watchlist()` to check `WatchlistEntry.query.filter_by(user_id=user_id, film_id=film_id).first()` before creating a new row. This mirrors the `add_to_collection()` duplicate-check pattern. I also updated the watchlist route to return a 409 response for duplicate watchlist adds, matching the collection route's conflict behavior.

**How I verified:** Ran a small in-memory service check that added the same film twice, confirmed `AlreadyInWatchlistError` was raised, and confirmed only one `WatchlistEntry` existed. Ran `python -m pytest tests/ -v`; all 4 existing tests passed.

## Comment 3 - Missing test
**What I did:** Added `tests/test_watchlist.py` with `test_add_to_watchlist_nonexistent_film_raises`, modeled after `test_add_to_collection_nonexistent_film_raises`. The new test uses the same in-memory app fixture, creates a sample user, passes a fake UUID film ID, and asserts that `add_to_watchlist()` raises `FilmNotFoundError`.

**How I verified:** Ran `python -m pytest tests\test_watchlist.py -v`; the new watchlist test passed. Ran `python -m pytest tests/ -v`; all 5 tests passed.

## Comment 4 - Default visibility
**My position:** I would keep `public=True` as the default for new watchlist entries.

**Reasoning:** CineLog is framed as a community film tracking app, so the default should support sharing and discovery unless a user chooses otherwise. A public watchlist makes it easier for friends or other community members to see what someone is interested in watching next, which fits the social value of the feature. It also keeps the watchlist consistent with an additive, low-friction save flow: users can quickly save films without making a visibility decision every time.

**Tradeoff acknowledged:** The tradeoff is privacy. Some users may treat a watchlist as personal intent rather than a recommendation list, and a private-by-default model would better protect those expectations. If CineLog later adds per-entry controls in the UI, onboarding, or account-level privacy settings, the default should be revisited. For this version, I think public-by-default is reasonable because it matches the app's community orientation, but the product should make the public behavior clear to users.

## Comment 5 - Sort order
**My position:** I would keep alphabetical ordering for `get_watchlist()` in this version.

**Reasoning:** A watchlist is more like a saved reference list than a viewing history. Users may add films over weeks or months and then come back looking for a specific title; alphabetical order gives them a stable, predictable way to scan the list even before the app has search, filters, or UI controls for sorting. It also avoids making older saved films disappear below newer saves just because the user recently browsed and added several titles.

**Engagement with reviewer's point:** The reviewer's date-added suggestion is valid because recency captures intent: the most recently saved films may be the ones a user is most excited to watch next. I would choose alphabetical for now because the current API exposes one default order and no separate "recently added" view. If usage shows that users treat the watchlist as a queue rather than a lookup list, I would change this to `date_added.desc()` or add an explicit `sort=` query parameter so both behaviors are available.

## Comment 6 - Rebase
**What conflicted:**

**How I resolved it:**

**How I verified no conflict remains:**

## PR Description
<!-- Written at the end - feature overview, design decisions, manual testing steps -->
