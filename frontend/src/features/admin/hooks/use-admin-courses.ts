"use client";

import { useState } from "react";
import { isAxiosError } from "axios";

import { useAsyncResource } from "./use-async-resource";
import * as coursesService from "../services/courses-service";
import type { CreateCourseInput, UpdateCourseInput } from "../types/course";

function extractErrorMessage(err: unknown, fallback: string): string {
  if (isAxiosError<{ message?: string }>(err)) {
    return err.response?.data?.message ?? fallback;
  }
  return fallback;
}

export function useAdminCourses() {
  const resource = useAsyncResource(() => coursesService.listCourses(), []);

  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  async function create(input: CreateCourseInput) {
    setCreating(true);
    setCreateError(null);

    try {
      const course = await coursesService.createCourse(input);
      resource.refetch();
      return course;
    } catch (err) {
      setCreateError(extractErrorMessage(err, "Failed to create course."));
      throw err;
    } finally {
      setCreating(false);
    }
  }

  async function update(courseId: string, data: UpdateCourseInput) {
    await coursesService.updateCourse(courseId, data);
    resource.refetch();
  }

  async function remove(courseId: string) {
    await coursesService.deleteCourse(courseId);
    resource.refetch();
  }

  return {
    ...resource,
    creating,
    createError,
    create,
    update,
    remove,
  };
}
