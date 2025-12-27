from __future__ import annotations

import argparse
import signal

from carbot.config.loader import load_run_config
from carbot.factories.app_factory import build_app


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="camera_test")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    cfg = load_run_config(args.config)
    app = build_app(cfg)

    exit_code = 0

    def _on_sigterm(_signum, _frame) -> None:
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, _on_sigterm)

    try:
        app.streaming.serve_forever()
    except KeyboardInterrupt:
        exit_code = 130
    except SystemExit as e:
        exit_code = int(e.code) if isinstance(e.code, int) else 143
    finally:
        app.close()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
