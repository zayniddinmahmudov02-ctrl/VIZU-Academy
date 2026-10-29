/** What the quote above a reply shows. Pure (unit-tested in
 *  frontend/tests/unit/reply-preview.test.mjs).
 *
 *  The server sends `reply_to` with every message (author + excerpt built on
 *  the server, or available: false). Polling only re-sends rows that
 *  changed, so a reply would keep an old quote after its original was
 *  edited or removed: if the original is loaded in this window, its current
 *  copy wins; if polling removed it, the quote falls back to "not
 *  available". */

export const EXCERPT_CHARS = 140;

export interface ReplyRef {
  id: string;
  available: boolean;
  sender: { id: string; name: string } | null;
  excerpt: string | null;
}

interface MessageLike {
  id: string;
  body: string | null;
  status: string;
  sender: { id: string; name: string } | null;
}

export interface ResolvedReply {
  id: string;
  available: boolean;
  /** null: deleted account (the caller shows its own label) */
  senderName: string | null;
  excerpt: string | null;
}

export function excerpt(text: string, max = EXCERPT_CHARS): string {
  const line = text.split(/\s+/).filter(Boolean).join(" ");
  const chars = Array.from(line); // count emoji as one character, never cut one in half
  return chars.length <= max ? line : `${chars.slice(0, max - 1).join("").trimEnd()}…`;
}

export function resolveReply(ref: ReplyRef | null | undefined, loaded: ReadonlyMap<string, MessageLike>,
                             removed: ReadonlySet<string>): ResolvedReply | null {
  if (!ref) return null;
  const gone = { id: ref.id, available: false, senderName: null, excerpt: null };
  if (removed.has(ref.id)) return gone;
  const local = loaded.get(ref.id);
  if (local) {
    // same rule as the server: deleted, or no text for this viewer (a hidden one reaches moderators only, with text)
    if (local.body === null || local.status === "deleted") return gone;
    return { id: ref.id, available: true, senderName: local.sender?.name ?? null, excerpt: excerpt(local.body) };
  }
  if (!ref.available) return gone;
  return { id: ref.id, available: true, senderName: ref.sender?.name ?? null, excerpt: ref.excerpt };
}
