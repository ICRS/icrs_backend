import logging
from threading import Thread
import time

from src.printer_gateway import PrinterGateway

__all__ = ["PrinterFarm"]


class PrinterFarm:
    def __init__(
            self,
            printer_names: list[str],
            printer_suffix: str,
            address: bool = False) -> None:
        self.printers = {
            name: PrinterGateway(
                (name + printer_suffix) if not address else printer_suffix)
            for name in printer_names}
        self.thread = Thread(target=self._updater)
        self.thread.daemon = True  # noqa Ensures the thread will exit when the main program does
        self.running = True
        self.thread.start()

    def _updater(self):
        while self.running:
            for printer_name, printer in self.printers.items():
                try:
                    printer.get_state()
                    printer.get_remaining_time()
                    printer.get_percentage()
                except Exception as e:
                    logging.error(
                        "Error handling printer %s: %s", printer, str(e))
            time.sleep(5)

    def printer_exists(func):                                   # noqa # pylint: disable=missing-function-docstring, no-self-argument
        def wrapper(self, printer_name, attr):
            if printer_name not in self.printers:
                raise Exception("Printer not found")
            return func(self, printer_name, attr)               # noqa # pylint: disable=not-callable
        return wrapper

    def get_printers(self, printer_type: str = None) -> list[PrinterGateway]:      # noqa # pylint: disable=redefined-builtin
        return [
            name for name, printer in self.printers.items()
            if printer_type is not None and printer.type == printer_type]

    @printer_exists
    def get(self, printer_name: str, attr: str) -> any:
        return self.printers[printer_name].data.get(attr, None)

    def __str__(self):
        return str(
            f"PrinterFarm({', '.join([f'{name}: {str(printer)}' for name, printer in self.printers.items()])})") # noqa # pylint: disable=line-too-long
