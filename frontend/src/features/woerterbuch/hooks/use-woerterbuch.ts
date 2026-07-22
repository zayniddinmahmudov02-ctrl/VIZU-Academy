"use client";

import { useState } from "react";

import type { DictionaryEntry } from "../types/dictionary";

interface UseWoerterbuchResult {
  query: string;
  setQuery: (value: string) => void;
  result: DictionaryEntry | null;
  search: () => void;
}

export function useWoerterbuch(): UseWoerterbuchResult {
  const [query, setQuery] = useState("");
  const [result] = useState<DictionaryEntry | null>(null);

  function search() {
    if (!query.trim()) return;

    // BACKEND TODO: query the PostgreSQL vocabulary database.
    // Expected: GET /dictionary/search?word=... -> DictionaryEntry
  }

  return { query, setQuery, result, search };
}
