import assert from "node:assert/strict";
import { test } from "node:test";

import { filterWords, normaliseSearch, wordTypes } from "../../src/features/lessons/utils/wortschatz-filter.ts";

const W = (german_word, translation, extra = {}) => ({
  german_word, translation, article: null, plural: null, word_type: null, lesson_number: 1, saved: false, learned: false, ...extra,
});

const words = [
  W("Bewerbung", "ish arizasi", { article: "die", plural: "Bewerbungen", word_type: "Nomen" }),
  W("Größe", "o‘lcham", { article: "die", word_type: "Nomen", saved: true }),
  W("fahren", "bormoq", { word_type: "Verb", lesson_number: 2, learned: true }),
  W("schön", "chiroyli", { word_type: "Adjektiv" }),
];
const none = { query: "", topic: null, wordType: null, onlySaved: false, hideLearned: false };
const names = (list) => list.map((w) => w.german_word);

test("German search ignores case, article and umlaut spelling", () => {
  assert.deepEqual(names(filterWords(words, { ...none, query: "die bewerbung" })), ["Bewerbung"]);
  assert.deepEqual(names(filterWords(words, { ...none, query: "groesse" })), ["Größe"]);
  assert.deepEqual(names(filterWords(words, { ...none, query: "SCHON" })), ["schön"]);
  assert.deepEqual(names(filterWords(words, { ...none, query: "bewerbungen" })), ["Bewerbung"]); // plural too
});

test("Uzbek search treats the apostrophe variants alike", () => {
  assert.deepEqual(names(filterWords(words, { ...none, query: "o'lcham" })), ["Größe"]);
  assert.deepEqual(names(filterWords(words, { ...none, query: "arizasi" })), ["Bewerbung"]);
  assert.equal(normaliseSearch("Oʻzbek"), normaliseSearch("O'zbek"));
});

test("topic, word type, saved and learned filters combine", () => {
  assert.deepEqual(names(filterWords(words, { ...none, topic: 2 })), ["fahren"]);
  assert.deepEqual(names(filterWords(words, { ...none, wordType: "Nomen" })), ["Bewerbung", "Größe"]);
  assert.deepEqual(names(filterWords(words, { ...none, onlySaved: true })), ["Größe"]);
  assert.deepEqual(names(filterWords(words, { ...none, hideLearned: true, topic: 2 })), []);
});

test("word types keep the teaching order", () => {
  assert.deepEqual(wordTypes(words), ["Nomen", "Verb", "Adjektiv"]);
});
