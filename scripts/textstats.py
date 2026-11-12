#!/usr/bin/env python3
"""Text statistics for HKDSE Chinese composition marking.

Counts CJK characters, sentences, sentence-length distribution and a few
high-frequency characters that betray a flat style.

Usage:
    python3 textstats.py essay.txt
    python3 textstats.py essay.txt --json
    cat essay.txt | python3 textstats.py -
"""

from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

CJK = re.compile(r"[\u4e00-\u9fff]")
SENT_SPLIT = re.compile(r"[。！？]+")
WATCH = ("的", "了", "我", "他", "她")


def load(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def strip_markdown(text: str) -> str:
    """Ignore fenced code and table rows, so a .md document is measured by prose."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    lines = [ln for ln in text.splitlines() if not ln.strip().startswith("|")]
    return "\n".join(lines)


def analyse(text: str) -> dict:
    han = len(CJK.findall(text))
    parts = [s for s in SENT_SPLIT.split(text) if CJK.search(s)]
    lengths = [len(CJK.findall(s)) for s in parts]
    n = len(lengths)

    if n == 0:
        raise SystemExit("沒有可分析的句子。")

    mean = statistics.mean(lengths)
    stdev = statistics.pstdev(lengths) if n > 1 else 0.0
    short = sum(1 for x in lengths if x < 10)

    counts = {ch: text.count(ch) for ch in WATCH}
    per100 = {ch: (c / han * 100 if han else 0.0) for ch, c in counts.items()}

    return {
        "chars": han,
        "sentences": n,
        "mean": round(mean, 1),
        "max": max(lengths),
        "min": min(lengths),
        "cv": round(stdev / mean, 2) if mean else 0.0,
        "short": short,
        "short_ratio": round(short / n, 2),
        "counts": counts,
        "per100": {k: round(v, 1) for k, v in per100.items()},
    }


def verdict(a: dict) -> list[str]:
    notes = []
    if a["mean"] < 16:
        notes.append("句短：平均不足十六字，近電報體，敘述改以逗號推進。")
    if a["mean"] > 34:
        notes.append("句長：平均逾三十四字，讀來滯，宜斷一二處。")
    if a["max"] < 35:
        notes.append("無長句：全篇最長不足三十五字，缺一口長氣。")
    if a["short_ratio"] > 0.40:
        notes.append("短句過多：十字以下逾四成，收束的權力用成敘述的常態。")
    if a["cv"] < 0.45:
        notes.append("句長太齊：長短無變化，節奏板。")
    if a["per100"]["的"] > 5.5:
        notes.append("「的」太密：每百字逾五個半，刪虛字。")
    if a["per100"]["我"] > 4.5:
        notes.append("「我」太密：每百字逾四個半，主語可省。")
    return notes


def main() -> None:
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    as_json = "--json" in sys.argv[1:]
    if len(args) != 1:
        raise SystemExit(__doc__)

    a = analyse(load(args[0]))

    if as_json:
        print(json.dumps({**a, "notes": verdict(a)}, ensure_ascii=False, indent=2))
        return

    print(f"字數（漢字）　{a['chars']}")
    print(f"句數　　　　　{a['sentences']}")
    print(f"平均句長　　　{a['mean']}")
    print(f"最長／最短　　{a['max']}／{a['min']}")
    print(f"句長變異 CV　 {a['cv']}")
    print(f"十字以下　　　{a['short']}（{a['short_ratio']:.0%}）")
    print("高頻字　　　　" + "　".join(f"{k} {v}" for k, v in a["counts"].items()))
    print("每百字　　　　" + "　".join(f"{k} {v}" for k, v in a["per100"].items()))

    notes = verdict(a)
    if notes:
        print("\n判語")
        for line in notes:
            print("· " + line)
    else:
        print("\n判語　句長與虛字，皆在合格之列。")


if __name__ == "__main__":
    main()
