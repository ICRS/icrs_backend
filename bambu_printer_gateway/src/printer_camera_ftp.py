import os
import ssl
from io import BytesIO
import tempfile
import ftplib
import cv2


__all__ = ["PrinterCamera"]


class ImplicitFTP_TLS(ftplib.FTP_TLS):
    """FTP_TLS subclass that automatically wraps sockets in SSL to support implicit FTPS."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sock = None

    @property
    def sock(self):
        """Return the socket."""
        return self._sock

    @sock.setter
    def sock(self, value):
        """When modifying the socket, ensure that it is ssl wrapped."""
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value)
        self._sock = value


class PrinterCamera:
    def __init__(self, ftp_server, ftp_password):
        self.__ftp_port = 990
        self.__ftp_user = "bblp"
        self.__ftp_server = str(ftp_server)
        self.__ftp_password = str(ftp_password)
        self.__ftps = None

        self.last_frame = None

    def connect(self):
        try:
            self.__ftps = ImplicitFTP_TLS()
            self.__ftps.connect(host=self.__ftp_server, port=self.__ftp_port)
            self.__ftps.login(self.__ftp_user, self.__ftp_password)
            self.__ftps.prot_p()
        except Exception as e:
            print(str(e))
            raise e

    def __del__(self):
        self.__ftps.quit()

    def get_frame(self):
        self.__get_last_frame()
        return self.last_frame

    def __get_last_frame(self):
        error = None
        try:
            self.__ftps.cwd("timelapse")
            ipcam_files = self.__ftps.nlst()
            latest_ipcam_file = max(ipcam_files)
            with BytesIO() as file_in_memory:
                self.__ftps.retrbinary(
                    'RETR ' + "/timelapse/" + latest_ipcam_file,
                    file_in_memory.write, 524288)
                file_in_memory.seek(0)
                video_bytes = file_in_memory.read()

                with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix='.avi') as temp_video_file:

                    temp_video_file.write(video_bytes)
                    temp_video_path = temp_video_file.name

                cap = cv2.VideoCapture(temp_video_path)
                if not cap.isOpened():
                    error = "Error opening video file"
                else:
                    cap.set(cv2.CAP_PROP_POS_FRAMES,
                            cap.get(cv2.CAP_PROP_FRAME_COUNT) - 2)
                    ret, last_frame = cap.read()
                    if not ret:
                        error = "Failed to read the last frame."
                    else:
                        self.last_frame = last_frame

                cap.release()
                os.remove(temp_video_path)

        except Exception as e:
            error = str(e)

        if error is not None:
            print(error)
            raise Exception(error)


"""
Example Usage:

server = IP_ADDRESS
password = BAMBU_LABS_ACCESS_CODE

printer_camera = PrinterCamera(server, password)

frame = printer_camera.get_frame()
"""
