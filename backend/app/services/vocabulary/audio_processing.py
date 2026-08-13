"""Turns one raw microphone recording of a German word into the final
"word, pause, word, pause, word" WAV file played back to students — no
AI voice generation anywhere in this module. The admin's own recorded
voice goes in; the same voice, cleaned up and repeated 3x, comes out.

Two ffmpeg subprocess calls per recording:
1. Clean: decode whatever the browser sent (webm/opus, ogg, wav, ...),
   trim leading/trailing silence, apply a light highpass + denoise, and
   normalize loudness -> one mono 16-bit WAV of just the spoken word.
2. Repeat: concatenate that cleaned word with a generated silence gap,
   3 times, into the final WAV actually stored and played back.

All I/O happens in a per-call TemporaryDirectory so nothing is ever left
on disk after a request finishes, whether it succeeds or fails.
"""

import asyncio
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.config import settings

SAMPLE_RATE = 48000
CHANNELS = 1

# Resolved once at import time, not a bare "ffmpeg"/"ffprobe" passed to
# subprocess — the production systemd unit runs this service with
# PATH=<venv>/bin only (no /usr/bin), so relying on $PATH here fails
# with FileNotFoundError even though ffmpeg is genuinely installed and
# reachable from an interactive shell. shutil.which() checks $PATH
# first, then the common system install locations as a fallback so this
# keeps working regardless of how a given host's PATH is configured.
def _resolve_binary(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    for candidate in (f"/usr/bin/{name}", f"/usr/local/bin/{name}"):
        if Path(candidate).exists():
            return candidate
    return name  # let subprocess raise its own clear FileNotFoundError


FFMPEG_BIN = _resolve_binary("ffmpeg")
FFPROBE_BIN = _resolve_binary("ffprobe")

# Conservative — trims silence and normalizes loudness without touching
# pitch/timbre, so the pronunciation itself is never altered:
#   highpass       removes low-frequency room rumble under 80Hz (not speech)
#   afftdn         light FFT denoise (a mic's constant background hiss)
#   silenceremove (x2, reversed between them) trims leading AND trailing
#     silence — running it once, reversing, running it again, reversing
#     back is the standard ffmpeg trick since the filter only trims from
#     the start of a stream
#   loudnorm       single-pass EBU R128 loudness normalization, tuned
#     for spoken word (not music)
_CLEAN_FILTER = (
    "highpass=f=80,"
    "afftdn=nf=-25,"
    "silenceremove=start_periods=1:start_duration=0.1:start_threshold=-45dB,"
    "areverse,"
    "silenceremove=start_periods=1:start_duration=0.1:start_threshold=-45dB,"
    "areverse,"
    "loudnorm=I=-16:TP=-1.5:LRA=11"
)


class AudioProcessingError(Exception):
    pass


def _run_ffmpeg(args: list[str]) -> None:
    """Synchronous — always call via asyncio.to_thread."""
    try:
        result = subprocess.run(
            [FFMPEG_BIN, "-y", "-hide_banner", "-loglevel", "error", *args],
            capture_output=True,
            timeout=60,
        )
    except FileNotFoundError as exc:
        raise AudioProcessingError(f"ffmpeg not found ({FFMPEG_BIN}): {exc}") from exc
    if result.returncode != 0:
        raise AudioProcessingError(
            f"ffmpeg failed: {result.stderr.decode('utf-8', errors='ignore')[:500]}"
        )


def _probe_duration_seconds(path: Path) -> float:
    try:
        result = subprocess.run(
            [
                FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration",
                "-of", "json", str(path),
            ],
            capture_output=True,
            timeout=20,
        )
    except FileNotFoundError as exc:
        raise AudioProcessingError(f"ffprobe not found ({FFPROBE_BIN}): {exc}") from exc
    if result.returncode != 0:
        raise AudioProcessingError(
            f"ffprobe failed: {result.stderr.decode('utf-8', errors='ignore')[:500]}"
        )
    try:
        return float(json.loads(result.stdout)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError):
        # silenceremove trimmed the recording down to (near) nothing —
        # ffprobe reports no usable duration for what's essentially an
        # empty stream. Same root cause as "too short", same message.
        return 0.0


# Below this, the cleaned recording is almost certainly silence/noise
# with nothing actually said — silenceremove trimmed it down to (near)
# nothing rather than isolating a spoken word.
_MIN_SPOKEN_SECONDS = 0.15


def _process_sync(raw_bytes: bytes, pause_ms: int) -> bytes:
    with tempfile.TemporaryDirectory(prefix="vizu_vocab_audio_") as tmp:
        tmp_dir = Path(tmp)
        raw_path = tmp_dir / "raw.input"
        cleaned_path = tmp_dir / "cleaned.wav"
        final_path = tmp_dir / "final.wav"

        raw_path.write_bytes(raw_bytes)

        _run_ffmpeg(
            [
                "-i", str(raw_path),
                "-af", _CLEAN_FILTER,
                "-ar", str(SAMPLE_RATE),
                "-ac", str(CHANNELS),
                "-sample_fmt", "s16",
                "-c:a", "pcm_s16le",
                str(cleaned_path),
            ]
        )

        cleaned_duration = _probe_duration_seconds(cleaned_path)
        if cleaned_duration < _MIN_SPOKEN_SECONDS:
            raise AudioProcessingError(
                "Keine Sprache erkannt — bitte das Wort deutlich und ohne "
                "lange Stille am Anfang/Ende aufnehmen."
            )

        pause_seconds = max(pause_ms, 0) / 1000
        # concat can't consume the same labeled stream ([0:a]/a trimmed
        # silence label) more than once in one filtergraph — ffmpeg
        # rejects it ("Invalid stream specifier", confirmed live on
        # 6.1.1) despite looking like valid syntax. asplit explicitly
        # duplicates each source into as many copies as it's used
        # (3x the word, 2x the pause) before concat runs.
        _run_ffmpeg(
            [
                "-i", str(cleaned_path),
                "-f", "lavfi", "-i", f"anullsrc=r={SAMPLE_RATE}:cl=mono",
                "-filter_complex",
                (
                    "[0:a]asplit=3[w1][w2][w3];"
                    f"[1:a]atrim=duration={pause_seconds}[p0];"
                    "[p0]asplit=2[p1][p2];"
                    "[w1][p1][w2][p2][w3]concat=n=5:v=0:a=1[out]"
                ),
                "-map", "[out]",
                "-ar", str(SAMPLE_RATE),
                "-ac", str(CHANNELS),
                "-sample_fmt", "s16",
                "-c:a", "pcm_s16le",
                str(final_path),
            ]
        )

        return final_path.read_bytes()


async def process_recording(raw_bytes: bytes, pause_ms: int | None = None) -> bytes:
    """raw_bytes is whatever MediaRecorder produced client-side (usually
    audio/webm;codecs=opus) — ffmpeg auto-detects the input format, no
    need to know the exact codec here. Returns the final WAV bytes:
    word, pause, word, pause, word. Never writes to permanent storage;
    the caller decides whether/where to persist the result."""

    if pause_ms is None:
        pause_ms = settings.VOCAB_AUDIO_REPEAT_PAUSE_MS

    return await asyncio.to_thread(_process_sync, raw_bytes, pause_ms)
