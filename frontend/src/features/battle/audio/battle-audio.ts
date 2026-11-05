/** VIZU DEUTSCH BATTLE audio: ONE central manager, all sound synthesised with the Web Audio API.
 *
 * Original music and effects generated in the browser — no audio files (no licence questions, zero download on
 * mobile data, nothing that can fail to load). Rules:
 * - Nothing plays before the first user gesture (mobile autoplay rules): the AudioContext is created on pointerdown/key.
 * - Exactly one music track at a time (setTrack crossfades); one-shot jingles duck the music.
 * - Settings (master mute, music/effects on-off + volume) live in localStorage and survive sessions.
 * - Hidden tab → context suspended; leaving Battle → stop(). Any audio error is swallowed: Battle never depends on it. */

export type Track = "off" | "home" | "search" | "arena" | "final";
export type Sfx =
  | "click" | "select" | "correct" | "wrong" | "tick" | "tickUrgent" | "timeUp" | "matchFound" | "count" | "go"
  | "opponent" | "roundWin" | "roundLose" | "transition" | "victory" | "defeat" | "draw" | "rankUp" | "unlock";

export interface AudioSettings {
  muted: boolean;
  music: boolean;
  sfx: boolean;
  musicVolume: number; // 0..1
  sfxVolume: number; // 0..1
}

const KEY = "vizu-battle-audio";
const DEFAULTS: AudioSettings = { muted: false, music: true, sfx: true, musicVolume: 0.45, sfxVolume: 0.8 };

// ── settings store (useSyncExternalStore-friendly) ───────────────────────────
let settings: AudioSettings = DEFAULTS;
let loaded = false;
const listeners = new Set<() => void>();

function load() {
  if (loaded || typeof window === "undefined") return;
  loaded = true;
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) settings = { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {
    settings = DEFAULTS;
  }
}

export function getAudioSettings(): AudioSettings {
  load();
  return settings;
}
export const getServerAudioSettings = (): AudioSettings => DEFAULTS;
export function subscribeAudioSettings(fn: () => void) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}
export function updateAudioSettings(patch: Partial<AudioSettings>) {
  load();
  settings = { ...settings, ...patch };
  try {
    localStorage.setItem(KEY, JSON.stringify(settings));
  } catch {
    /* private mode: keep for this page */
  }
  applyGains();
  if (!settings.muted && settings.music) startTrack(wantedTrack);
  else stopMusic();
  listeners.forEach((l) => l());
}

// ── engine ───────────────────────────────────────────────────────────────────
let ctx: AudioContext | null = null;
let master: GainNode, musicBus: GainNode, sfxBus: GainNode, duck: GainNode;
let noiseBuf: AudioBuffer | null = null;
let wantedTrack: Track = "off";
let playing: Track = "off";
let timer: ReturnType<typeof setInterval> | null = null;
let nextTime = 0;
let step = 0;

function ensure(): AudioContext | null {
  if (typeof window === "undefined") return null;
  if (ctx) return ctx;
  const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!Ctor) return null;
  try {
    ctx = new Ctor();
    master = ctx.createGain();
    musicBus = ctx.createGain();
    duck = ctx.createGain();
    sfxBus = ctx.createGain();
    musicBus.connect(duck).connect(master);
    sfxBus.connect(master);
    const comp = ctx.createDynamicsCompressor(); // keeps peaks civil on phone speakers
    master.connect(comp).connect(ctx.destination);
    noiseBuf = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
    const d = noiseBuf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    applyGains();
  } catch {
    ctx = null;
  }
  return ctx;
}

function applyGains() {
  if (!ctx) return;
  const s = getAudioSettings();
  const t = ctx.currentTime;
  master.gain.setTargetAtTime(s.muted ? 0 : 1, t, 0.03);
  musicBus.gain.setTargetAtTime(s.music ? s.musicVolume * 0.32 : 0, t, 0.05);
  sfxBus.gain.setTargetAtTime(s.sfx ? s.sfxVolume * 0.7 : 0, t, 0.02);
}

/** Call from a user gesture (pointerdown / keydown): creates / resumes the context, then starts the wanted track. */
export function unlockAudio() {
  const c = ensure();
  if (!c) return;
  if (c.state === "suspended") c.resume().catch(() => {});
  startTrack(wantedTrack);
}

export function setSuspended(hidden: boolean) {
  if (!ctx) return;
  (hidden ? ctx.suspend() : ctx.resume()).catch(() => {});
}

const hz = (midi: number) => 440 * Math.pow(2, (midi - 69) / 12);

function tone(bus: GainNode, midi: number, at: number, dur: number, type: OscillatorType, vol: number, opts: { glideTo?: number; cutoff?: number; attack?: number } = {}) {
  if (!ctx) return;
  const o = ctx.createOscillator();
  const g = ctx.createGain();
  o.type = type;
  o.frequency.setValueAtTime(hz(midi), at);
  if (opts.glideTo !== undefined) o.frequency.exponentialRampToValueAtTime(hz(opts.glideTo), at + dur);
  const a = opts.attack ?? 0.005;
  g.gain.setValueAtTime(0.0001, at);
  g.gain.exponentialRampToValueAtTime(vol, at + a);
  g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
  let node: AudioNode = o;
  if (opts.cutoff) {
    const f = ctx.createBiquadFilter();
    f.type = "lowpass";
    f.frequency.value = opts.cutoff;
    o.connect(f);
    node = f;
  }
  node.connect(g).connect(bus);
  o.start(at);
  o.stop(at + dur + 0.05);
}

function noise(bus: GainNode, at: number, dur: number, vol: number, hp = 6000) {
  if (!ctx || !noiseBuf) return;
  const s = ctx.createBufferSource();
  s.buffer = noiseBuf;
  const f = ctx.createBiquadFilter();
  f.type = "highpass";
  f.frequency.value = hp;
  const g = ctx.createGain();
  g.gain.setValueAtTime(vol, at);
  g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
  s.connect(f).connect(g).connect(bus);
  s.start(at);
  s.stop(at + dur + 0.02);
}

function kick(at: number, vol = 0.9) {
  if (!ctx) return;
  const o = ctx.createOscillator();
  const g = ctx.createGain();
  o.frequency.setValueAtTime(140, at);
  o.frequency.exponentialRampToValueAtTime(42, at + 0.14);
  g.gain.setValueAtTime(vol, at);
  g.gain.exponentialRampToValueAtTime(0.0001, at + 0.22);
  o.connect(g).connect(musicBus);
  o.start(at);
  o.stop(at + 0.25);
}

// Music: A minor, i–VI–III–VII (Am F C G) — an original electronic loop per state.
const CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]];
const BASS = [45, 41, 36, 43];
const TRACKS: Record<Exclude<Track, "off">, { bpm: number; drums: 0 | 1 | 2; arp: boolean; pad: boolean; ping: boolean; cutoff: number }> = {
  home: { bpm: 96, drums: 0, arp: true, pad: true, ping: false, cutoff: 1400 },
  search: { bpm: 84, drums: 0, arp: false, pad: true, ping: true, cutoff: 900 },
  arena: { bpm: 112, drums: 1, arp: true, pad: false, ping: false, cutoff: 1800 },
  final: { bpm: 128, drums: 2, arp: true, pad: false, ping: false, cutoff: 3200 },
};

function scheduleStep(track: Exclude<Track, "off">, at: number, n: number) {
  const cfg = TRACKS[track];
  const bar = Math.floor(n / 16) % 4;
  const s16 = n % 16;
  const sixteenth = 60 / cfg.bpm / 4;
  const chord = CHORDS[bar];
  if (cfg.pad && s16 === 0) chord.forEach((m) => tone(musicBus, m, at, sixteenth * 16, "triangle", 0.06, { attack: 0.4, cutoff: cfg.cutoff }));
  if (s16 % 2 === 0 && (cfg.drums || track === "home")) tone(musicBus, BASS[bar] + (s16 % 8 === 6 ? 12 : 0), at, sixteenth * 1.8, "sawtooth", 0.11, { cutoff: cfg.cutoff * 0.5 });
  if (cfg.arp && s16 % 2 === 1) tone(musicBus, chord[(s16 >> 1) % 3] + 12, at, sixteenth * 1.5, "square", 0.035, { cutoff: cfg.cutoff });
  if (cfg.ping && s16 % 8 === 0) tone(musicBus, 81, at, 0.5, "sine", 0.05, { glideTo: 76 });
  if (cfg.drums) {
    if (s16 % 4 === 0) kick(at, cfg.drums === 2 ? 0.8 : 0.65);
    if (s16 % 4 === 2) noise(musicBus, at, 0.05, 0.12);
    if (cfg.drums === 2 && (s16 === 4 || s16 === 12)) noise(musicBus, at, 0.16, 0.22, 1800);
  }
}

function startTrack(track: Track) {
  wantedTrack = track;
  const s = getAudioSettings();
  if (!ctx || ctx.state === "closed" || track === "off" || s.muted || !s.music) {
    if (track === "off" || s.muted || !s.music) stopMusic();
    return;
  }
  if (playing === track && timer) return;
  stopMusic();
  playing = track;
  nextTime = ctx.currentTime + 0.08;
  step = 0;
  duck.gain.cancelScheduledValues(ctx.currentTime);
  duck.gain.setValueAtTime(0.0001, ctx.currentTime);
  duck.gain.exponentialRampToValueAtTime(1, ctx.currentTime + 0.8); // fade in
  timer = setInterval(() => {
    if (!ctx || playing === "off") return;
    const sixteenth = 60 / TRACKS[playing].bpm / 4;
    while (nextTime < ctx.currentTime + 0.12) {
      scheduleStep(playing, nextTime, step++);
      nextTime += sixteenth;
    }
  }, 25);
}

function stopMusic() {
  if (timer) clearInterval(timer);
  timer = null;
  playing = "off";
}

/** The one place pages ask for music. Safe before unlock (remembered and started on the first gesture). */
export function setTrack(track: Track) {
  wantedTrack = track;
  if (ctx) startTrack(track);
}

export function stopAudio() {
  wantedTrack = "off";
  stopMusic();
}

function duckMusic(seconds: number) {
  if (!ctx) return;
  const t = ctx.currentTime;
  duck.gain.cancelScheduledValues(t);
  duck.gain.setTargetAtTime(0.25, t, 0.05);
  duck.gain.setTargetAtTime(1, t + seconds, 0.4);
}

/** Distinct, short sound per event. No-op before the first gesture or when effects are off. */
export function playSfx(name: Sfx) {
  const s = getAudioSettings();
  if (!ctx || s.muted || !s.sfx) return;
  if (ctx.state === "suspended") ctx.resume().catch(() => {});
  const t = ctx.currentTime + 0.01;
  const b = sfxBus;
  try {
    switch (name) {
      case "click": tone(b, 84, t, 0.05, "sine", 0.18); break;
      case "select": tone(b, 76, t, 0.07, "triangle", 0.3); tone(b, 83, t + 0.05, 0.09, "triangle", 0.25); break;
      case "correct": [72, 76, 79, 84].forEach((m, i) => tone(b, m, t + i * 0.06, 0.18, "triangle", 0.32)); break;
      case "wrong": tone(b, 52, t, 0.32, "sawtooth", 0.22, { glideTo: 45, cutoff: 900 }); tone(b, 51, t, 0.32, "square", 0.08, { cutoff: 700 }); break;
      case "tick": tone(b, 96, t, 0.025, "square", 0.05, { cutoff: 5000 }); break;
      case "tickUrgent": tone(b, 88, t, 0.06, "square", 0.14, { cutoff: 4000 }); tone(b, 100, t + 0.07, 0.04, "square", 0.08, { cutoff: 4000 }); break;
      case "timeUp": tone(b, 69, t, 0.5, "sawtooth", 0.18, { glideTo: 57, cutoff: 1200 }); noise(b, t, 0.3, 0.1, 2000); break;
      case "matchFound": duckMusic(1.2); [69, 76, 81, 88].forEach((m, i) => tone(b, m, t + i * 0.07, 0.25, "square", 0.12, { cutoff: 3000 })); noise(b, t, 0.6, 0.08, 3000); break;
      case "count": tone(b, 81, t, 0.18, "sine", 0.35); break;
      case "go": tone(b, 93, t, 0.4, "sine", 0.35); tone(b, 81, t, 0.4, "triangle", 0.2); break;
      case "opponent": tone(b, 64, t, 0.08, "sine", 0.15); tone(b, 60, t + 0.07, 0.1, "sine", 0.12); break;
      case "roundWin": [79, 84].forEach((m, i) => tone(b, m, t + i * 0.09, 0.22, "triangle", 0.28)); break;
      case "roundLose": [67, 62].forEach((m, i) => tone(b, m, t + i * 0.1, 0.24, "triangle", 0.22)); break;
      case "transition": noise(b, t, 0.35, 0.12, 1200); tone(b, 60, t, 0.35, "sine", 0.12, { glideTo: 72 }); break;
      case "victory": duckMusic(3); [60, 64, 67, 72, 76, 79, 84].forEach((m, i) => tone(b, m, t + i * 0.09, 0.5, "square", 0.12, { cutoff: 4000 })); [72, 76, 79].forEach((m) => tone(b, m, t + 0.7, 1.4, "triangle", 0.16, { attack: 0.05 })); break;
      case "defeat": duckMusic(2.5); [69, 65, 62, 57].forEach((m, i) => tone(b, m, t + i * 0.18, 0.45, "triangle", 0.2, { cutoff: 1500 })); break;
      case "draw": duckMusic(2); tone(b, 69, t, 0.35, "triangle", 0.2); tone(b, 69, t + 0.35, 0.5, "triangle", 0.18); break;
      case "rankUp": duckMusic(4); [57, 64, 69, 72, 76, 81].forEach((m, i) => tone(b, m, t + i * 0.12, 0.7, "sawtooth", 0.09, { cutoff: 3500 })); [81, 85, 88].forEach((m) => tone(b, m, t + 0.8, 1.8, "triangle", 0.14, { attack: 0.08 })); noise(b, t + 0.8, 1.2, 0.06, 8000); break;
      case "unlock": [76, 83, 88, 95].forEach((m, i) => tone(b, m, t + i * 0.05, 0.3, "sine", 0.2)); break;
    }
  } catch {
    /* audio is decoration only */
  }
}
