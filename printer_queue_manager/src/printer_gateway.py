import requests

__all__ = ['PrinterGateway']


class PrinterGateway:
    """
    Printer Gateway Class to query REST endpoints
    to get information about the printers
    """

    def __init__(self, printer_url):
        self.printer_url = printer_url

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
        return r['time'] if 'time' in r else -1

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
        return r['percentage'] if 'percentage' in r else -1

    def get_frame(self) -> str | None:
        """
        Get the frame of the print job

        Returns
        -------
        str
            The frame of the print job
        """
        response = requests.get(f"http://{self.printer_url}/printer/camera")
        if response.status_code != 200:
            return None
        r: dict = response.json()
        return r['frame'].get("body", "") if 'frame' in r else None

    def get_state(self) -> str:
        """
        Get the state of the printer

        Returns
        -------
        str
            The state of the printer
        """
        response = requests.get(
            f"http://{self.printer_url}/printer/status/state")
        if response.status_code != 200:
            return "UNKNOWN"
        r: dict = response.json()
        return r.get("state", "IDLE")
