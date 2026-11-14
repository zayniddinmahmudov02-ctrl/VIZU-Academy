import BookDetailClient from "@/features/medien/components/book-detail-client";

export const dynamic = "force-dynamic";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function BookPage({ params }: Props) {
  const { id } = await params;
  return <BookDetailClient bookId={id} />;
}