

from printer_farm import PrinterFarm


__all__ = ["QueueManager"]


class QueueManager:
    def __init__(self, printer_names: list[str], printer_suffix: str) -> None:
        self.printer_farm = PrinterFarm(printer_names, printer_suffix)
