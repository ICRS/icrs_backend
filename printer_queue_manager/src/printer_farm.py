import logging

from bambulabs_api import GcodeState

from src.printer_gateway import PrinterGateway

__all__ = ["PrinterFarm"]


class PrinterFarm:
    def __init__(self, printer_names: list[str], printer_suffix: str) -> None:
        self.printers = {name: PrinterGateway(
            name + printer_suffix) for name in printer_names}
        self.__printer_cache: dict = {name: {} for name in printer_names}

    def printer_exists(func):                           # noqa # pylint: disable=missing-function-docstring, no-self-argument
        def wrapper(self, printer_name):
            if printer_name not in self.printers:
                raise Exception("Printer not found")
            return func(self, printer_name)             # noqa # pylint: disable=not-callable
        return wrapper

    @printer_exists
    def get_remaining_time(self, printer_name: str) -> int:
        """
        Get the remaining time of the print job

        Parameters
        ----------
        printer_name : str
            The name of the printer to get the remaining time for

        Returns
        -------
        int
            The remaining time of the print job
        """
        logging.info("Printer name: %s", printer_name)
        remaining_time = self.printers[printer_name].get_remaining_time()
        return remaining_time if remaining_time > 0 else 0

    @printer_exists
    def get_percentage(self, printer_name: str) -> int:
        """
        Get the percentage of the print job

        Parameters
        ----------
        printer_name : str
            The name of the printer to get the percentage for

        Returns
        -------
        int
            The percentage of the print job
        """
        logging.info("Printer name: %s", printer_name)
        percentage = self.printers[printer_name].get_percentage()
        return percentage if percentage > 0 else 0

    @printer_exists
    def get_frame(self, printer_name: str) -> str:
        """
        Get the frame of the print job

        Parameters
        ----------
        printer_name : str
            The name of the printer to get the frame for

        Returns
        -------
        str
            The frame of the print job
        """
        logging.info("Printer name: %s", printer_name)
        frame = self.printers[printer_name].get_frame()
        self.__printer_cache[printer_name]["frame"] = frame if frame else self.__printer_cache[printer_name]["frame"]  # noqa # pylint: disable=line-too-long
        return self.__printer_cache[printer_name]["frame"]

    @printer_exists
    def get_state(self, printer_name: str) -> GcodeState:
        """
        Get the state of the printer

        Parameters
        ----------
        printer_name : str
            The name of the printer to get the state for

        Returns
        -------
        State
            The state of the printer
        """
        logging.info("Printer name: %s", printer_name)
        state = self.printers[printer_name].get_state()
        return GcodeState(state)

    def get_printers(self) -> list[str]:
        """
        Get the list of printers

        Returns
        -------
        list[str]
            The list of printers
        """
        return list(self.printers.keys())
