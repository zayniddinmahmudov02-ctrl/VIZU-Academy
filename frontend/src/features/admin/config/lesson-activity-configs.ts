export type ActivityFieldType = "text" | "textarea" | "number" | "checkbox";

export interface ActivityField {
  key: string;
  label: string;
  type: ActivityFieldType;
  required?: boolean;
  defaultValue?: string | number | boolean;
}

export interface ActivityColumn {
  key: string;
  label: string;
}

export interface ActivityTypeConfig {
  type: string;
  label: string;
  /** Base API path, e.g. "/vocabularies" — list/create hit this path
   *  directly, update/delete append "/{id}". */
  apiBase: string;
  /** Some of this codebase's routers declare their list/create routes
   *  with a trailing slash (`@router.get("/")`), some without
   *  (`@router.get("")`) — get this wrong and every request 307-redirects,
   *  which can silently drop the Authorization header on some setups, so
   *  it's tracked explicitly per resource rather than guessed. */
  trailingSlash: boolean;
  fields: ActivityField[];
  columns: ActivityColumn[];
}

const PUBLISHED_FIELD: ActivityField = { key: "is_published", label: "Published", type: "checkbox", defaultValue: false };
const ORDER_FIELD: ActivityField = { key: "order_index", label: "Order", type: "number", defaultValue: 1 };
const PUBLISHED_COLUMN: ActivityColumn = { key: "is_published", label: "Published" };
const ORDER_COLUMN: ActivityColumn = { key: "order_index", label: "Order" };

export const LESSON_ACTIVITY_CONFIGS: ActivityTypeConfig[] = [
  {
    type: "vocabulary",
    label: "Vocabulary",
    apiBase: "/vocabularies",
    trailingSlash: true,
    fields: [
      { key: "german_word", label: "German word", type: "text", required: true },
      { key: "article", label: "Article (der/die/das)", type: "text" },
      { key: "plural", label: "Plural", type: "text" },
      { key: "translation", label: "Translation", type: "text", required: true },
      { key: "example_sentence", label: "Example sentence", type: "textarea" },
      { key: "example_translation", label: "Example translation", type: "textarea" },
      { key: "audio_url", label: "Audio URL", type: "text" },
      { key: "image_url", label: "Image URL", type: "text" },
      ORDER_FIELD,
      PUBLISHED_FIELD,
    ],
    columns: [
      { key: "german_word", label: "Word" },
      { key: "translation", label: "Translation" },
      ORDER_COLUMN,
      PUBLISHED_COLUMN,
    ],
  },
  {
    type: "grammar",
    label: "Grammar",
    apiBase: "/grammars",
    trailingSlash: false,
    fields: [
      { key: "title", label: "Title", type: "text", required: true },
      { key: "content", label: "Content", type: "textarea", required: true },
      { key: "video_url", label: "Video URL", type: "text" },
      ORDER_FIELD,
      PUBLISHED_FIELD,
    ],
    columns: [{ key: "title", label: "Title" }, ORDER_COLUMN, PUBLISHED_COLUMN],
  },
  {
    type: "reading",
    label: "Reading",
    apiBase: "/readings",
    trailingSlash: true,
    fields: [
      { key: "title", label: "Title", type: "text", required: true },
      { key: "content", label: "Passage text", type: "textarea", required: true },
      ORDER_FIELD,
      PUBLISHED_FIELD,
    ],
    columns: [{ key: "title", label: "Title" }, ORDER_COLUMN, PUBLISHED_COLUMN],
  },
  {
    type: "listening",
    label: "Listening",
    apiBase: "/listenings",
    trailingSlash: false,
    fields: [
      { key: "title", label: "Title", type: "text", required: true },
      { key: "audio_url", label: "Audio URL", type: "text", required: true },
      { key: "transcript", label: "Transcript", type: "textarea" },
      ORDER_FIELD,
      PUBLISHED_FIELD,
    ],
    columns: [{ key: "title", label: "Title" }, ORDER_COLUMN, PUBLISHED_COLUMN],
  },
  {
    type: "writing",
    label: "Writing",
    apiBase: "/writings",
    trailingSlash: false,
    fields: [
      { key: "title", label: "Title", type: "text", required: true },
      { key: "instruction", label: "Instruction", type: "textarea", required: true },
      { key: "min_words", label: "Min words", type: "number", defaultValue: 30 },
      { key: "max_words", label: "Max words", type: "number", defaultValue: 150 },
      ORDER_FIELD,
      PUBLISHED_FIELD,
    ],
    columns: [
      { key: "title", label: "Title" },
      { key: "min_words", label: "Min" },
      { key: "max_words", label: "Max" },
      ORDER_COLUMN,
      PUBLISHED_COLUMN,
    ],
  },
  {
    type: "speaking",
    label: "Speaking",
    apiBase: "/speakings",
    trailingSlash: false,
    fields: [
      { key: "title", label: "Title", type: "text", required: true },
      { key: "topic", label: "Topic", type: "text", required: true },
      { key: "instruction", label: "Instruction", type: "textarea", required: true },
      { key: "sample_answer", label: "Sample answer", type: "textarea" },
      { key: "keywords", label: "Keywords", type: "text" },
      { key: "preparation_time", label: "Prep time (sec)", type: "number", defaultValue: 15 },
      { key: "speaking_time", label: "Speaking time (sec)", type: "number", defaultValue: 90 },
      ORDER_FIELD,
      PUBLISHED_FIELD,
    ],
    columns: [
      { key: "title", label: "Title" },
      { key: "topic", label: "Topic" },
      ORDER_COLUMN,
      PUBLISHED_COLUMN,
    ],
  },
  {
    type: "quiz",
    label: "Quiz",
    apiBase: "/quizzes",
    trailingSlash: false,
    fields: [
      { key: "title", label: "Title", type: "text", required: true },
      { key: "description", label: "Description", type: "textarea" },
      { key: "passing_score", label: "Passing score (%)", type: "number", defaultValue: 70 },
      ORDER_FIELD,
      PUBLISHED_FIELD,
    ],
    columns: [
      { key: "title", label: "Title" },
      { key: "passing_score", label: "Pass %" },
      ORDER_COLUMN,
      PUBLISHED_COLUMN,
    ],
  },
];
