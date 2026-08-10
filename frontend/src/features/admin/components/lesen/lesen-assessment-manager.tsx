"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, Eye, Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminInput } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import {
  createAssessment,
  createOption,
  createQuestion,
  createSection,
  createTask,
  deleteOption,
  deleteQuestion,
  deleteTask,
  listAssessments,
  listSections,
  listTasks,
  updateAssessment,
  updateOption,
  updateQuestion,
  updateTask,
  validateTask,
} from "@/features/admin/services/assessment-service";
import {
  TASK_TYPES,
  TASK_TYPE_LABELS,
  type AssessmentTask,
  type AudioPolicy,
  type SectionSkill,
  type SpeakingConfig,
  type TaskType,
  type WritingConfig,
} from "@/features/admin/types/assessment.types";

import AudioPanel from "./audio-panel";
import ClozeTextEditor from "./cloze-text-editor";
import GapList from "./gap-list";
import LesenRichTextEditor from "./lesen-rich-text-editor";
import SpeakingPanel from "./speaking-panel";
import TaskQuestionsEditor from "./task-questions-editor";
import WritingPanel from "./writing-panel";

const SKILL_LABELS: Record<SectionSkill, string> = {
  LESEN: "Lesen",
  HOEREN: "Hören",
  SCHREIBEN: "Schreiben",
  SPRECHEN: "Sprechen",
};

interface Props {
  lessonId: string;
  skill: SectionSkill;
}

/** The Course integration point: "+ Aufgabe hinzufügen" builder for a
 * Lesson's skill section, on top of the universal Assessment engine
 * (Assessment[type=COURSE, lesson_id] -> one Section per skill -> Tasks).
 * Shared by Lesen and Hören (and ready for Schreiben/Sprechen later) —
 * the engine itself doesn't know or care which skill it's serving; only
 * this component's `skill` prop and the AudioPanel (rendered for HOEREN
 * only) differ. The Assessment + Section are lazily get-or-created the
 * first time an admin adds a task — nothing is ever auto-created with
 * content in it. */
export default function LesenAssessmentManager({ lessonId, skill }: Props) {
  const queryClient = useQueryClient();
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [deleting, setDeleting] = useState<AssessmentTask | null>(null);

  const { data: assessments, isLoading: loadingAssessments } = useQuery({
    queryKey: ["skill-assessment", lessonId, skill],
    queryFn: () => listAssessments({ assessment_type: "COURSE", lesson_id: lessonId }),
  });
  // One COURSE assessment can in principle exist per lesson today (the
  // builder always creates just one) — scope by section skill once
  // sections are loaded so Lesen and Hören never collide if that changes.
  const assessment = assessments?.[0];

  const { data: sections } = useQuery({
    queryKey: ["skill-sections", assessment?.id],
    queryFn: () => listSections(assessment!.id),
    enabled: !!assessment,
  });
  const section = sections?.find((s) => s.skill === skill);

  const { data: tasks, isLoading: loadingTasks } = useQuery({
    queryKey: ["skill-tasks", section?.id],
    queryFn: () => listTasks(section!.id),
    enabled: !!section,
  });

  function invalidateAll() {
    queryClient.invalidateQueries({ queryKey: ["skill-assessment", lessonId, skill] });
    queryClient.invalidateQueries({ queryKey: ["skill-sections"] });
    queryClient.invalidateQueries({ queryKey: ["skill-tasks"] });
  }

  async function ensureAssessmentAndSection(): Promise<string> {
    let currentAssessment = assessment;
    if (!currentAssessment) {
      currentAssessment = await createAssessment({
        title: SKILL_LABELS[skill],
        assessment_type: "COURSE",
        lesson_id: lessonId,
      });
    }

    let currentSection = section;
    if (!currentSection) {
      currentSection = await createSection(currentAssessment.id, {
        skill,
        title: SKILL_LABELS[skill],
        sort_order: 1,
      });
    }

    return currentSection.id;
  }

  async function handleCreateTask(taskType: TaskType) {
    const sectionId = await ensureAssessmentAndSection();
    const created = await createTask(sectionId, {
      task_type: taskType,
      title: TASK_TYPE_LABELS[taskType],
      sort_order: (tasks?.length ?? 0) + 1,
      // Sprechen has no AI audio evaluation in this phase — every
      // SPEAKING task is teacher-only, unlike WRITING's AI_ONLY default.
      ...(taskType === "SPEAKING" ? { evaluation_mode: "TEACHER_ONLY" as const } : {}),
    });
    invalidateAll();
    setPickerOpen(false);
    setExpandedTaskId(created.id);
  }

  async function handlePublishToggle() {
    if (!assessment) return;
    await updateAssessment(assessment.id, {
      status: assessment.status === "PUBLISHED" ? "DRAFT" : "PUBLISHED",
    });
    invalidateAll();
  }

  const isLoading = loadingAssessments || (!!section && loadingTasks);
  const sortedTasks = [...(tasks ?? [])].sort((a, b) => a.sort_order - b.sort_order);

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">{SKILL_LABELS[skill]} — Aufgaben</h3>
          <p className="mt-0.5 text-xs text-[var(--admin-text-muted)]">
            {assessment?.status === "PUBLISHED"
              ? "Veröffentlicht — für Lernende sichtbar."
              : "Entwurf — nur im Admin sichtbar."}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {assessment && (
            <AdminButton
              size="sm"
              variant={assessment.status === "PUBLISHED" ? "secondary" : "primary"}
              onClick={handlePublishToggle}
            >
              {assessment.status === "PUBLISHED" ? (
                <>
                  <Eye size={13} />
                  Zurück zu Entwurf
                </>
              ) : (
                <>
                  <CheckCircle2 size={13} />
                  Veröffentlichen
                </>
              )}
            </AdminButton>
          )}
          <div className="relative">
            <AdminButton size="sm" onClick={() => setPickerOpen((v) => !v)}>
              <Plus size={14} />
              Aufgabe hinzufügen
            </AdminButton>
            {pickerOpen && (
              <div className="absolute right-0 z-10 mt-1.5 w-64 rounded-xl bg-[var(--admin-card)] p-1.5 shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border-strong)]">
                {TASK_TYPES.map((type) => (
                  <button
                    key={type}
                    onClick={() => handleCreateTask(type)}
                    className="block w-full rounded-lg px-3 py-2 text-left text-xs text-[var(--admin-text-secondary)] hover:bg-white/5 hover:text-[var(--admin-text-primary)]"
                  >
                    {TASK_TYPE_LABELS[type]}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}

      {!isLoading && sortedTasks.length === 0 && (
        <div className="rounded-2xl bg-white/[0.02] px-6 py-14 text-center ring-1 ring-[var(--admin-border)]">
          <p className="text-sm text-[var(--admin-text-muted)]">
            Noch keine Aufgaben. Klicke auf &quot;Aufgabe hinzufügen&quot;, um zu beginnen.
          </p>
        </div>
      )}

      <div className="space-y-2.5">
        {sortedTasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            skill={skill}
            expanded={expandedTaskId === task.id}
            onToggle={() => setExpandedTaskId(expandedTaskId === task.id ? null : task.id)}
            onDelete={() => setDeleting(task)}
            onChanged={invalidateAll}
          />
        ))}
      </div>

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Aufgabe löschen"
        description={`"${deleting?.title}" wird dauerhaft gelöscht.`}
        onConfirm={async () => {
          if (!deleting) return;
          await deleteTask(deleting.id);
          setDeleting(null);
          invalidateAll();
        }}
      />
    </div>
  );
}

function TaskCard({
  task,
  skill,
  expanded,
  onToggle,
  onDelete,
  onChanged,
}: {
  task: AssessmentTask;
  skill: SectionSkill;
  expanded: boolean;
  onToggle: () => void;
  onDelete: () => void;
  onChanged: () => void;
}) {
  const [validation, setValidation] = useState<{ is_publishable: boolean; errors: string[] } | null>(null);

  async function checkValidation() {
    const result = await validateTask(task.id);
    setValidation(result);
  }

  return (
    <div className="rounded-2xl bg-[var(--admin-card)] shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)]">
      <div className="flex items-center gap-3 p-4">
        <button onClick={onToggle} className="flex h-6 w-6 items-center justify-center text-[var(--admin-text-muted)]">
          {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </button>

        <span className="shrink-0 rounded-full bg-[var(--admin-primary)]/15 px-2.5 py-1 text-[10px] font-semibold uppercase text-[var(--admin-primary)]">
          {TASK_TYPE_LABELS[task.task_type]}
        </span>

        <span className="flex-1 text-sm font-medium text-[var(--admin-text-primary)]">{task.title}</span>

        <span className="text-xs text-[var(--admin-text-muted)]">{task.max_points} Pkt.</span>

        {validation && !validation.is_publishable && (
          <span title={validation.errors.join(" ")} className="text-[var(--admin-warning)]">
            <AlertTriangle size={15} />
          </span>
        )}

        <button
          onClick={onDelete}
          aria-label="Löschen"
          className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--admin-text-muted)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
        >
          <Trash2 size={14} />
        </button>
      </div>

      {expanded && (
        <div className="space-y-4 border-t border-[var(--admin-border)] p-4">
          <TaskDetailEditor task={task} skill={skill} onChanged={onChanged} />

          <div className="flex items-center justify-between border-t border-[var(--admin-border)] pt-3">
            <AdminButton size="sm" variant="ghost" onClick={checkValidation}>
              Publish-Check
            </AdminButton>
            {validation && (
              <span className={validation.is_publishable ? "text-xs text-[var(--admin-accent)]" : "text-xs text-[var(--admin-warning)]"}>
                {validation.is_publishable ? "Bereit zur Veröffentlichung" : validation.errors.join(" · ")}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function TaskDetailEditor({
  task,
  skill,
  onChanged,
}: {
  task: AssessmentTask;
  skill: SectionSkill;
  onChanged: () => void;
}) {
  const queryClient = useQueryClient();

  async function saveTitle(title: string) {
    if (title === task.title) return;
    await updateTask(task.id, { title });
    onChanged();
  }

  async function savePolicy(policy: Partial<AudioPolicy>) {
    await updateTask(task.id, policy);
    onChanged();
  }

  async function saveWritingConfig(config: Partial<WritingConfig>) {
    await updateTask(task.id, config);
    onChanged();
  }

  async function saveSpeakingConfig(config: Partial<SpeakingConfig> & { image_url?: string | null }) {
    await updateTask(task.id, config);
    onChanged();
  }

  async function saveContent(content: string) {
    await updateTask(task.id, { content });
    onChanged();
  }

  async function saveInstructions(instructions: string) {
    await updateTask(task.id, { instructions });
    onChanged();
  }

  const questionMutations = {
    create: (data: { task_id: string; prompt: string; points: number; sort_order: number }) =>
      createQuestion(task.id, data),
    update: ({ id, data }: { id: string; data: Partial<Parameters<typeof updateQuestion>[1]> }) =>
      updateQuestion(id, data).then(onChanged),
    remove: (id: string) => deleteQuestion(id).then(onChanged),
  };

  const optionMutations = {
    create: (data: {
      question_id: string;
      option_text: string;
      match_value?: string | null;
      is_correct?: boolean;
      sort_order: number;
    }) => createOption(data.question_id, data).then(onChanged),
    update: ({ id, data }: { id: string; data: Record<string, unknown> }) => updateOption(id, data).then(onChanged),
    remove: (id: string) => deleteOption(id).then(onChanged),
  };

  async function insertGap(): Promise<number> {
    const nextIndex = (task.questions?.length ?? 0) + 1;
    await createQuestion(task.id, { prompt: `Lücke ${nextIndex}`, points: 1, sort_order: nextIndex });
    onChanged();
    queryClient.invalidateQueries({ queryKey: ["skill-tasks"] });
    return nextIndex;
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">Titel</label>
        <AdminInput defaultValue={task.title} onBlur={(e) => saveTitle(e.target.value)} />
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
          Anweisung für Lernende (optional)
        </label>
        <AdminInput
          defaultValue={task.instructions ?? ""}
          onBlur={(e) => saveInstructions(e.target.value)}
          placeholder="Lies den Text und beantworte die Fragen."
        />
      </div>

      {skill === "HOEREN" && <AudioPanel task={task} onPolicyChange={savePolicy} onChanged={onChanged} />}

      {task.task_type === "CLOZE_TEXT" ? (
        <div>
          <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">Text</label>
          <ClozeTextEditor content={task.content ?? ""} onChange={saveContent} onInsertGap={insertGap} />
          <div className="mt-3">
            <GapList
              gaps={task.questions}
              onUpdate={(id, data) => updateQuestion(id, data).then(onChanged)}
              onRemove={(id) => deleteQuestion(id).then(onChanged)}
            />
          </div>
        </div>
      ) : task.task_type === "SHORT_ANSWER" ? (
        <ShortAnswerEditor task={task} onChanged={onChanged} />
      ) : task.task_type === "WRITING" ? (
        <div>
          <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
            Aufgabenstellung (z. B. &quot;Sie haben einen Freund eingeladen...&quot;)
          </label>
          <LesenRichTextEditor content={task.content ?? ""} onChange={saveContent} />
          <div className="mt-3">
            <WritingPanel task={task} onConfigChange={saveWritingConfig} onChanged={onChanged} />
          </div>
        </div>
      ) : task.task_type === "SPEAKING" ? (
        <div>
          <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
            Aufgabenstellung (Text und/oder Bild)
          </label>
          <LesenRichTextEditor content={task.content ?? ""} onChange={saveContent} />
          <div className="mt-3">
            <SpeakingPanel task={task} onConfigChange={saveSpeakingConfig} onChanged={onChanged} />
          </div>
        </div>
      ) : (
        <>
          {(task.task_type === "HEADING_MATCHING" ||
            task.task_type === "ADVERTISEMENT_MATCHING" ||
            task.task_type === "TEXT_MATCHING") && (
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
                Text / Anzeigen
              </label>
              <LesenRichTextEditor content={task.content ?? ""} onChange={saveContent} />
            </div>
          )}

          <TaskQuestionsEditor
            taskId={task.id}
            taskType={task.task_type}
            questions={task.questions}
            questionMutations={questionMutations}
            optionMutations={optionMutations}
          />
        </>
      )}
    </div>
  );
}

function ShortAnswerEditor({ task, onChanged }: { task: AssessmentTask; onChanged: () => void }) {
  const question = task.questions[0];

  async function ensureQuestion() {
    if (question) return question;
    return createQuestion(task.id, { prompt: task.title, points: 1, sort_order: 1 });
  }

  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">Frage</label>
      <AdminInput
        defaultValue={question?.prompt ?? ""}
        placeholder="Wie heißt die Hauptstadt von Deutschland?"
        onBlur={async (e) => {
          const q = await ensureQuestion();
          await updateQuestion(q.id, { prompt: e.target.value });
          onChanged();
        }}
        className="mb-3"
      />
      {question && (
        <GapList
          gaps={[question]}
          onUpdate={(id, data) => updateQuestion(id, data).then(onChanged)}
          onRemove={() => {}}
        />
      )}
    </div>
  );
}
