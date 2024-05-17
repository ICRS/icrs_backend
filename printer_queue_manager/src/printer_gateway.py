import requests
import logging
import zipfile
import io


__all__ = ['PrinterGateway']


class PrinterGateway:
    """
    Printer Gateway Class to query REST endpoints
    to get information about the printers
    """

    def __init__(self, printer_url, type="p1p"):
        self.printer_url = printer_url
        self.type = type

    def __str__(self):
        return f"PrinterGateway({self.printer_url}, {self.type})"

    def create_zip_archive_in_memory(
            self,
            text_content: str,
            text_file_name: str = 'file.txt') -> io.BytesIO:
        """
        Create a zip archive in memory

        Args:
            text_content (str): content of the text file
            text_file_name (str, optional): location of the text file.
                Defaults to 'file.txt'.

        Returns:
            io.BytesIO: zip archive in memory
        """
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(text_file_name, text_content)
        zip_buffer.seek(0)
        return zip_buffer

    def start_print(self,
                    gcode: str,
                    filename: str,
                    use_ams: bool = True,
                    ams_mapping: list[int] = [0]) -> None:
        """
        Start the print job

        Parameters
        ----------
        gcode : str
            The gcode to print
        filename : str
            The filename to use
        use_ams : bool
            Use AMS
        ams_mapping : list[int]
            AMS trays to use
        """
        filename += ".3mf"
        gcode_location = "Metadata/plate_1.gcode"
        p = self.create_zip_archive_in_memory(gcode, gcode_location)

        logging.info(f"Starting print on {self.printer_url}")
        response = requests.post(
            f"http://{self.printer_url}/printer/print/3mf",
            params={"filename": filename,
                    "plate_number": 1,
                    "use_ams": use_ams,
                    },
            files={"file": (filename, p.read())},
            json={"ams_mapping": ams_mapping}
        )

        if response.status_code != 200:
            raise Exception("Error starting print job")

    def printer_availability(self) -> bool:
        logging.info(f"Getting availability of printer on {self.printer_url}")
        response = requests.get(
            f"http://{self.printer_url}/printer/available"
        )
        return response.json() if response.status_code == 200 else False
