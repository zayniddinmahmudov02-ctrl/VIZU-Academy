"use client";

import { ReactNode, useEffect } from "react";
import { useLanguageStore } from "@/store/language-store";

interface Props {
  children: ReactNode;
}

export default function LanguageProvider({
  children,
}: Props) {
  useEffect(() => {
    useLanguageStore.persist.rehydrate();
  }, []);

  return <>{children}</>;
}
