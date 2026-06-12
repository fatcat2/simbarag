import asyncio
import logging
import signal
import sys

from aiohttp import web

from simbakit.config import Config
from simbakit.database import Database
from simbakit.poller import run_poller
from simbakit.web import create_app


def _handle_signal(
    sig: signal.Signals, shutdown_event: asyncio.Event, log: logging.Logger
) -> None:
    log.info("Received %s, shutting down...", sig.name)
    shutdown_event.set()


async def _async_main(config: Config) -> None:
    logger = logging.getLogger("simbakit")

    db = Database(config.db_path)
    await db.initialize()

    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_signal, sig, shutdown_event, logger)

    # Start web server
    app = create_app(db)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.web_host, config.web_port)
    await site.start()
    logger.info("Web UI available at http://%s:%d", config.web_host, config.web_port)

    logger.info(
        "SimbaKit starting -- polling %s every %ds",
        config.petkit_region,
        config.poll_interval_seconds,
    )
    try:
        await run_poller(config, db, shutdown_event)
    finally:
        await runner.cleanup()
        await db.close()
        logger.info("SimbaKit shut down cleanly")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("simbakit")

    try:
        config = Config()
    except KeyError as e:
        logger.error("Missing required environment variable: %s", e)
        sys.exit(1)

    asyncio.run(_async_main(config))


if __name__ == "__main__":
    main()
