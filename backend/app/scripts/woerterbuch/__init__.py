"""Wörterbuch data pipeline: the five CEFR word lists in docs/ (the Telegram
word game's lists: id, German, correct Uzbek answer, two wrong answers) ->
deduplicated dictionary entries, enriched with Wiktionary grammar and
Claude-written examples (all examples needs_review). See build.py."""
