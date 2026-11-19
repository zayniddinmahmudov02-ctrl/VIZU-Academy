import assert from "node:assert/strict";
import { test } from "node:test";

import {
  fileIdOf, isAudioName, localDuplicates, MAX_FILES, parseDuplicate, restoreState, room, sameNames, summarize,
} from "../../src/features/admin/lib/song-upload.ts";

test("the list takes up to 500 files, only audio endings", () => {
  assert.equal(MAX_FILES, 500);
  assert.equal(room(0), 500);
  assert.equal(room(490), 10);
  assert.equal(room(600), 0);
  for (const n of ["a.mp3", "B.WAV", "c.m4a", "d.aac", "e.ogg", "f.flac"]) assert.equal(isAudioName(n), true);
  for (const n of ["x.txt", "y.mp4", "noext"]) assert.equal(isAudioName(n), false);
  assert.equal(fileIdOf({ name: "a.mp3", size: 10, lastModified: 5 }), "a.mp3|10|5");
});

test("the server's duplicate answer gives the existing song", () => {
  assert.deepEqual(parseDuplicate("SONG_DUPLICATE: 0b9b2b39-9a1c-4c45-9b1e-1f2a3b4c5d6e Mein Lied"), { id: "0b9b2b39-9a1c-4c45-9b1e-1f2a3b4c5d6e", title: "Mein Lied" });
  assert.equal(parseDuplicate("FILE_TOO_LARGE: x"), null);
  assert.equal(parseDuplicate(undefined), null);
});

test("the same file twice in the list: the later one is the duplicate; the same NAME with other content is only a hint", () => {
  const rows = [{ key: "a", sha: "h1", name: "lied.mp3" }, { key: "b", sha: "h2", name: "Lied.mp3" }, { key: "c", sha: "h1", name: "kopie.mp3" }, { key: "d", sha: null, name: "x.mp3" }];
  assert.deepEqual([...localDuplicates(rows)], [["c", "a"]]);
  assert.deepEqual([...sameNames(rows)].sort(), ["a", "b"]);
  assert.equal(sameNames([{ key: "a", sha: "h1", name: "x.mp3" }, { key: "b", sha: "h1", name: "x.mp3" }]).size, 0); // same name AND content = a duplicate, not this hint
});

test("the numbers of the progress panel", () => {
  const rows = [
    { key: "1", state: "done", size: 100, percent: 100, processing: "PENDING" },
    { key: "2", state: "done", size: 100, percent: 100, processing: "OK" },
    { key: "3", state: "up", size: 200, percent: 50 },
    { key: "4", state: "wait", size: 100, percent: 0 },
    { key: "5", state: "hashing", size: 100, percent: 0 },
    { key: "6", state: "error", size: 100, percent: 0 },
    { key: "7", state: "dup", size: 1000, percent: 0 },
    { key: "8", state: "missing", size: 100, percent: 0 },
  ].map((r) => ({ fileId: r.key, name: r.key, sha: null, ...r }));
  const s = summarize(rows);
  assert.deepEqual({ total: s.total, done: s.done, failed: s.failed, dups: s.dups, uploading: s.uploading, waiting: s.waiting, missing: s.missing, remaining: s.remaining, processing: s.processing },
    { total: 8, done: 2, failed: 1, dups: 1, uploading: 1, waiting: 2, missing: 1, remaining: 4, processing: 1 });
  assert.equal(s.bytesTotal, 800); // a duplicate is never sent
  assert.equal(s.bytesDone, 300);
  assert.equal(s.percent, 37);
  assert.equal(summarize([]).percent, 0);
});

test("after a reload: finished rows stay, the rest needs its file again", () => {
  assert.equal(restoreState("done"), "done");
  assert.equal(restoreState("dup"), "dup");
  for (const st of ["wait", "up", "hashing", "error", "missing"]) assert.equal(restoreState(st), "missing");
});
