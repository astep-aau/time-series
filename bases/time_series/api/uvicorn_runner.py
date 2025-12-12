import logging
import signal

from time_series.api.logging_utils import setup_logging
from time_series.settings import Environment, get_settings
from uvicorn import Config, Server


def run() -> None:
    settings = get_settings()

    server = Server(
        Config(
            "time_series.api.main:app",
            host=settings.listen_host,
            port=settings.port,
            log_level=logging.getLevelName(settings.log_level.value),
            reload=(settings.environment != Environment.PRODUCTION),
            log_config=None,  # Handled by setup_logging()
        ),
    )

    def handle_exit(sig, frame):
        server.should_exit = True

    signal.signal(signal.SIGINT, handle_exit)  # CTRL+C
    signal.signal(signal.SIGTERM, handle_exit)  # pod/OS kill

    setup_logging()
    server.run()


if __name__ == "__main__":
    run()
