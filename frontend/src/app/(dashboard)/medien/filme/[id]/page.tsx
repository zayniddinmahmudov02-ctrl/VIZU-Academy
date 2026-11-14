import FilmWatchClient from "@/features/medien/components/film-watch-client";

export const dynamic = "force-dynamic";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function FilmPage({ params }: Props) {
  const { id } = await params;
  return <FilmWatchClient filmId={id} />;
}