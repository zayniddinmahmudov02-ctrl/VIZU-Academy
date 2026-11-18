import { part1 } from "./extra/part1";
import { part2 } from "./extra/part2";
import { part3 } from "./extra/part3";
import { part4 } from "./extra/part4";
import { part5 } from "./extra/part5";
import { part6 } from "./extra/part6";
import { part7 } from "./extra/part7";
import { part8 } from "./extra/part8";
import { part9 } from "./extra/part9";
import { part10 } from "./extra/part10";
import { part11 } from "./extra/part11";

/** English and Russian interface texts: namespace -> key -> [en, ru]. Keys mirror translations.ts (uz / de);
 * a missing entry falls back to German (use-translation.ts). Coverage is checked by tests/unit/i18n-coverage.test.mjs. */
export const extraTranslations: Record<string, Record<string, [string, string]>> = Object.assign(
  {},
  ...[part1, part2, part3, part4, part5, part6, part7, part8, part9, part10, part11].map((part) => part),
);
