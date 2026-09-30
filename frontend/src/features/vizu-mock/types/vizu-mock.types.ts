export type VizuMockAttemptStatus = "IN_PROGRESS" | "COMPLETED";

export type VizuMockSkill = "lesen" | "hoeren" | "schreiben" | "sprechen";

export interface VizuMockAttempt {
  id: string;
  status: VizuMockAttemptStatus;
  started_at: string;
  completed_at: string | null;
  // CEFR code per skill, plus the overall result — all null until a
  // future phase wires real evaluation (see backend/app/models/
  // vizu_mock_attempt.py). Framework only, never fabricated client-side.
  lesen_level: string | null;
  hoeren_level: string | null;
  schreiben_level: string | null;
  sprechen_level: string | null;
  overall_level: string | null;
}
