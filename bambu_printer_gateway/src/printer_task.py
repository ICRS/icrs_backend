__all__ = ["PrinterTask"]

import asyncio
import json
import requests

from bambulabs_api import GcodeState, Printer
from .printer import (
    PRINTER_NAME_TITLE,
    DATABASE_URL,
    RABBITMQ_EXCHANGE,
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USERNAME,
    RABBITMQ_PASSWORD,
)
import pika
from pika.exchange_type import ExchangeType

FINISH_STATES = set([GcodeState.FAILED, GcodeState.FINISH])
RUNNING_STATES = set([GcodeState.RUNNING, GcodeState.PAUSE])


class PrinterTask:
    EXCHANGE = RABBITMQ_EXCHANGE
    EXCHANGE_TYPE = ExchangeType.topic
    PRINTER_NAME = PRINTER_NAME_TITLE.replace(" ", "-").lower()

    def __init__(self, printer: Printer, sleep=5) -> None:
        self._printer = printer
        self._task_sleep = sleep

        self.running = False

        self.credentials = pika.PlainCredentials(
            RABBITMQ_USERNAME, RABBITMQ_PASSWORD)

    async def task(self):
        with pika.BlockingConnection(
            pika.ConnectionParameters(
                host=str(RABBITMQ_HOST),
                port=int(RABBITMQ_PORT),
                credentials=self.credentials,
            )
        ) as conn:
            channel = conn.channel()
            channel.exchange_declare(
                exchange=self.EXCHANGE, exchange_type=self.EXCHANGE_TYPE)

            while True:
                state = GcodeState(self._printer.get_state())
                if state in RUNNING_STATES:
                    self.running = True
                elif state in FINISH_STATES and self.running:
                    self.running = False
                    requests.post(
                        f"{DATABASE_URL}/print-metrics/print/update/stop",
                        params={
                            "printer_name": PRINTER_NAME_TITLE
                        }
                    )
                channel.basic_publish(
                    exchange=self.EXCHANGE,
                    routing_key=f"printer.{self.PRINTER_NAME}.status",
                    body=json.dumps({
                        "state": str(state),
                        "running": self.running,
                    })
                )

                await asyncio.sleep(self._task_sleep)
