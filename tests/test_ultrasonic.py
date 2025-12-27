from __future__ import annotations

import argparse

from carbot.config.loader import load_run_config
from carbot.factories.app_factory import build_app


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="ultrasonic_test")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    cfg = load_run_config(args.config)
    app = build_app(cfg)

    assert app.ultrasonic is not None

    assert app.motor is None
    assert app.servo is None
    assert app.infrared is None
    assert app.camera is None
    assert app.streaming is None

    driver = app.ultrasonic
    driver.start()

    try:
        last_seq: int | None = None
        while True:
            res = driver.wait_next(last_seq, timeout=1.0)
            if res is None:
                continue

            seq, dist = res
            last_seq = seq
            print(f"Distance: {dist:.3f}")

    except KeyboardInterrupt:
        return 130

    finally:
        driver.close()


if __name__ == "__main__":
    raise SystemExit(main())
