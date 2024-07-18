__all__ = ["PrinterTask"]

import asyncio
import requests

from bambulabs_api import GcodeState, Printer
from .printer import PRINTER_NAME_TITLE, DATABASE_URL

FINISH_STATES = set([GcodeState.FAILED, GcodeState.FINISH])
RUNNING_STATES = set([GcodeState.RUNNING, GcodeState.PAUSE])


class PrinterTask:
    def __init__(self, printer: Printer, sleep=5) -> None:
        self._printer = printer
        self._task_sleep = sleep

        self.running = False

    async def task(self):
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

            await asyncio.sleep(self._task_sleep)
