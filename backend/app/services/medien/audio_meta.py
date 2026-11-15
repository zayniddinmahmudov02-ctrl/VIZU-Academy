"""Metadata of an uploaded song: duration, bitrate, codec and the title / artist / album / genre tags.

Read with ffprobe (JSON), or with ffmpeg alone when ffprobe is not installed (its `-i` report is parsed). Three outcomes:
  * a file the tool ran on and could read            -> `AudioInfo(status="OK")` (some fields may still be None)
  * a file the tool ran on and says is NOT audio     -> `AudioUnreadable` (the upload is refused: broken / renamed file)
  * the tool is missing, times out or crashes        -> `AudioInfo(status="FAILED", note=...)`: the ORIGINAL file is kept, the song is
    saved without metadata and the admin sees the warning — one missing tool never blocks every upload.
Nothing is re-encoded here and no file is changed. Every step is logged (without file contents)."""

from __future__ import annotations

import json
import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.services.audio_files import service as audio

log = logging.getLogger("vizu.medien.audio")

PROBE_TIMEOUT = 60
MAX_DURATION_MS = audio.MAX_DURATION_MS
_TAGS = ("title", "artist", "album", "genre")
_CONTROL = re.compile(r"[\x00-\x1f\x7f​-‏‪-‮﻿]")
_NOT_AUDIO = re.compile(r"invalid data found|could not find codec|moov atom not found|no such file|does not contain any stream|end of file", re.I)


class AudioUnreadable(Exception):
    """The tool ran fine and reports that the file cannot be decoded as audio."""


@dataclass
class AudioInfo:
    duration_ms: int | None = None
    bitrate_kbps: int | None = None
    codec: str | None = None
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    genre: str | None = None
    status: str = "OK"          # OK | FAILED
    note: str | None = None     # why metadata is missing (FAILED)


def _clean(value) -> str | None:
    text = " ".join(_CONTROL.sub(" ", str(value or "")).split())
    return text[:255] or None


def _duration_ms(seconds: float | None) -> int | None:
    if seconds is None:
        return None
    ms = round(seconds * 1000)
    return ms if 0 < ms < MAX_DURATION_MS else None


def _failed(note: str) -> AudioInfo:
    log.warning("song metadata unavailable: %s", note)
    return AudioInfo(status="FAILED", note=note[:300])


def _from_ffprobe(tool: str, path: Path) -> AudioInfo:
    proc = subprocess.run([tool, "-v", "error", "-show_entries", "format=duration,bit_rate:format_tags:stream=codec_name,codec_type", "-of", "json", str(path)],
                          capture_output=True, text=True, timeout=PROBE_TIMEOUT)
    if proc.returncode != 0:
        if _NOT_AUDIO.search(proc.stderr or ""):
            raise AudioUnreadable((proc.stderr or "").strip()[:200])
        return _failed(f"ffprobe exit {proc.returncode}")
    data = json.loads(proc.stdout or "{}")
    fmt = data.get("format") or {}
    streams = [s for s in data.get("streams") or [] if s.get("codec_type") in (None, "audio")]
    if not streams and not fmt.get("duration"):
        raise AudioUnreadable("no audio stream")
    tags = {str(k).lower(): v for k, v in (fmt.get("tags") or {}).items()}
    for s in data.get("streams") or []:  # some containers keep the tags on the stream
        for k, v in (s.get("tags") or {}).items():
            tags.setdefault(str(k).lower(), v)
    seconds = float(fmt["duration"]) if fmt.get("duration") not in (None, "N/A") else None
    bitrate = int(round(int(fmt["bit_rate"]) / 1000)) if str(fmt.get("bit_rate") or "").isdigit() else None
    return AudioInfo(duration_ms=_duration_ms(seconds), bitrate_kbps=bitrate, codec=(streams[0].get("codec_name") if streams else None),
                     **{k: _clean(tags.get(k)) for k in _TAGS})


def _from_ffmpeg(tool: str, path: Path) -> AudioInfo:
    # `ffmpeg -i file` without an output file prints the report to stderr and exits with 1 — that is expected
    proc = subprocess.run([tool, "-nostdin", "-hide_banner", "-i", str(path)], capture_output=True, text=True, timeout=PROBE_TIMEOUT)
    report = proc.stderr or ""
    if _NOT_AUDIO.search(report) and "Duration:" not in report:
        raise AudioUnreadable(report.strip().splitlines()[-1][:200] if report.strip() else "unreadable")
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", report)
    seconds = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None
    b = re.search(r"bitrate:\s*(\d+)\s*kb/s", report)
    codec = re.search(r"Stream #\d+:\d+[^:]*: Audio:\s*([\w]+)", report)
    if seconds is None and not codec:
        raise AudioUnreadable("no audio stream")
    tags: dict[str, str] = {}
    head = report.split("Duration:", 1)[0]  # the file-level "Metadata:" block comes before the Duration line
    for line in head.splitlines():
        t = re.match(r"^\s{4}(title|artist|album|genre)\s*:\s*(.+)$", line, re.I)
        if t:
            tags.setdefault(t.group(1).lower(), t.group(2))
    return AudioInfo(duration_ms=_duration_ms(seconds), bitrate_kbps=int(b.group(1)) if b else None, codec=codec.group(1) if codec else None,
                     **{k: _clean(tags.get(k)) for k in _TAGS})


def read(path: Path) -> AudioInfo:
    """Metadata of the stored file (see the module docstring for the three outcomes)."""
    probe, mpeg = audio.find_tool("ffprobe"), audio.find_tool("ffmpeg")
    if not probe and not mpeg:
        return _failed("AUDIO_TOOL_MISSING: neither ffprobe nor ffmpeg was found")
    try:
        info = _from_ffprobe(probe, path) if probe else _from_ffmpeg(mpeg, path)
    except AudioUnreadable:
        log.info("song metadata: not readable as audio")
        raise
    except subprocess.TimeoutExpired:
        return _failed(f"the metadata tool timed out after {PROBE_TIMEOUT} s")
    except (subprocess.SubprocessError, OSError, ValueError, KeyError) as exc:
        return _failed(f"the metadata tool failed ({type(exc).__name__})")
    log.info("song metadata read: tool=%s duration_ms=%s bitrate_kbps=%s codec=%s tags=%s", "ffprobe" if probe else "ffmpeg", info.duration_ms,
             info.bitrate_kbps, info.codec, [k for k in _TAGS if getattr(info, k)])
    if info.duration_ms is None:
        info.status, info.note = "FAILED", "the duration could not be determined"
    return info
