import type { LevelCode } from "./levels";

export interface ExamProvider {
  id: string;
  name: string;
  /** Short descriptor shown under the name. */
  description: string;
  /** CEFR levels this provider is offered for on VIZU. */
  levels: LevelCode[];
  accent: string;
}

/** Number of mock tests available per exam (provider × level). */
export const MOCKS_PER_EXAM = 5;

export const examProviders: ExamProvider[] = [
  {
    id: "goethe",
    name: "Goethe-Zertifikat",
    description: "Goethe-Institut",
    levels: ["A1", "A2", "B1", "B2", "C1"],
    accent: "from-brand-700 to-brand-500",
  },
  {
    id: "telc",
    name: "telc Deutsch",
    description: "The European Language Certificates",
    levels: ["A1", "A2", "B1", "B2", "C1"],
    accent: "from-emerald-600 to-emerald-400",
  },
  {
    id: "osd",
    name: "ÖSD Zertifikat",
    description: "Österreichisches Sprachdiplom",
    levels: ["A1", "A2", "B1", "B2", "C1"],
    accent: "from-warning to-amber-400",
  },
  {
    id: "testdaf",
    name: "TestDaF",
    description: "Test Deutsch als Fremdsprache",
    levels: ["B2", "C1"],
    accent: "from-brand-900 to-brand-700",
  },
];

/** Providers available for a given level. */
export function providersForLevel(level: LevelCode): ExamProvider[] {
  return examProviders.filter((p) => p.levels.includes(level));
}
