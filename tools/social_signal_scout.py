# -*- coding: utf-8 -*-
"""
CHEONOK Social Signal Scout v0.1
--------------------------------
목적:
- TikTok/Shorts/Reels 링크 1개를 입력받아 단건 분석용 자료를 만든다.
- 대량 크롤링 금지. 링크 기반 수집만 수행한다.
- yt-dlp가 설치되어 있으면 메타데이터/영상 다운로드를 시도한다.
- 결과를 Markdown 보고서로 저장한다.

사용 예:
python tools/social_signal_scout.py "https://vt.tiktok.com/xxxx/"

선택 설치:
pip install yt-dlp
"""

import json
import os
import re
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


def run_cmd(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", "COMMAND_NOT_FOUND"
    except subprocess.TimeoutExpired:
        return 124, "", "TIMEOUT"


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
    code, out, err = run_cmd(cmd)
    if code == 0:
        files = list(workdir.glob("video.*"))
        return files[0].name if files else None, None
    return None, err or f"yt-dlp exit {code}"


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


def canon_judgement(fields):
    text = " ".join([
        fields.get("title", ""),
        fields.get("description", ""),
        " ".join(fields.get("tags", []) if isinstance(fields.get("tags"), list) else []),
    ]).lower()

    signals = []
    if any(k in text for k in ["money", "revenue", "income", "수익", "돈", "매출", "달러"]):
        signals.append("현금흐름/수익 신호")
    if any(k in text for k in ["faceless", "얼굴", "anonymous", "no face"]):
        signals.append("얼굴 없는 콘텐츠 신호")
    if any(k in text for k in ["youtube", "short", "shorts", "유튜브", "쇼츠"]):
        signals.append("YouTube/Shorts 유입 신호")
    if any(k in text for k in ["ai", "automation", "자동화"]):
        signals.append("AI/자동화 신호")
    if any(k in text for k in ["niche", "니치"]):
        signals.append("니치 발굴 신호")

    if signals:
        verdict = "PASS as signal / HOLD as proof"
    else:
        verdict = "HOLD"

    return verdict, signals


def make_report(url, workdir, meta, meta_err, video_file, video_err):
    fields = extract_fields(meta)
    verdict, signals = canon_judgement(fields)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""# CHEONOK Social Signal Scout Report

생성시각: {now}

## 1. 입력 링크

{url}

## 2. 수집 상태

- metadata: {'OK' if meta else 'FAILED'}
- video_download: {'OK: ' + video_file if video_file else 'FAILED'}
- metadata_error: {meta_err or '-'}
- video_error: {video_err or '-'}

## 3. 메타데이터 요약

- title: {fields.get('title','')}
- uploader: {fields.get('uploader','')}
- upload_date: {fields.get('upload_date','')}
- duration: {fields.get('duration','')}
- view_count: {fields.get('view_count','')}
- like_count: {fields.get('like_count','')}
- comment_count: {fields.get('comment_count','')}
- tags: {', '.join(fields.get('tags', [])) if isinstance(fields.get('tags'), list) else fields.get('tags','')}

## 4. 정본 신호 판정

판정: **{verdict}**

감지 신호:

{chr(10).join(['- ' + s for s in signals]) if signals else '- 감지 신호 부족'}

## 5. CHEONOK 적용 질문

```text
1. 이 콘텐츠는 사람들의 어떤 욕망/불안을 건드리는가?
2. 이 신호가 현금흐름·유입·구독·사람 가치 증폭 중 어디에 연결되는가?
3. 그대로 따라 하면 위험한 부분은 무엇인가?
4. CHEONOK 방식으로 바꾸면 어떤 콘텐츠/상품/페이지가 되는가?
5. PASS / HOLD / BLOCK 최종 판정은 무엇인가?
```

## 6. 다음 행동

```text
- 영상이 다운로드되었으면 자막/OCR/음성 추출 단계로 넘긴다.
- 영상 다운로드 실패 시 캡처 2~3장 또는 요약 텍스트로 보완한다.
- 좋은 신호라면 콘텐츠 아이디어와 홈페이지 문구로 변환한다.
```

## 7. 원칙

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
        print("사용법: python tools/social_signal_scout.py <TikTok/Shorts/Reels URL>")
        sys.exit(1)
    url = sys.argv[1].strip()
    name = datetime.now().strftime("%Y%m%d_%H%M%S_") + safe_name(urlparse(url).netloc + "_" + url)
    workdir = OUT_DIR / name
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "input_url.txt").write_text(url, encoding="utf-8")

    meta, meta_err = get_metadata(url, workdir)
    video_file, video_err = download_video(url, workdir)
    report_path = make_report(url, workdir, meta, meta_err, video_file, video_err)

    print("CHEONOK Social Signal Scout DONE")
    print("workdir:", workdir)
    print("report:", report_path)


if __name__ == "__main__":
    main()
