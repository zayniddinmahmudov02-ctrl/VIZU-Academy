"use client";

import { useState } from "react";

import type { VocabularyExercise } from "./exercise-generator";

interface Props {
  exercise: VocabularyExercise;
  onDone: (correct: boolean) => void;
}

const CHOICE_BASE =
  "w-full rounded-xl px-4 py-3 text-left text-sm font-medium shadow-sm ring-1 transition-colors disabled:cursor-not-allowed";
const CHOICE_IDLE = "bg-surface-card text-text-primary ring-surface-border hover:bg-accent-blue/5 hover:ring-accent-blue/30";
const CHOICE_SELECTED = "bg-accent-blue/10 text-text-primary ring-accent-blue/40";
const CHOICE_CORRECT = "bg-success/10 text-success ring-success/40";
const CHOICE_WRONG = "bg-danger/10 text-danger ring-danger/40";

function NextButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="mt-4 inline-flex items-center gap-1.5 rounded-button bg-gradient-to-r from-accent-blue-hover to-accent-blue px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-accent-blue/25 transition hover:-translate-y-0.5"
    >
      Weiter
    </button>
  );
}

/** One sequential Wortschatz exercise — answer, check, reveal, advance.
 * Keyed by index in the parent so each mount gets fresh local state. */
export default function ExerciseRunner({ exercise, onDone }: Props) {
  switch (exercise.kind) {
    case "MULTIPLE_CHOICE":
      return (
        <ChoiceExercise
          prompt={`${exercise.word.article ? exercise.word.article + " " : ""}${exercise.word.german_word}`}
          instruction="Wähle die richtige Übersetzung"
          choices={exercise.choices}
          correctAnswer={exercise.correctAnswer}
          onDone={onDone}
        />
      );
    case "ARTIKEL":
      return (
        <ChoiceExercise
          prompt={exercise.word.german_word}
          instruction="Wähle den richtigen Artikel"
          choices={exercise.choices}
          correctAnswer={exercise.correctAnswer}
          onDone={onDone}
        />
      );
    case "LUECKENTEXT":
      return <LueckentextExercise exercise={exercise} onDone={onDone} />;
    case "WORT_ORDNEN":
      return <WortOrdnenExercise exercise={exercise} onDone={onDone} />;
    case "ZUORDNUNG":
      return <ZuordnungExercise exercise={exercise} onDone={onDone} />;
    default:
      return null;
  }
}

function ChoiceExercise({
  prompt,
  instruction,
  choices,
  correctAnswer,
  onDone,
}: {
  prompt: string;
  instruction: string;
  choices: string[];
  correctAnswer: string;
  onDone: (correct: boolean) => void;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const [checked, setChecked] = useState(false);

  return (
    <div className="rounded-2xl bg-surface-hover/60 p-6 ring-1 ring-surface-border">
      <p className="text-xs font-medium text-text-muted">{instruction}</p>
      <h3 className="mt-1 text-lg font-bold text-text-primary">{prompt}</h3>

      <div className="mt-4 space-y-2.5">
        {choices.map((choice) => {
          const isSelected = selected === choice;
          const showCorrect = checked && choice === correctAnswer;
          const showWrong = checked && isSelected && choice !== correctAnswer;
          return (
            <button
              key={choice}
              type="button"
              disabled={checked}
              onClick={() => setSelected(choice)}
              className={`${CHOICE_BASE} ${
                showCorrect ? CHOICE_CORRECT : showWrong ? CHOICE_WRONG : isSelected ? CHOICE_SELECTED : CHOICE_IDLE
              }`}
            >
              {choice}
            </button>
          );
        })}
      </div>

      {!checked ? (
        <button
          type="button"
          disabled={!selected}
          onClick={() => setChecked(true)}
          className="mt-4 inline-flex items-center gap-1.5 rounded-button bg-gradient-to-r from-accent-blue-hover to-accent-blue px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-accent-blue/25 transition enabled:hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Prüfen
        </button>
      ) : (
        <NextButton onClick={() => onDone(selected === correctAnswer)} />
      )}
    </div>
  );
}

function LueckentextExercise({
  exercise,
  onDone,
}: {
  exercise: Extract<VocabularyExercise, { kind: "LUECKENTEXT" }>;
  onDone: (correct: boolean) => void;
}) {
  const [value, setValue] = useState("");
  const [checked, setChecked] = useState(false);
  const isCorrect = value.trim().toLowerCase() === exercise.correctAnswer.trim().toLowerCase();

  return (
    <div className="rounded-2xl bg-surface-hover/60 p-6 ring-1 ring-surface-border">
      <p className="text-xs font-medium text-text-muted">Lückentext — ergänze das fehlende Wort</p>
      <h3 className="mt-1 text-lg font-bold text-text-primary">{exercise.sentenceWithBlank}</h3>

      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={checked}
        placeholder="Antwort eingeben..."
        className="mt-4 w-full rounded-xl bg-surface-card px-4 py-3 text-sm text-text-primary shadow-sm ring-1 ring-surface-border outline-none focus:ring-accent-blue/40 disabled:cursor-not-allowed"
      />

      {checked && (
        <p className={`mt-2 text-sm ${isCorrect ? "text-success" : "text-danger"}`}>
          Richtige Antwort: <span className="font-semibold">{exercise.correctAnswer}</span>
        </p>
      )}

      {!checked ? (
        <button
          type="button"
          disabled={!value.trim()}
          onClick={() => setChecked(true)}
          className="mt-4 inline-flex items-center gap-1.5 rounded-button bg-gradient-to-r from-accent-blue-hover to-accent-blue px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-accent-blue/25 transition enabled:hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Prüfen
        </button>
      ) : (
        <NextButton onClick={() => onDone(isCorrect)} />
      )}
    </div>
  );
}

function WortOrdnenExercise({
  exercise,
  onDone,
}: {
  exercise: Extract<VocabularyExercise, { kind: "WORT_ORDNEN" }>;
  onDone: (correct: boolean) => void;
}) {
  const [pickedIndices, setPickedIndices] = useState<number[]>([]);
  const [checked, setChecked] = useState(false);

  const pickedTokens = pickedIndices.map((i) => exercise.scrambledTokens[i]);
  const isCorrect = pickedTokens.join(" ") === exercise.correctTokens.join(" ");
  const allPicked = pickedIndices.length === exercise.scrambledTokens.length;

  function toggle(tokenIndex: number) {
    if (checked) return;
    setPickedIndices((prev) =>
      prev.includes(tokenIndex) ? prev.filter((i) => i !== tokenIndex) : [...prev, tokenIndex],
    );
  }

  return (
    <div className="rounded-2xl bg-surface-hover/60 p-6 ring-1 ring-surface-border">
      <p className="text-xs font-medium text-text-muted">Wort ordnen — bilde den richtigen Satz</p>
      <h3 className="mt-1 text-sm font-semibold text-text-secondary">{exercise.word.translation}</h3>

      <div className="mt-4 flex min-h-[3rem] flex-wrap gap-2 rounded-xl bg-surface-card p-3 ring-1 ring-surface-border">
        {pickedIndices.length === 0 && (
          <span className="text-xs text-text-muted">Klicke die Wörter unten in der richtigen Reihenfolge an</span>
        )}
        {pickedTokens.map((token, i) => (
          <span key={i} className="rounded-lg bg-accent-blue/10 px-3 py-1.5 text-sm font-medium text-accent-blue">
            {token}
          </span>
        ))}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {exercise.scrambledTokens.map((token, i) => {
          const picked = pickedIndices.includes(i);
          return (
            <button
              key={i}
              type="button"
              disabled={checked || picked}
              onClick={() => toggle(i)}
              className={`rounded-xl px-3.5 py-2 text-sm font-medium shadow-sm ring-1 transition-colors ${
                picked
                  ? "cursor-not-allowed bg-surface-hover text-text-muted ring-surface-border"
                  : "bg-surface-card text-text-primary ring-surface-border hover:bg-accent-blue/5 hover:ring-accent-blue/30"
              }`}
            >
              {token}
            </button>
          );
        })}
      </div>

      {checked && (
        <p className={`mt-3 text-sm ${isCorrect ? "text-success" : "text-danger"}`}>
          Richtiger Satz: <span className="font-semibold">{exercise.correctTokens.join(" ")}</span>
        </p>
      )}

      {!checked ? (
        <button
          type="button"
          disabled={!allPicked}
          onClick={() => setChecked(true)}
          className="mt-4 inline-flex items-center gap-1.5 rounded-button bg-gradient-to-r from-accent-blue-hover to-accent-blue px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-accent-blue/25 transition enabled:hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Prüfen
        </button>
      ) : (
        <NextButton onClick={() => onDone(isCorrect)} />
      )}
    </div>
  );
}

function ZuordnungExercise({
  exercise,
  onDone,
}: {
  exercise: Extract<VocabularyExercise, { kind: "ZUORDNUNG" }>;
  onDone: (correct: boolean) => void;
}) {
  const [pairs, setPairs] = useState<Record<string, string>>({});
  const [pendingWordId, setPendingWordId] = useState<string | null>(null);
  const [checked, setChecked] = useState(false);

  const [shuffledTranslations] = useState(() => {
    const arr = exercise.words.map((w) => w.translation);
    for (let i = arr.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  });

  const allPaired = Object.keys(pairs).length === exercise.words.length;
  const isCorrect = exercise.words.every((w) => pairs[w.id] === w.translation);

  function pickTranslation(value: string) {
    if (checked || !pendingWordId) return;
    setPairs((prev) => ({ ...prev, [pendingWordId]: value }));
    setPendingWordId(null);
  }

  return (
    <div className="rounded-2xl bg-surface-hover/60 p-6 ring-1 ring-surface-border">
      <p className="text-xs font-medium text-text-muted">Zuordnung — ordne die Wörter ihrer Übersetzung zu</p>

      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="space-y-2">
          {exercise.words.map((word) => {
            const isPending = pendingWordId === word.id;
            const pairedValue = pairs[word.id];
            const isCorrectPair = checked && pairedValue === word.translation;
            const isWrongPair = checked && !!pairedValue && !isCorrectPair;
            return (
              <button
                key={word.id}
                type="button"
                disabled={checked}
                onClick={() => setPendingWordId(word.id)}
                className={`flex w-full items-center justify-between rounded-xl px-3.5 py-2.5 text-left text-sm font-medium shadow-sm ring-1 transition-colors ${
                  isCorrectPair
                    ? CHOICE_CORRECT
                    : isWrongPair
                      ? CHOICE_WRONG
                      : isPending
                        ? CHOICE_SELECTED
                        : CHOICE_IDLE
                }`}
              >
                <span>
                  {word.article && <span className="text-text-secondary">{word.article} </span>}
                  {word.german_word}
                </span>
                {pairedValue && <span className="text-xs text-text-muted">→ {pairedValue}</span>}
              </button>
            );
          })}
        </div>
        <div className="space-y-2">
          {shuffledTranslations.map((translation) => {
            const usedBy = Object.entries(pairs).find(([, v]) => v === translation);
            return (
              <button
                key={translation}
                type="button"
                disabled={checked || !!usedBy}
                onClick={() => pickTranslation(translation)}
                className={`w-full rounded-xl px-3.5 py-2.5 text-left text-sm font-medium shadow-sm ring-1 transition-colors ${
                  usedBy ? "cursor-not-allowed bg-surface-hover text-text-muted ring-surface-border" : CHOICE_IDLE
                }`}
              >
                {translation}
              </button>
            );
          })}
        </div>
      </div>

      {!checked ? (
        <button
          type="button"
          disabled={!allPaired}
          onClick={() => setChecked(true)}
          className="mt-4 inline-flex items-center gap-1.5 rounded-button bg-gradient-to-r from-accent-blue-hover to-accent-blue px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-accent-blue/25 transition enabled:hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Prüfen
        </button>
      ) : (
        <NextButton onClick={() => onDone(isCorrect)} />
      )}
    </div>
  );
}
