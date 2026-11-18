/** Which part of the music player is shown where (pure; unit-tested in tests/unit/medien-player-view.test.mjs).
 *
 * One <audio> element plays for the whole student panel (GlobalAudioPlayer in the dashboard layout). Around it:
 *  - the large vinyl player: opens when a song is started on Medien → Musik (or from the floating disc); closes on every page change;
 *  - the Musik page bar: the normal controls on Medien → Musik while the large player is closed;
 *  - the floating vinyl disc: on every other page while a song is loaded (playing or paused).
 * Closing (X) stops the audio and empties the player, so none of the three is shown any more. */

export const MUSIC_PATH = "/medien/musik";

export function isMusicPath(pathname: string | null | undefined): boolean {
  return !!pathname && (pathname === MUSIC_PATH || pathname.startsWith(`${MUSIC_PATH}/`));
}

/** A running Multilevel exam docks its Hören audio at the bottom of the phone screen: the floating disc moves above it there. */
export function isExamPath(pathname: string | null | undefined): boolean {
  return !!pathname && /^\/vorbereitung\/multilevel\/pruefung\//.test(pathname);
}

export interface ViewInput {
  hasSong: boolean;
  isMusicPageActive: boolean;
  isLargePlayerOpen: boolean;
}

export interface PlayerView {
  large: boolean;
  floating: boolean;
  bar: boolean;
}

export function playerView({ hasSong, isMusicPageActive, isLargePlayerOpen }: ViewInput): PlayerView {
  if (!hasSong) return { large: false, floating: false, bar: false };
  if (isLargePlayerOpen) return { large: true, floating: false, bar: false };
  return { large: false, floating: !isMusicPageActive, bar: isMusicPageActive };
}

/** 0..1 of the song that has been played (0 while the length is unknown). */
export function progressFraction(current: number, duration: number): number {
  if (!Number.isFinite(current) || !Number.isFinite(duration) || duration <= 0) return 0;
  return Math.min(1, Math.max(0, current / duration));
}

/** stroke-dashoffset of the progress ring around the floating disc. */
export function ringOffset(current: number, duration: number, circumference: number): number {
  return circumference * (1 - progressFraction(current, duration));
}

/** The song length in seconds: the element's own value, else the catalogue value (duration_ms), else 0. */
export function songSeconds(elementDuration: number, durationMs: number | null | undefined): number {
  if (Number.isFinite(elementDuration) && elementDuration > 0) return elementDuration;
  return durationMs && durationMs > 0 ? durationMs / 1000 : 0;
}
