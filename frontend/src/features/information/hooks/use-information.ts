"use client";

import { useEffect, useState } from "react";

import { INFORMATION_API_ENABLED } from "@/constants/feature-flags";
import { getInformation } from "../services/information-service";
import type { ProjectInformation } from "../types/information";

/** Known-correct defaults, shown immediately and kept if the backend call fails. */
export const DEFAULT_INFORMATION: ProjectInformation = {
  projectName: "VIZU Academy",
  foundedDate: "06.01.2026",
  authorName: "Zayniddinkhuja Makhmudov",
  telegramUrl: "https://t.me/vizu_deutsch",
  instagramUrl: "https://www.instagram.com/vizu_deutsch",
  youtubeUrl: "https://www.youtube.com/@vizu_deutsch",
};

interface UseInformationResult {
  information: ProjectInformation;
  loading: boolean;
}

export function useInformation(): UseInformationResult {
  const [information, setInformation] = useState<ProjectInformation>(DEFAULT_INFORMATION);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!INFORMATION_API_ENABLED) {
      setLoading(false);
      return;
    }

    let isMounted = true;

    async function fetchInformation() {
      try {
        const data = await getInformation();
        if (isMounted) {
          setInformation(data);
        }
      } catch (err) {
        console.warn("Failed to load project information, using defaults:", err);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchInformation();

    return () => {
      isMounted = false;
    };
  }, []);

  return { information, loading };
}
