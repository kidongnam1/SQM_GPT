#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
두 SQM 릴리스 폴더를 전수 비교하는 유지보수 도구.

예시:
  python scripts\compare_release_folders.py ^
    --base "D:\program\SQM_inventory\SQM_v868_claan" ^
    --target "D:\program\SQM_inventory\sqm_v869_clean"
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import os
from datetime import datetime
from pathlib import Path


SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".cursor",
    ".bkit",
    "backups",
    "data",
}
SKIP_EXTS = {
    ".db",
    ".db-wal",
    ".db-shm",
    ".pyc",
    ".pyo",
    ".exe",
    ".dll",
    ".png",
    ".jpg",
    ".ico",
    ".bak_pendingempty",
    ".bak_pendingbtn",
    ".bak_corrupted",
    ".bak_schema_a",
    ".bak_schema_b",
}
TEXT_EXTS = {
    ".py",
    ".js",
    ".html",
    ".css",
    ".json",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".cfg",
    ".ini",
    ".sql",
}


def md5(path: Path) -> str | None:
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except OSError:
        return None


def collect(base: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for root, dirs, fnames in os.walk(base):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel_root = Path(root).relative_to(base)
        for name in fnames:
            rel = rel_root / name
            if rel.suffix.lower() in SKIP_EXTS:
                continue
            files[str(rel)] = Path(root) / name
    return files


def diff_lines(left: Path, right: Path) -> tuple[int, int, list[str]]:
    try:
        left_lines = left.read_text(encoding="utf-8", errors="replace").splitlines()
        right_lines = right.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return 0, 0, []

    ops = list(difflib.unified_diff(left_lines, right_lines, lineterm=""))
    added = sum(1 for line in ops if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in ops if line.startswith("-") and not line.startswith("---"))
    return added, removed, ops


def build_report(base: Path, target: Path) -> list[str]:
    base_files = collect(base)
    target_files = collect(target)
    all_keys = sorted(set(base_files) | set(target_files))

    only_base: list[str] = []
    only_target: list[str] = []
    same: list[str] = []
    modified: list[str] = []

    for key in all_keys:
        if key in base_files and key not in target_files:
            only_base.append(key)
        elif key in target_files and key not in base_files:
            only_target.append(key)
        elif md5(base_files[key]) == md5(target_files[key]):
            same.append(key)
        else:
            modified.append(key)

    lines: list[str] = []
    append = lines.append
    append(f"# 릴리스 폴더 비교 보고서")
    append("")
    append(f"- 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    append(f"- 기준(base): `{base}`")
    append(f"- 대상(target): `{target}`")
    append("")
    append("## 요약")
    append("")
    append("| 구분 | 개수 |")
    append("|---|---:|")
    append(f"| 전체 비교 파일 | {len(all_keys)} |")
    append(f"| 동일 | {len(same)} |")
    append(f"| 수정됨 | {len(modified)} |")
    append(f"| base에만 존재 | {len(only_base)} |")
    append(f"| target에만 존재 | {len(only_target)} |")
    append("")
    append("## 수정된 파일")
    append("")
    for key in modified:
        added, removed, ops = diff_lines(base_files[key], target_files[key])
        append(f"### `{key}`")
        append("")
        append(f"- 변경량: `+{added} / -{removed}`")
        if Path(key).suffix.lower() in TEXT_EXTS and ops:
            append("")
            append("```diff")
            shown = 0
            for line in ops:
                if line.startswith("@@"):
                    append(line)
                elif line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
                    append(line[:160])
                    shown += 1
                if shown >= 40:
                    append(f"... (이하 생략, 총 +{added}/-{removed} 줄)")
                    break
            append("```")
        append("")

    append("## base에만 있는 파일")
    append("")
    for key in only_base:
        append(f"- `{key}` ({base_files[key].stat().st_size:,} bytes)")
    append("")

    append("## target에만 있는 파일")
    append("")
    for key in only_target:
        append(f"- `{key}` ({target_files[key].stat().st_size:,} bytes)")

    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="두 SQM 릴리스 폴더를 전수 비교합니다.")
    parser.add_argument("--base", type=Path, required=True, help="기준 폴더")
    parser.add_argument("--target", type=Path, required=True, help="비교 대상 폴더")
    parser.add_argument(
        "--output",
        type=Path,
        help="보고서 저장 경로. 생략하면 REPORTS 아래 자동 파일명으로 저장",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base = args.base.resolve()
    target = args.target.resolve()

    if not base.exists():
        raise SystemExit(f"[오류] 기준 폴더가 없습니다: {base}")
    if not target.exists():
        raise SystemExit(f"[오류] 대상 폴더가 없습니다: {target}")

    if args.output:
        output = args.output.resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = Path("REPORTS") / f"folder_diff_{base.name}_vs_{target.name}_{stamp}.md"

    output.parent.mkdir(parents=True, exist_ok=True)
    lines = build_report(base, target)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"완료: {output}")


if __name__ == "__main__":
    main()
