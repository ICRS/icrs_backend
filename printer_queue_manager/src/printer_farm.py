import logging
import json
import os
from src.printer_gateway import PrinterGateway
import requests

__all__ = ["PrinterFarm"]


# ==============================================================================
settings = json.load(open(os.path.abspath("database_settings.json"),
                          "r", encoding="utf-8"))

DATABASE_ENDPOINT = settings['DATABASE_ENDPOINT']
# ==============================================================================


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

    def printer_exists(func):  # noqa # pylint: disable=missing-function-docstring, no-self-argument
        def wrapper(self, printer_name, attr):
            if printer_name not in self.printers:
                raise Exception("Printer not found")
            return func(self, printer_name, attr)  # noqa # pylint: disable=not-callable
        return wrapper

    def get_printers(self, printer_type: str = None) -> list[PrinterGateway]:
        return [
            name for name, printer in self.printers.items()
            if printer_type is not None and printer.type == printer_type]

    def __str__(self):
        return str(
            f"PrinterFarm({', '.join([f'{name}: {str(printer)}' for name, printer in self.printers.items()])})")  # noqa # pylint: disable=line-too-long

    def queue_print(
        self,
        printer_type: str,
        filename: str,
        gcode: str,
        shortcode: str,
        print_time: int,
        print_weight: int
    ) -> bool:

        for name, printer in self.printers.items():
            if printer.type != printer_type:
                continue
            logging.info(f"Trying to upload to printer: {name}")
            try:
                if printer.printer_availability():
                    logging.info(f"Uploading gcode to printer {name}")
                    use_ams = True
                    ams_mapping = [0]
                    printer.start_print(
                        gcode=gcode,
                        filename=filename,
                        use_ams=use_ams,
                        ams_mapping=ams_mapping)
                    logging.info(f"Started printer {name} with {filename}")
                    requests.post(
                        f"http://{DATABASE_ENDPOINT}/print-metrics/print",
                        params={
                            "printer_name": name,
                            "shortcode": shortcode,
                            "print_time": print_time,
                            "print_weight": print_weight,
                        }
                    )
                    return True

            except Exception as e:
                logging.error(f"Failed to queue printer {name}: {str(e)}")

        return False
