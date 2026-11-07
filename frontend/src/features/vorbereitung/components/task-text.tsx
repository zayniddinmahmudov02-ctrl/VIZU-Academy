// Imported Modelltests store plain text (line breaks matter); content written in the admin editor is HTML.
export function isHtml(value: string): boolean {
  return /<\/?[a-z][^>]*>/i.test(value);
}

export default function TaskText({ value, className = "" }: { value: string; className?: string }) {
  if (isHtml(value)) {
    return <div className={`prose-editor text-text-secondary ${className}`} dangerouslySetInnerHTML={{ __html: value }} />;
  }
  return <div className={`whitespace-pre-line break-words text-text-secondary ${className}`}>{value}</div>;
}
