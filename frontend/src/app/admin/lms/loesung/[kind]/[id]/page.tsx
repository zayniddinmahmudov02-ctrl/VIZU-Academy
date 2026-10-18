import { notFound } from "next/navigation";

import LoesungEditorClient from "@/features/admin/components/loesung/loesung-editor-client";

export const dynamic = "force-dynamic";

export default async function LoesungTaskPage({ params }: { params: Promise<{ kind: string; id: string }> }) {
  const { kind, id } = await params;
  if (kind !== "lesen" && kind !== "hoeren") notFound();
  return <LoesungEditorClient key={`${kind}:${id}`} kind={kind} id={id} />;
}