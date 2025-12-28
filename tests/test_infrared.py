from __future__ import annotations

import argparse

from carbot.config.loader import load_run_config
from carbot.factories.app_factory import build_app


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="infrared_test")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    cfg = load_run_config(args.config)
    app = build_app(cfg)

    assert app.infrared is not None

    assert app.motor is None
    assert app.servo is None
    assert app.ultrasonic is None
    assert app.camera is None
    assert app.streaming is None

    driver = app.infrared
    driver.start()

    try:
        last_seq: int | None = None
        while True:
            sample = driver.wait_next(last_seq, timeout=1.0)
            if sample is None:
                continue

            last_seq = sample.seq
            print(
                f"Bits:  {sample.bits:03b}\tTuple: {(sample.left, sample.middle, sample.right)}"
            )

    except KeyboardInterrupt:
        return 130

    finally:
        driver.close()


if __name__ == "__main__":
    raise SystemExit(main())
