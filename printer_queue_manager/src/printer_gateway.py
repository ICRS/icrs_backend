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
            text_content,
            text_file_name='file.txt'):

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(text_file_name, text_content)
        zip_buffer.seek(0)
        return zip_buffer

    def upload_gcode(self, gcode: str, filename: str):
        """
        Upload the gcode to the printer

        Parameters
        ----------
        gcode : str
            The gcode to upload
        """

        filename += ".3mf"
        gcode_location = "Metadata/plate_1.gcode"
        p = self.create_zip_archive_in_memory(gcode, gcode_location)

        response = requests.post(
            f"http://{self.printer_url}/printer/upload/gcode",
            files={"file": (filename, p.read())}
        )
        if response.status_code != 200:
            raise Exception("Error uploading gcode")

        return filename, 1

    def start_print(self, filename: str,
                    plater_number: int,
                    use_ams: bool = True,
                    ams_mapping: list[int] = [0]) -> None:
        """
        Start the print job

        Parameters
        ----------
        filename : str
            The filename of the gcode
        plater_number : int
            The plate number of the print job
        use_ams : bool
            Use AMS
        ams_mapping : list[int]
            AMS trays to use
        """
        logging.info(f"Starting print on {self.printer_url}")
        response = requests.post(
            f"http://{self.printer_url}/printer/print/start",
            params={"filename": filename,
                    "plate_number": plater_number,
                    "use_ams": use_ams,
                    "ams_mapping": ams_mapping
                    }
        )
        if response.status_code != 200:
            raise Exception("Error starting print job")

    def printer_availability(self) -> bool:
        logging.info(f"Getting availability of printer on {self.printer_url}")
        response = requests.get(
            f"http://{self.printer_url}/printer/availability"
        )
        return response.json() if response.status_code == 200 else False
