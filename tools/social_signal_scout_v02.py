# -*- coding: utf-8 -*-
"""
CHEONOK Social Signal Scout v0.2
--------------------------------
Single-link social signal analyzer for TikTok / Shorts / Reels.

What v0.2 adds:
- metadata extraction by yt-dlp
- video download by yt-dlp
- subtitle / auto-caption download attempt by yt-dlp
- audio extraction by ffmpeg when available
- optional transcription using local whisper command when available
- frame extraction by ffmpeg when available
- Korean markdown report with CHEONOK canon filter

Usage:
python tools/social_signal_scout_v02.py "https://vt.tiktok.com/xxxx/"

Required:
pip install yt-dlp

Optional:
- ffmpeg in PATH
- whisper command in PATH, if local transcription is wanted

Rule:
This is a single-link analysis tool. Do not use as a mass crawler.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "social_signal_scout"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_name(text: str) -> str:
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^a-zA-Z0-9가-힣_.-]+", "_", text)
    return text[:90].strip("_") or "social_signal"


def run_cmd(cmd, timeout=240):
    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", "COMMAND_NOT_FOUND"
    except subprocess.TimeoutExpired:
        return 124, "", "TIMEOUT"


def which(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def get_metadata(url: str, workdir: Path):
    json_path = workdir / "metadata.json"
    cmd = ["yt-dlp", "--dump-json", "--no-playlist", url]
    code, out, err = run_cmd(cmd)
    if code == 0 and out.strip():
        try:
            data = json.loads(out.splitlines()[0])
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return data, None
        except Exception as e:
            return None, f"metadata_parse_error: {e}"
    return None, err or f"yt-dlp exit {code}"


def download_video(url: str, workdir: Path):
    outtmpl = str(workdir / "video.%(ext)s")
    cmd = ["yt-dlp", "--no-playlist", "-f", "mp4/best", "-o", outtmpl, url]
    code, out, err = run_cmd(cmd, timeout=600)
    if code == 0:
        files = sorted(workdir.glob("video.*"), key=lambda p: p.stat().st_mtime, reverse=True)
        return files[0] if files else None, None
    return None, err or f"yt-dlp exit {code}"


def download_subtitles(url: str, workdir: Path):
    subdir = workdir / "subs"
    subdir.mkdir(exist_ok=True)
    outtmpl = str(subdir / "subs.%(ext)s")
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs",
        "all,-live_chat",
        "--convert-subs",
        "srt",
        "-o",
        outtmpl,
        url,
    ]
    code, out, err = run_cmd(cmd, timeout=240)
    subs = sorted(subdir.glob("*.srt")) + sorted(subdir.glob("*.vtt"))
    text = ""
    for p in subs:
        try:
            text += f"\n\n--- {p.name} ---\n" + p.read_text(encoding="utf-8", errors="replace")[:20000]
        except Exception:
            pass
    if text.strip():
        (workdir / "subtitles_collected.txt").write_text(text, encoding="utf-8")
        return [p.name for p in subs], None
    return [], err or f"subtitle exit {code}"


def extract_audio(video_path: Path, workdir: Path):
    if not video_path:
        return None, "NO_VIDEO"
    if not which("ffmpeg"):
        return None, "FFMPEG_NOT_FOUND"
    audio_path = workdir / "audio.wav"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(audio_path),
    ]
    code, out, err = run_cmd(cmd, timeout=600)
    if code == 0 and audio_path.exists():
        return audio_path, None
    return None, err or f"ffmpeg exit {code}"


def transcribe_audio(audio_path: Path, workdir: Path):
    if not audio_path:
        return None, "NO_AUDIO"
    if not which("whisper"):
        return None, "WHISPER_COMMAND_NOT_FOUND"
    tdir = workdir / "transcript"
    tdir.mkdir(exist_ok=True)
    cmd = [
        "whisper",
        str(audio_path),
        "--model",
        "base",
        "--language",
        "ko",
        "--output_dir",
        str(tdir),
        "--output_format",
        "txt",
    ]
    code, out, err = run_cmd(cmd, timeout=1200)
    txts = list(tdir.glob("*.txt"))
    if code == 0 and txts:
        text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in txts)
        (workdir / "transcript_collected.txt").write_text(text, encoding="utf-8")
        return text, None
    return None, err or f"whisper exit {code}"


def extract_frames(video_path: Path, workdir: Path):
    if not video_path:
        return [], "NO_VIDEO"
    if not which("ffmpeg"):
        return [], "FFMPEG_NOT_FOUND"
    frames_dir = workdir / "frames"
    frames_dir.mkdir(exist_ok=True)
    out_pattern = str(frames_dir / "frame_%03d.jpg")
    # Extract one frame every 3 seconds, max first 60 seconds.
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-t",
        "60",
        "-vf",
        "fps=1/3,scale=720:-1",
        out_pattern,
    ]
    code, out, err = run_cmd(cmd, timeout=600)
    frames = sorted(frames_dir.glob("*.jpg"))
    if frames:
        return [p.name for p in frames], None
    return [], err or f"ffmpeg frame exit {code}"


def extract_fields(meta):
    if not meta:
        return {}
    return {
        "title": meta.get("title") or "",
        "description": meta.get("description") or "",
        "uploader": meta.get("uploader") or meta.get("channel") or "",
        "upload_date": meta.get("upload_date") or "",
        "duration": meta.get("duration") or "",
        "view_count": meta.get("view_count") or "",
        "like_count": meta.get("like_count") or "",
        "comment_count": meta.get("comment_count") or "",
        "repost_count": meta.get("repost_count") or "",
        "tags": meta.get("tags") or [],
        "webpage_url": meta.get("webpage_url") or "",
    }


def load_text_if_exists(path: Path, limit=30000) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    return ""


def canon_judgement(fields, subtitles_text="", transcript_text=""):
    text = " ".join([
        fields.get("title", ""),
        fields.get("description", ""),
        " ".join(fields.get("tags", []) if isinstance(fields.get("tags"), list) else []),
        subtitles_text,
        transcript_text,
    ]).lower()

    signals = []
    if any(k in text for k in ["money", "revenue", "income", "수익", "돈", "매출", "달러", "$"]):
        signals.append("현금흐름/수익 신호")
    if any(k in text for k in ["faceless", "얼굴", "anonymous", "no face", "without showing"]):
        signals.append("얼굴 없는 콘텐츠 신호")
    if any(k in text for k in ["youtube", "short", "shorts", "유튜브", "쇼츠"]):
        signals.append("YouTube/Shorts 유입 신호")
    if any(k in text for k in ["ai", "automation", "자동화", "인공지능"]):
        signals.append("AI/자동화 신호")
    if any(k in text for k in ["niche", "니치"]):
        signals.append("니치 발굴 신호")
    if any(k in text for k in ["tool", "도구", "software", "app"]):
        signals.append("도구/소프트웨어 탐색 신호")
    if any(k in text for k in ["beginner", "초보", "쉽게", "simple", "without editing", "편집"]):
        signals.append("초보자/무편집 욕망 신호")

    if len(signals) >= 2:
        verdict = "PASS as signal / HOLD as proof"
    elif signals:
        verdict = "HOLD as weak signal"
    else:
        verdict = "HOLD"
    return verdict, signals


def make_report(url, workdir, meta, meta_err, video_path, video_err, subs, sub_err, audio_path, audio_err, transcript_text, transcript_err, frames, frames_err):
    fields = extract_fields(meta)
    subtitles_text = load_text_if_exists(workdir / "subtitles_collected.txt")
    transcript_text = transcript_text or load_text_if_exists(workdir / "transcript_collected.txt")
    verdict, signals = canon_judgement(fields, subtitles_text, transcript_text)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    title = fields.get('title','')
    desc = fields.get('description','')
    tags = fields.get('tags', [])
    if isinstance(tags, list):
        tags_txt = ', '.join(str(x) for x in tags)
    else:
        tags_txt = str(tags)

    report = f"""# CHEONOK Social Signal Scout Report v0.2

생성시각: {now}

## 1. 입력 링크

{url}

## 2. 수집 상태

- metadata: {'OK' if meta else 'FAILED'}
- video_download: {'OK: ' + video_path.name if video_path else 'FAILED'}
- subtitles: {'OK: ' + ', '.join(subs) if subs else 'FAILED/NONE'}
- audio_extract: {'OK: ' + audio_path.name if audio_path else 'FAILED/NONE'}
- transcript: {'OK' if transcript_text else 'FAILED/NONE'}
- frames: {'OK: ' + str(len(frames)) + ' frames' if frames else 'FAILED/NONE'}

### errors

- metadata_error: {meta_err or '-'}
- video_error: {video_err or '-'}
- subtitle_error: {sub_err or '-'}
- audio_error: {audio_err or '-'}
- transcript_error: {transcript_err or '-'}
- frames_error: {frames_err or '-'}

## 3. 메타데이터 요약

- title: {title}
- uploader: {fields.get('uploader','')}
- upload_date: {fields.get('upload_date','')}
- duration: {fields.get('duration','')}
- view_count: {fields.get('view_count','')}
- like_count: {fields.get('like_count','')}
- comment_count: {fields.get('comment_count','')}
- tags: {tags_txt}

## 4. 자막/음성 텍스트 미리보기

### subtitles preview

```text
{subtitles_text[:2500] if subtitles_text else 'NO SUBTITLE TEXT'}
```

### transcript preview

```text
{transcript_text[:2500] if transcript_text else 'NO TRANSCRIPT TEXT'}
```

## 5. 정본 신호 판정

판정: **{verdict}**

감지 신호:

{chr(10).join(['- ' + s for s in signals]) if signals else '- 감지 신호 부족'}

## 6. CHEONOK 적용 질문

```text
1. 이 콘텐츠는 사람들의 어떤 욕망/불안을 건드리는가?
2. 이 신호가 현금흐름·유입·구독·사람 가치 증폭 중 어디에 연결되는가?
3. 그대로 따라 하면 위험한 부분은 무엇인가?
4. CHEONOK 방식으로 바꾸면 어떤 콘텐츠/상품/페이지가 되는가?
5. PASS / HOLD / BLOCK 최종 판정은 무엇인가?
```

## 7. 현재 자동 해석 초안

```text
- 이 링크는 수익/유입/니치/AI/무편집/얼굴없는 콘텐츠 중 감지된 신호를 기준으로 평가한다.
- 실제 수익 증거는 검증 전까지 HOLD다.
- 대중 욕망 신호는 PASS 가능하다.
- CHEONOK 적용 시 그대로 베끼지 말고, 인간친화·현실해결·동반성장 메시지로 변환한다.
```

## 8. 다음 행동

```text
- 좋은 신호라면 Social Signal DB에 저장한다.
- 유사 GitHub 도구를 Open Intelligence Scout로 탐색한다.
- CHEONOK 콘텐츠 아이디어 3개로 변환한다.
- 홈페이지/무료진단/결제 루프와 연결한다.
```

## 9. 원칙

```text
대량 크롤링 금지.
단건 링크 기반 분석.
저작권·플랫폼 정책·개인정보 위험이 있으면 HOLD/BLOCK.
신호로는 PASS 가능하나, 수익 증거로는 검증 전 HOLD.
```
"""
    path = workdir / "report.md"
    path.write_text(report, encoding="utf-8")
    return path


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/social_signal_scout_v02.py <TikTok/Shorts/Reels URL>")
        sys.exit(1)

    url = sys.argv[1].strip()
    name = datetime.now().strftime("%Y%m%d_%H%M%S_") + safe_name(urlparse(url).netloc + "_" + url)
    workdir = OUT_DIR / name
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "input_url.txt").write_text(url, encoding="utf-8")

    print("[v0.2] metadata...")
    meta, meta_err = get_metadata(url, workdir)

    print("[v0.2] video download...")
    video_path, video_err = download_video(url, workdir)

    print("[v0.2] subtitles...")
    subs, sub_err = download_subtitles(url, workdir)

    print("[v0.2] audio extract...")
    audio_path, audio_err = extract_audio(video_path, workdir)

    print("[v0.2] transcript optional...")
    transcript_text, transcript_err = transcribe_audio(audio_path, workdir)

    print("[v0.2] frames optional...")
    frames, frames_err = extract_frames(video_path, workdir)

    report_path = make_report(
        url,
        workdir,
        meta,
        meta_err,
        video_path,
        video_err,
        subs,
        sub_err,
        audio_path,
        audio_err,
        transcript_text,
        transcript_err,
        frames,
        frames_err,
    )

    print("CHEONOK Social Signal Scout v0.2 DONE")
    print("workdir:", workdir)
    print("report:", report_path)


if __name__ == "__main__":
    main()
