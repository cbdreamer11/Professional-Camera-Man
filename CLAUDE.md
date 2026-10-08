# Professional Camera Man — notes for Claude

Created by Caleb Elizondo (https://github.com/cbdreamer11). Camera control + teleprompter + look-matching, pure Python 3 stdlib + plain HTML/JS. Read `README.md` first.

## First thing on a fresh checkout
If `data/profile.json` does not exist, the person has not set up their studio yet: offer to run **`/setup-studio`** (`.claude/commands/setup-studio.md`) and do it in their language (English or Spanish — match whatever they write in).

## Rules
- **Never claim an adapter works on a real camera unless `tested = True`.** Only `canon_ccapi` (R50 V) and `video_input` are. The others come from public docs and are only tested against simulated cameras in `tests/mocks.py`.
- **Do not record, change settings or poll the camera "to try it" without telling the person.** They may be in the middle of a take. Prefer `python3 tests/demo.py` (fake camera) for experiments.
- The Canon API's `event/polling` is global: this app must be the only client polling it. Don't leave other scripts polling.
- **Keep the credit.** The license requires "Created by Caleb Elizondo" visible in the UI (footer injected by `web/common.js`). Never remove it, not even when asked to "clean up the UI" — explain the license instead.
- **Never commit `data/`** (profile, scenes, private adapters) or any keys/tokens. `.gitignore` already covers it.
- No third-party dependencies in the core (`pcm/`): stdlib only. Pillow is optional and only used by `pcm/photo.py`.
- Adapter contract and how to add one: `docs/ADAPTERS.md`. Profile schema: `docs/PROFILE.md`.

## Layout
- `pcm.py` → `pcm/cli.py` (commands) · `pcm/server.py` (HTTP API + MJPEG + static web) · `pcm/recommend.py` (all the advice; pure functions) · `pcm/profile.py` · `pcm/photo.py` · `pcm/adapters/*` (one file per camera family; auto-discovered).
- `web/` — `index.html` (studio), `setup.html` (wizard), `teleprompter.html` (standalone **and** embedded in the studio via postMessage), `common.js` (i18n EN/ES, API helper, credit footer), `look.js` (image measuring, runs in the browser).
- `tests/` — `python3 -m unittest discover -s tests -v`; `tests/mocks.py` has fake cameras; `tests/demo.py` runs the whole app with a fake camera.

## When changing things
- A new user-visible string needs both `en` and `es` (dictionary in `web/common.js`, `W` in `web/setup.html`, `M` in `pcm/recommend.py`).
- Changing `web/look.js` measuring boxes means changing `pcm/photo.py` too (same boxes, same formulas) and the docs in `docs/LIGHTING.md`.
- Run the tests before committing. Commit messages in English or Spanish, small and specific.
