import LmsLevelClient from "./lms-level-client";

export const dynamic = "force-dynamic";

interface Props {
  params: Promise<{ level: string }>;
}

export default async function LmsLevelPage({ params }: Props) {
  const { level } = await params;
  return <LmsLevelClient level={level} />;
}
