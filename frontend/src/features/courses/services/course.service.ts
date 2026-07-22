import { api } from "@/src/services/api";
import { Course } from "../types/course";

export async function getCourses(): Promise<Course[]> {
  const response = await api.get<Course[]>("/courses");
  return response.data;
}