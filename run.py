import argparse
import asyncio
import logging
from pathlib import Path

import uvicorn

from bot.api import create_app
from bot.config import Config
from bot.engine import Engine

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Trading bot platform")
    sub = parser.add_subparsers(dest="command", required=True)

    engine_p = sub.add_parser("engine", help="run the trading engine loop")
    engine_p.add_argument("--env", default=str(ROOT / ".env"), help="path to .env file")

    api_p = sub.add_parser("api", help="run the REST API + dashboard")
    api_p.add_argument("--env", default=str(ROOT / ".env"), help="path to .env file")
    api_p.add_argument("--host", default="0.0.0.0")
    api_p.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    config = Config.from_env(Path(args.env))

    if args.command == "engine":
        engine = Engine(config)
        try:
            asyncio.run(engine.run())
        except KeyboardInterrupt:
            engine.stop()
    else:
        app = create_app(config)
        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
