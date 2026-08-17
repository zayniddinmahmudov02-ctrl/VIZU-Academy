import { api } from "@/src/services/api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";

export interface AIGenerateRequest {
  source_text: string;
  level?: string;
  count?: number;
}

export interface AIQuizOptionPreview {
  option_text: string;
  is_correct: boolean;
  match_value: string | null;
}

export interface AIQuizQuestionPreview {
  question: string;
  question_type: string;
  points: number;
  options: AIQuizOptionPreview[];
  correct_text_answer: string | null;
}

export interface AIGrammarQuizPreview {
  questions: AIQuizQuestionPreview[];
}

export interface AIComprehensionOptionPreview {
  option_text: string;
  is_correct: boolean;
}

export interface AIComprehensionQuestionPreview {
  prompt: string;
  options: AIComprehensionOptionPreview[];
}

export interface AILesenPreview {
  reading_text: string;
  questions: AIComprehensionQuestionPreview[];
}

export interface AIHoerenPreview {
  questions: AIComprehensionQuestionPreview[];
}

export interface AIRubricCriterionPreview {
  name: string;
  max_score: number;
}

export interface AISchreibenPreview {
  task_content: string;
  requirements: string;
  rubric_criteria: AIRubricCriterionPreview[];
}

export interface AISprechenPreview {
  task_content: string;
  preparation_instructions: string;
  rubric_criteria: AIRubricCriterionPreview[];
}

// Every endpoint here only ever returns a preview — never writes to the
// database. Turning a preview into real content is the caller's job, via
// the same manual create mutations a human admin already uses.
export async function generateGrammarQuizPreview(data: AIGenerateRequest): Promise<AIGrammarQuizPreview> {
  const response = await api.post<AIGrammarQuizPreview>(`${ADMIN_ENDPOINTS.aiContent}/grammar-quiz/generate`, data);
  return response.data;
}

export async function generateLesenPreview(data: AIGenerateRequest): Promise<AILesenPreview> {
  const response = await api.post<AILesenPreview>(`${ADMIN_ENDPOINTS.aiContent}/lesen/generate`, data);
  return response.data;
}

export async function generateHoerenPreview(data: AIGenerateRequest): Promise<AIHoerenPreview> {
  const response = await api.post<AIHoerenPreview>(`${ADMIN_ENDPOINTS.aiContent}/hoeren/generate`, data);
  return response.data;
}

export async function generateSchreibenPreview(data: AIGenerateRequest): Promise<AISchreibenPreview> {
  const response = await api.post<AISchreibenPreview>(`${ADMIN_ENDPOINTS.aiContent}/schreiben/generate`, data);
  return response.data;
}

export async function generateSprechenPreview(data: AIGenerateRequest): Promise<AISprechenPreview> {
  const response = await api.post<AISprechenPreview>(`${ADMIN_ENDPOINTS.aiContent}/sprechen/generate`, data);
  return response.data;
}
