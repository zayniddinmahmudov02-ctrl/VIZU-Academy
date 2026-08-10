"use client";

import { Plus } from "lucide-react";

import { GapExtension } from "../../lib/gap-extension";
import LesenRichTextEditor from "./lesen-rich-text-editor";

interface Props {
  content: string;
  onChange: (html: string) => void;
  /** Creates a new TaskQuestion row for the gap being inserted and
   * resolves with its 1-based gap index (its sort_order) — the editor
   * only embeds that index in the content; the actual correct/alternative
   * answers live in the TaskQuestion row, edited in the gap list below the
   * editor (see gap-list.tsx), not here. */
  onInsertGap: () => Promise<number>;
}

/** CLOZE_TEXT's content editor — the same rich-text toolbar as any other
 * task, plus one extra command: insert an inline "Lücke" (gap) marker at
 * the cursor. e.g. "Berlin ist die Hauptstadt von [Lücke 1]." */
export default function ClozeTextEditor({ content, onChange, onInsertGap }: Props) {
  return (
    <LesenRichTextEditor
      content={content}
      onChange={onChange}
      extraExtensions={[GapExtension]}
      extraToolbar={(editor) => (
        <button
          type="button"
          onClick={async () => {
            const gapIndex = await onInsertGap();
            editor.chain().focus().insertGap(gapIndex).run();
          }}
          className="flex h-7 items-center gap-1 rounded-md px-2 text-xs font-semibold text-[var(--admin-primary)] transition hover:bg-[var(--admin-primary)]/10"
        >
          <Plus size={13} />
          Lücke einfügen
        </button>
      )}
    />
  );
}
