export type SkillType = "writing" | "speaking";

export interface WritingEvaluationRequest {
  lessonId?: string;
  prompt: string;
  text: string;
  targetLevel?: string;
}

export interface SpeakingEvaluationRequest {
  lessonId?: string;
  prompt: string;
  /** Base64 or uploaded audio reference. */
  audioUrl?: string;
  transcript?: string;
  targetLevel?: string;
}

export interface EvaluationCriterion {
  name: string;
  /** 0–100 */
  score: number;
  comment: string;
}

export interface Correction {
  original: string;
  suggestion: string;
  reason: string;
}

export interface Evaluation {
  /** 0–100 overall */
  score: number;
  /** Estimated CEFR level, e.g. "A2". */
  level: string;
  summary: string;
  criteria: EvaluationCriterion[];
  corrections: Correction[];
}
