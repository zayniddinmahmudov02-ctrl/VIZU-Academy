import { Node, mergeAttributes } from "@tiptap/core";

// A "Lücke" (gap) is an inline atom node embedded directly in a CLOZE_TEXT
// task's rich-text content, e.g. "Berlin ist die Hauptstadt von [Gap 1]."
// It only carries a `gapIndex` (1-based, matching the sort_order of the
// corresponding TaskQuestion row that stores the actual correct/alternative
// answers) — the gap's answer configuration lives in TaskQuestion, not in
// the editor content itself, so editing an answer never requires
// re-serializing the passage HTML.
export interface GapOptions {
  HTMLAttributes: Record<string, unknown>;
}

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    gap: {
      insertGap: (gapIndex: number) => ReturnType;
    };
  }
}

export const GapExtension = Node.create<GapOptions>({
  name: "gap",
  group: "inline",
  inline: true,
  atom: true,
  selectable: true,

  addAttributes() {
    return {
      gapIndex: {
        default: 1,
        parseHTML: (element) => Number(element.getAttribute("data-gap-index")) || 1,
        renderHTML: (attributes) => ({ "data-gap-index": attributes.gapIndex }),
      },
    };
  },

  parseHTML() {
    return [{ tag: "span[data-gap]" }];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "span",
      mergeAttributes(HTMLAttributes, { "data-gap": "true", class: "vizu-gap" }),
      `Lücke ${HTMLAttributes["data-gap-index"]}`,
    ];
  },

  addCommands() {
    return {
      insertGap:
        (gapIndex: number) =>
        ({ chain }) =>
          chain().insertContent({ type: this.name, attrs: { gapIndex } }).run(),
    };
  },
});

/** Counts how many gap nodes exist in a content HTML string, in document
 * order — used to assign the next gap its index and to detect gaps whose
 * TaskQuestion row was deleted (index appears in content but not in the
 * question list, or vice versa) so the admin UI can flag the mismatch. */
export function extractGapIndexesFromHtml(html: string): number[] {
  if (typeof window === "undefined") return [];
  const container = document.createElement("div");
  container.innerHTML = html;
  return Array.from(container.querySelectorAll("[data-gap-index]")).map((el) =>
    Number(el.getAttribute("data-gap-index")),
  );
}
