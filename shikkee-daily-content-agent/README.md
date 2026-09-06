# Shikkee Daily Content Agent

Shikkee's daily news-to-content pipeline: same-day U.S. news in, platform-native
Shikkee copy out, scheduled as a **draft** in Metricool (and WordPress for Blog)
so a human approves from inside those tools, with the full record and its
status logged in Airtable. Airtable is the system of record for content and
status -- it does **not** gate publishing. Metricool's draft state and
WordPress's draft status are the approval checkpoints, with one deliberate,
explicit exception (see [Blog cross-post](#blog-cross-post--founder-repost)).

This repo is the implementation of that pipeline as real, runnable Python. It
is **not** a fully autonomous "figure out the news and post it" black box --
the research + copywriting step is a judgment call best made by an LLM agent
with live web search (that's how this pipeline is actually operated day to
day). What this codebase does is everything mechanical and rule-bound around
that step: validating copy against brand rules, generating avatar video,
scheduling drafts across every channel, and keeping Airtable as an accurate
system of record.

## Why this exists

Manually posting to six channels a day, plus two founder-personal written
tracks, plus Reddit, plus Slack-sourced ideas, while enforcing a dozen hard
constraints (no banned terms, no em dashes, verified tagging only, draft-only
scheduling, avatar rotation, real-asset attachment) does not scale by hand.
This codebase encodes those constraints as code so they can't be silently
skipped on a busy day.

## Architecture

```
shikkee_agent/
  config/
    settings.py       # env-var-backed config (secrets never hardcoded)
    brand_rules.py     # banned terms, em-dash check, campaign facts, brand colors
    avatars.py          # HeyGen persona/voice/approved-look configuration
  clients/               # one thin wrapper per external API
    airtable_client.py
    metricool_client.py
    wordpress_client.py
    heygen_client.py
    slack_client.py
    google_drive_client.py
  pipeline/               # the actual business rules
    validators.py         # pre-publish gate: banned terms / em dashes / tagging
    reconcile.py           # RECONCILE-FIRST rule
    content_bank.py         # RSS Feeds angle bank (stop defaulting to mortgage-rate posts)
    rotation.py              # Tal/Ayala daily rotation, self-correcting off Airtable
    six_channel.py            # IG / X / LinkedIn / GBP / Blog / YouTube
    founder_tracks.py          # Founder Slay + Founder Expert Numbers
    blog_cross_post.py          # Blog Cross-Post & Founder Repost Rule (Parts A & B)
    reddit_track.py               # Tue/Fri, browser-drafted only, account-aging gate
    slack_intake.py                 # #narrative channel intake
  browser/
    playwright_session.py           # persisted-login sessions, never touches a password
  orchestrator.py                    # sequences the steps
scripts/
  run_daily.py                        # entry point (fill in today's copy, then run)
  save_login_session.py                # one-time interactive browser login
tests/
  test_validators.py
  test_rotation.py
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # only needed for the Reddit/Medium/repost tracks
cp .env.example .env          # fill in real API keys/tokens -- .env is gitignored
```

Run the test suite (no external credentials needed -- these test pure logic):

```bash
pytest -q
```

## Daily operation

1. An LLM agent (or a human) does the research pass: check the Airtable RSS
   Feeds bank first (`content_bank.get_best_reviewed_angle`), then fresh
   same-day research if nothing strong is banked. Pick one angle for the
   six-channel pipeline; bank any strong runner-ups.
2. Write platform-native copy for each channel, following the length/tone
   guidance below.
3. Fill in `scripts/run_daily.py` with today's `ChannelCopy` and founder
   scripts, then run it. The script:
   - Reconciles yesterday's/today's Airtable "draft" records against what's
     actually live in Metricool/WordPress (`pipeline.reconcile`).
   - Checks whether the Blog Cross-Post rule's Part A/B should fire
     (`pipeline.blog_cross_post`).
   - Validates every piece of copy (`pipeline.validators.enforce_or_raise`) --
     this **raises** on a banned term or an em dash, it does not silently
     schedule bad copy.
   - Generates the HeyGen video for Instagram/YouTube ONLY, always passing an
     explicit `avatar_id`/`voice_id` (never relying on prompt text alone) and
     always attaching a real Shikkee asset URL. The two founder tracks
     (Founder Slay, Founder Expert Numbers) no longer generate any video at
     all -- see [Founder avatar video discontinued](#founder-avatar-video-discontinued-2026-09-06)
     below.
   - Schedules every post as a Metricool/WordPress **draft**.
   - Logs every piece to Airtable's Content Pipeline table with status
     `"draft"`.
4. Twice a week (Tue -> r/RealEstate, Fri -> r/urbanplanning),
   `pipeline.reddit_track` re-checks the account-aging gate and, if cleared,
   drafts (never submits) a contrarian post via a persisted browser session.
5. Every day, `pipeline.slack_intake` checks `#narrative` for founder-submitted
   ideas and either asks a clarifying question in-thread or drafts additional
   content -- it never fabricates from a link it couldn't fetch.

## Hard constraints (enforced in code, not just documentation)

- **No banned terms**: "prefab", "prefabricated", "modular home/construction"
  never appear in Shikkee's own copy (`config/brand_rules.py`,
  `pipeline/validators.py`).
- **No em dashes**: anywhere, in any channel's copy (same validator). A plain
  hyphen in a numeric range like `10-15%` is fine.
- **Draft-only scheduling**: every `MetricoolClient.create_scheduled_post` call
  forces `draft=True, autoPublish=False` unless a caller deliberately opts out
  (only `blog_cross_post.cross_post_blog_to_five_channels` does, and it says so
  in its docstring).
- **Explicit avatar/voice IDs**: `HeyGenClient.generate_avatar_video` requires
  `avatar_id` and `voice_id` as real parameters, never inferred from prompt
  text, after a real incident where HeyGen substituted the wrong avatar.
- **Real-asset attachment**: every HeyGen call takes `asset_urls` and appends
  the required "use the attached assets in positive scenes..." instruction via
  `HeyGenClient.build_prompt_footer()`.
- **Verified tagging only**: `validators.validate_copy` takes an optional
  `verified_tags` map; anything mapped to `None` (no confirmed real handle) is
  surfaced, not silently guessed at.
- **Never types a password**: `browser/playwright_session.py` only ever loads
  a previously, interactively saved session. If it's expired, the action is
  logged as blocked, not retried with credentials.
- **LinkedIn & X never carry an avatar video** (added 2026-09-06, per Tal's
  explicit instruction -- supersedes the old rule that mirrored the
  Instagram/YouTube video onto X/LinkedIn): across every brand (ShikkeeUSA,
  Tal's Personal, Ayala's Profile), LinkedIn and X posts get either a custom
  static picture or no image at all, never a HeyGen video. In code:
  `six_channel.schedule_six_channel(..., x_linkedin_image_url=...)` only
  attaches media to Instagram/YouTube by default and passes a plain picture
  (or nothing) to X/LinkedIn.
- **Founder avatar video discontinued (2026-09-06)**: per Tal's explicit
  follow-up instruction, `founder_tracks.py` no longer calls HeyGen at all.
  Since the Founder Slay and Founder Expert Numbers tracks post ONLY to
  LinkedIn/X, and those never carried the video anyway (see the rule above),
  there was no reason left to generate one. `run_founder_slay(post_copy,
  theme_letter, hook_summary, custom_image_url=None)` and
  `run_founder_expert_numbers(post_copy, pool, stat_source,
  custom_image_url=None)` now take the finished copy directly and post it as
  text, with an optional custom picture -- no `HeyGenClient` import, no
  avatar/voice ID, no video file. `config/avatars.py`'s `TAL_LEVI` and
  `AYALA_CHRYSLER` personas are kept for historical reference only; `ELLA` is
  the only persona this codebase still generates video for.

## Known operational gotchas

- **WordPress bot protection**: shikkee.com sits behind Cloudways / Cloudflare
  / Wordfence (or Imunify360). The RankMath SEO-meta endpoint in particular has
  been observed returning a bare `403 potentially unsafe operation detected`
  even with valid credentials. `WordPressClient.push_rankmath_meta` does not
  raise on this -- it returns `(False, message)` so the blog draft itself still
  counts as done. If it happens, the fix is on the hosting side (allowlist the
  automation IP / this endpoint), not in this code.
- **Metricool media normalization**: always pass the HeyGen video's
  `captioned_video_url`, never the plain `video_url` (which carries an
  expiring signature and reproducibly fails Metricool's "Failed to normalize
  media" check). `six_channel.py` is the only place this still applies --
  Instagram/YouTube are the only channels that carry video at all now.
- **Campaign facts**: `config/brand_rules.py::CURRENT_CAMPAIGN_FACTS["ship_date"]`
  is **"Ships Christmas 2026"**, confirmed definitive by Tal on 2026-09-06.
  An earlier "September 2026" figure was used in prior runs and briefly
  conflicted with some already-published posts; that conflict is now resolved
  in favor of Christmas 2026 -- don't reintroduce "September 2026".

## What's genuinely NOT automated end-to-end here

- **Research and copywriting** -- deliberately left to whatever agent runs
  `scripts/run_daily.py`, since "read the news and decide what's Shikkee-worthy
  today" isn't a rule you can hardcode.
- **Reddit/Medium/founder-repost browser sessions** -- these need a one-time,
  interactive, human login (`scripts/save_login_session.py`) before the
  scheduled pipeline can use them. There is no supported way to automate that
  first login, by design.
- **Metricool/WordPress selector and endpoint details** in `clients/` are
  written against the documented API shapes as of when this repo was created;
  double-check against current docs (developers.metricool.com,
  developer.wordpress.org/rest-api) before relying on them in production, and
  especially before wiring the commented-out `daily-run` CI job back on.

## License

Private, internal Shikkee tooling. Not licensed for external use.
