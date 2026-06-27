"""
Safe demo fake-attack script for decoy files.

This script simulates ransomware behavior only on files inside a given
decoy directory by creating an encrypted-copy with ".locked" extension
and appending a short marker line. It does NOT delete originals.

Usage:
  python scripts/demo_fake_attack.py --dir agent/decoy_files_wiretrap_test --delay 0.5

Run with a small delay to emulate file traversal.
"""
from __future__ import annotations
import argparse
import time
from pathlib import Path

def simulate_on_file(p: Path, marker: str = "[FAKE-ENCRYPTED]"):
    out = p.with_name(p.name + ".locked")
    try:
        with p.open("rb") as fr, out.open("wb") as fw:
            fw.write(fr.read())
            fw.write(b"\n")
            fw.write(marker.encode("utf-8"))
        return True, str(out)
    except Exception as e:
        return False, str(e)

def main():
    ap = argparse.ArgumentParser(description="Safe fake ransomware demo on decoy files")
    ap.add_argument("--dir", default="agent/decoy_files_wiretrap_test", help="Decoy directory to target")
    ap.add_argument("--delay", type=float, default=0.2, help="Seconds to wait between files")
    ap.add_argument("--pattern", default="*.*", help="Glob pattern to match files")
    args = ap.parse_args()

    d = Path(args.dir)
    if not d.exists():
        print(f"Decoy directory not found: {d}")
        return

    files = sorted([p for p in d.glob(args.pattern) if p.is_file()])
    if not files:
        print(f"No files matched in {d}")
        return

    print(f"Simulating fake attack on {len(files)} files in {d}")
    for p in files:
        ok, info = simulate_on_file(p)
        if ok:
            print(f"[OK] created: {info}")
        else:
            print(f"[ERR] {p}: {info}")
        time.sleep(args.delay)

    print("Done. Originals preserved; encrypted-copies created with .locked suffix.")

if __name__ == '__main__':
    main()
