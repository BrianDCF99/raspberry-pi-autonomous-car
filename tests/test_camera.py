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

    def _on_sigterm(_signum, _frame) -> None:
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, _on_sigterm)

    streaming = app.streaming
    if streaming is None:
        # this is the real issue on the Pi
        raise RuntimeError(
            "app.streaming is None. Your run config must set 'networking' and also configure camera_* "
            "(camera_controller + camera_cfg + camera_policy)."
        )

    try:
        streaming.serve_forever()
    except KeyboardInterrupt:
        return 130
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else 143
    finally:
        app.close()

    return 1


if __name__ == "__main__":
    raise SystemExit(main())