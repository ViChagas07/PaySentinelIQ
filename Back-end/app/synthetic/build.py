from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.synthetic.dataset import build_dataset, build_golden


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build synthetic boleto and payslip datasets.",
    )
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-total", type=int, default=1000)
    parser.add_argument("--render", type=int, default=60)
    parser.add_argument("--langs", default="pt,es,en")
    parser.add_argument("--dataset-version", default="v2.1")
    parser.add_argument("--generator-version", default="v2.1")
    parser.add_argument("--golden", action="store_true")
    args = parser.parse_args()
    out = Path(args.out)
    if args.golden:
        manifest = build_golden(out, seed=args.seed)
        print(
            f"golden documents={manifest['count']} out={out}"
        )
        return
    manifest = build_dataset(
        out,
        seed=args.seed,
        n_total=args.n_total,
        render=args.render,
        langs=tuple(args.langs.split(",")),
        dataset_version=args.dataset_version,
        generator_version=args.generator_version,
    )
    print(json.dumps(manifest["splits"], ensure_ascii=False))
    print(
        f"records={manifest['n_total']} rendered={manifest['render']} "
        f"out={out}"
    )


if __name__ == "__main__":
    main()
