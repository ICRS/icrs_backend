import requests
import logging

import bambulabs_api as blapi
from fastapi import UploadFile

__all__ = ['PrinterGateway']


class PrinterGateway:
    """
    Printer Gateway Class to query REST endpoints
    to get information about the printers
    """

    def __init__(self, printer_url, type="p1p"):
        self.printer_url = printer_url
        self.type = type
        self.data = {}

    def __str__(self):
        return f"PrinterGateway({self.printer_url}, {self.type}, {self.data})"

    def get_remaining_time(self) -> int:
        """
        Get the remaining time of the print job

        Returns
        -------
        int
            The remaining time of the print job
        """
        response = requests.get(
            f"http://{self.printer_url}/printer/status/time"
        )
        if response.status_code != 200:
            return -1
        r = response.json()
        self.data.update({"time": r['time'] if 'time' in r else -1})
        return self.data.get("time", -1)

    def get_percentage(self) -> int:
        """
        Get the percentage of the print job

        Returns
        -------
        int
            The percentage of the print job
        """
        response = requests.get(
            f"http://{self.printer_url}/printer/status/percentage")
        if response.status_code != 200:
            return -1
        r = response.json()
        self.data.update(
            {"percentage": r['percentage'] if 'percentage' in r else -1})
        return self.data.get("percentage", -1)

    def get_state(self) -> str:
        """
        Get the state of the printer

        Returns
        -------
        str
            The state of the printer
        """
        url = f"http://{self.printer_url}/printer/status/state"
        response = requests.get(url)
        logging.info(f"Update State {url}: {response}")
        if response.status_code != 200:
            return "UNKNOWN"
        r: dict = response.json()
        self.data.update({"state": blapi.GcodeState(r.get("state", "IDLE"))})
        return r.get("state", blapi.GcodeState.IDLE)

    def upload_gcode(self, gcode: UploadFile) -> None:
        """
        Upload the gcode to the printer

        Parameters
        ----------
        gcode : str
            The gcode to upload
        """
        response = requests.post(
            f"http://{self.printer_url}/printer/upload/gcode",
            files={"file": gcode}
        )
        if response.status_code != 200:
            raise Exception("Error uploading gcode")

    def start_print(self, filename: str, plater_number: int) -> None:
        """
        Start the print job

        Parameters
        ----------
        filename : str
            The filename of the gcode
        plater_number : int
            The plate number of the print job
        """
        response = requests.post(
            f"http://{self.printer_url}/printer/print/start",
            json={"filename": filename, "plate_number": plater_number}
        )
        if response.status_code != 200:
            raise Exception("Error starting print job")
        self.data.update({"state": blapi.GcodeState.RUNNING})
