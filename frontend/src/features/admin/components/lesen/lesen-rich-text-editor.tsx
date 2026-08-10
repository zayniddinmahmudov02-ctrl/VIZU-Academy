"use client";

import { useEffect } from "react";
import { useEditor, EditorContent, type Editor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import ImageExtension from "@tiptap/extension-image";
import LinkExtension from "@tiptap/extension-link";
import Underline from "@tiptap/extension-underline";
import {
  Bold,
  Heading2,
  Image as ImageIcon,
  Italic,
  Link as LinkIcon,
  List,
  ListOrdered,
  Underline as UnderlineIcon,
} from "lucide-react";

import { cn } from "@/lib/utils";

interface Props {
  content: string;
  onChange: (html: string) => void;
  className?: string;
  /** Extra Tiptap extensions layered on top of the base set — used by
   * ClozeTextEditor to add the Gap node without duplicating all the
   * toolbar/styling plumbing here. */
  extraExtensions?: Parameters<typeof useEditor>[0]["extensions"];
  /** Rendered after the built-in toolbar buttons — e.g. "Lücke einfügen". */
  extraToolbar?: (editor: Editor) => React.ReactNode;
}

const TOOLBAR_BUTTON =
  "flex h-7 w-7 items-center justify-center rounded-md text-[var(--admin-text-secondary)] transition hover:bg-white/10 hover:text-[var(--admin-text-primary)] data-[active=true]:bg-[var(--admin-primary)]/20 data-[active=true]:text-[var(--admin-primary)]";

/** A Tiptap-based rich text editor scoped to the Lesen assessment engine
 * (features/admin/components/lesen/*) — deliberately NOT the shared
 * components/admin/rich-text-editor.tsx (a separate, pre-existing,
 * dependency-free contentEditable editor already used by
 * grammar-manager/reading-manager/teil-content-editor with a different
 * value/onChange prop shape). This one exists because CLOZE_TEXT needs a
 * real extensible node model to embed atomic "Lücke" gap markers inline —
 * something execCommand-based contentEditable can't do reliably. Reusing
 * a proper editor framework here, rather than bolting gap support onto
 * the shared editor, keeps both editors' contracts stable for their
 * existing callers. */
export default function LesenRichTextEditor({ content, onChange, className, extraExtensions = [], extraToolbar }: Props) {
  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit.configure({ heading: { levels: [2, 3] } }),
      Underline,
      LinkExtension.configure({ openOnClick: false, autolink: true }),
      ImageExtension,
      ...extraExtensions,
    ],
    content,
    editorProps: {
      attributes: {
        class: "prose-editor min-h-[120px] px-3.5 py-2.5 text-sm text-[var(--admin-text-primary)] outline-none",
      },
    },
    onUpdate: ({ editor }) => onChange(editor.getHTML()),
  });

  useEffect(() => {
    if (!editor) return;
    if (editor.getHTML() === content) return;
    editor.commands.setContent(content, { emitUpdate: false });
  }, [editor, content]);

  if (!editor) return null;

  function addLink() {
    const url = window.prompt("Link-URL:");
    if (!url) return;
    editor!.chain().focus().setLink({ href: url }).run();
  }

  function addImage() {
    const url = window.prompt("Bild-URL:");
    if (!url) return;
    editor!.chain().focus().setImage({ src: url }).run();
  }

  return (
    <div className={cn("overflow-hidden rounded-lg bg-[var(--admin-card)] ring-1 ring-[var(--admin-border-strong)]", className)}>
      <div className="flex flex-wrap items-center gap-0.5 border-b border-[var(--admin-border)] bg-white/[0.02] px-2 py-1.5">
        <button type="button" data-active={editor.isActive("bold")} onClick={() => editor.chain().focus().toggleBold().run()} className={TOOLBAR_BUTTON} aria-label="Fett">
          <Bold size={14} />
        </button>
        <button type="button" data-active={editor.isActive("italic")} onClick={() => editor.chain().focus().toggleItalic().run()} className={TOOLBAR_BUTTON} aria-label="Kursiv">
          <Italic size={14} />
        </button>
        <button type="button" data-active={editor.isActive("underline")} onClick={() => editor.chain().focus().toggleUnderline().run()} className={TOOLBAR_BUTTON} aria-label="Unterstrichen">
          <UnderlineIcon size={14} />
        </button>
        <span className="mx-1 h-4 w-px bg-[var(--admin-border)]" />
        <button type="button" data-active={editor.isActive("heading", { level: 2 })} onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} className={TOOLBAR_BUTTON} aria-label="Überschrift">
          <Heading2 size={14} />
        </button>
        <button type="button" data-active={editor.isActive("bulletList")} onClick={() => editor.chain().focus().toggleBulletList().run()} className={TOOLBAR_BUTTON} aria-label="Liste">
          <List size={14} />
        </button>
        <button type="button" data-active={editor.isActive("orderedList")} onClick={() => editor.chain().focus().toggleOrderedList().run()} className={TOOLBAR_BUTTON} aria-label="Nummerierte Liste">
          <ListOrdered size={14} />
        </button>
        <span className="mx-1 h-4 w-px bg-[var(--admin-border)]" />
        <button type="button" data-active={editor.isActive("link")} onClick={addLink} className={TOOLBAR_BUTTON} aria-label="Link">
          <LinkIcon size={14} />
        </button>
        <button type="button" onClick={addImage} className={TOOLBAR_BUTTON} aria-label="Bild">
          <ImageIcon size={14} />
        </button>
        {extraToolbar && (
          <>
            <span className="mx-1 h-4 w-px bg-[var(--admin-border)]" />
            {extraToolbar(editor)}
          </>
        )}
      </div>

      <EditorContent editor={editor} />
    </div>
  );
}
