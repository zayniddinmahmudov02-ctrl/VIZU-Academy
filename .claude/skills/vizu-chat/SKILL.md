---
name: vizu-chat
description: VIZU Global Chat — messages, replies, edits, read state, moderation (mute/ban/restrictions), word filter, rate limits, chat widget and admin moderation page. Also the boundary to group chats (study groups). Use for any chat feature, bug or chat security question.
---
# VIZU Chat

## Context to load
1. `docs/ai-context/module-registry.md` → "Global Chat" (+ "Authentication" for user/session questions).
2. `docs/global-chat.md` (behaviour) and `docs/audit/global-chat-reply.md` (reply feature) — only the part needed.
3. Source:
   - API: `backend/app/api/global_chat/router.py` (`/global-chat`, `/admin/global-chat`)
   - services: `backend/app/services/global_chat/` — `messages.py` (post, edit, reply, serialize),
     `access.py` (moderator roles), `restrictions.py` (mute/ban), `word_filter.py`
   - model: `backend/app/models/global_chat.py` (5 tables)
   - UI: `frontend/src/features/global-chat/` (`chat-panel.tsx`, `reply-ui.tsx`, `reply-swipe.ts`,
     `reply-preview.ts`, `global-chat-service.ts`, admin `admin-global-chat.tsx`)

## Rules
- Separate from group chat (`study_group_messages`, `services/study_groups/chat.py`): no shared code.
- Order in `messages.post`: restriction (mute/ban → 403 `chat_muted`/`chat_banned`) → reply target valid
  (422 `reply_not_found`) → rate limit → word filter (flags the message + audit `message.flag`, does not
  reject; moderators exempt). Keep the order (tests rely on it). Messages are never hard-deleted.
- Updates arrive by polling, not websockets.
- Moderation actions write `global_chat_moderation_actions` and an audit entry.

## Tests
`backend/tests/test_global_chat.py`, `test_global_chat_reply_migration.py`; frontend unit
`tests/unit/reply-*.test.mjs`; E2E `e2e/tests/global-chat*.spec.ts`.
