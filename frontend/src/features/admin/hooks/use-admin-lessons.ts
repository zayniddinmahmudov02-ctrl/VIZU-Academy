"use client";

import { useState } from "react";
import { isAxiosError } from "axios";

import { useAsyncResource } from "./use-async-resource";
import * as lessonsService from "../services/lessons-service";
import type { CreateLessonInput, UpdateLessonInput } from "../types/lesson";

function extractErrorMessage(err: unknown, fallback: string): string {
  if (isAxiosError<{ message?: string }>(err)) {
    return err.response?.data?.message ?? fallback;
  }
  return fallback;
}

export function useAdminLessons() {
  const resource = useAsyncResource(() => lessonsService.listLessons(), []);
  const modules = useAsyncResource(() => lessonsService.listModuleOptions(), []);

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  async function create(input: CreateLessonInput) {
    setSaving(true);
    setSaveError(null);
    try {
      const lesson = await lessonsService.createLesson(input);
      resource.refetch();
      return lesson;
    } catch (err) {
      setSaveError(extractErrorMessage(err, "Failed to create lesson."));
      throw err;
    } finally {
      setSaving(false);
    }
  }

  async function update(lessonId: string, data: UpdateLessonInput) {
    setSaving(true);
    setSaveError(null);
    try {
      const lesson = await lessonsService.updateLesson(lessonId, data);
      resource.refetch();
      return lesson;
    } catch (err) {
      setSaveError(extractErrorMessage(err, "Failed to update lesson."));
      throw err;
    } finally {
      setSaving(false);
    }
  }

  async function remove(lessonId: string) {
    await lessonsService.deleteLesson(lessonId);
    resource.refetch();
  }

  return {
    ...resource,
    modules: modules.data ?? [],
    modulesLoading: modules.loading,
    saving,
    saveError,
    create,
    update,
    remove,
  };
}
