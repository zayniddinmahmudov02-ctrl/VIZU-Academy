"use client";

import { useEffect, useRef } from "react";
import {
  Bold,
  Heading2,
  Image as ImageIcon,
  Italic,
  List,
  ListOrdered,
  Underline,
} from "lucide-react";

import { cn } from "@/lib/utils";

interface Props {
  value: string;
  onChange: (html: string) => void;
  placeholder?: string;
  className?: string;
}

const TOOLBAR_BUTTONS: {
  command: string;
  icon: typeof Bold;
  label: string;
  value?: string;
}[] = [
  { command: "bold", icon: Bold, label: "Fett" },
  { command: "italic", icon: Italic, label: "Kursiv" },
  { command: "underline", icon: Underline, label: "Unterstrichen" },
  { command: "formatBlock", icon: Heading2, label: "Überschrift", value: "h3" },
  { command: "insertUnorderedList", icon: List, label: "Aufzählung" },
  { command: "insertOrderedList", icon: ListOrdered, label: "Nummerierte Liste" },
];

/** A lightweight, dependency-free rich text editor for lesson content
 * (Lesen paragraphs, Grammar explanations, ...). Built on
 * contentEditable + execCommand rather than a full editor library —
 * sufficient for headings/bold/italic/lists/images without adding a new
 * dependency mid-project; a proper editor (Tiptap/Lexical) is a
 * reasonable future upgrade if richer formatting is needed. */
export default function RichTextEditor({ value, onChange, placeholder, className }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const isFirstRender = useRef(true);

  useEffect(() => {
    if (ref.current && isFirstRender.current) {
      ref.current.innerHTML = value || "";
      isFirstRender.current = false;
    }
  }, [value]);

  function exec(command: string, commandValue?: string) {
    ref.current?.focus();
    document.execCommand(command, false, commandValue);
    if (ref.current) onChange(ref.current.innerHTML);
  }

  function handleInsertImage() {
    const url = window.prompt("Bild-URL einfügen:");
    if (url) exec("insertImage", url);
  }

  return (
    <div className={cn("overflow-hidden rounded-lg ring-1 ring-[var(--admin-border-strong)]", className)}>
      <div className="flex flex-wrap items-center gap-1 border-b border-[var(--admin-border)] bg-white/[0.03] p-1.5">
        {TOOLBAR_BUTTONS.map(({ command, icon: Icon, label, value: cmdValue }) => (
          <button
            key={command + (cmdValue ?? "")}
            type="button"
            title={label}
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => exec(command, cmdValue)}
            className="flex h-8 w-8 items-center justify-center rounded-md text-[var(--admin-text-secondary)] transition hover:bg-white/5 hover:text-[var(--admin-primary)]"
          >
            <Icon size={15} />
          </button>
        ))}
        <button
          type="button"
          title="Bild einfügen"
          onMouseDown={(e) => e.preventDefault()}
          onClick={handleInsertImage}
          className="flex h-8 w-8 items-center justify-center rounded-md text-[var(--admin-text-secondary)] transition hover:bg-white/5 hover:text-[var(--admin-primary)]"
        >
          <ImageIcon size={15} />
        </button>
      </div>

      <div
        ref={ref}
        contentEditable
        suppressContentEditableWarning
        onInput={(e) => onChange(e.currentTarget.innerHTML)}
        data-placeholder={placeholder}
        className={cn(
          "prose-editor min-h-[160px] w-full bg-[var(--admin-card)] px-4 py-3 text-sm text-[var(--admin-text-primary)] outline-none",
          "empty:before:text-[var(--admin-text-muted)] empty:before:content-[attr(data-placeholder)]",
        )}
      />
    </div>
  );
}
