import { useEffect, useState } from "react";

import { getCourses } from "../services/course.service";
import { Course } from "../types/course";

export function useCourses() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCourses();
  }, []);

  async function loadCourses() {
    try {
      const data = await getCourses();
      setCourses(data);
    } finally {
      setLoading(false);
    }
  }

  return {
    courses,
    loading,
    reload: loadCourses,
  };
}