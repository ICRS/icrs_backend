import asyncio
import os
import ftplib
from io import BytesIO
import ssl
import tempfile
from threading import Thread
import time

import cv2
from fastapi.responses import StreamingResponse


__all__ = ["PrinterCamera"]


def convert_bytes(size, precision=4):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    suffixIndex = 0
    while size > 1024 and suffixIndex < 4:
        suffixIndex += 1  # increment the index of the suffix
        size = size / 1024.0  # apply the division
    return "%.*f%s" % (precision, size, suffixes[suffixIndex])


class ImplicitFTP_TLS(ftplib.FTP_TLS):
    """
    FTP_TLS subclass that automatically wraps
    sockets in SSL to support implicit FTPS.
    """

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

        self.__thread = Thread(target=self.__retriever)
        self.__thread.daemon = True

        self.last_file = None
        self.last_frame = None

    def connect(self):
        try:
            self.__ftps = ImplicitFTP_TLS()
            self.__ftps.connect(host=self.__ftp_server, port=self.__ftp_port)
            self.__ftps.login(self.__ftp_user, self.__ftp_password)
            status = self.__ftps.prot_p()
            print("FTP Status: ", status)

            self.__thread.start()

        except Exception as e:
            print(str(e))
            raise e

    def __retriever(self):
        while True:
            try:
                self.__get_last_frame()
            except Exception as e:
                print(str(e))
            time.sleep(15)

    def disconnect(self):
        self.__ftps.quit()

    def get_frame(self):
        if self.last_frame is None:
            raise Exception("No frame available.")
        try:
            res, im_png = cv2.imencode(".png", self.last_frame)
            if not res:
                raise Exception("Failed to encode the frame.")
        except Exception as e:
            raise Exception(str(e))
        return StreamingResponse(BytesIO(im_png.tobytes()),
                                 media_type="image/png")

    def __get_last_frame(self, folder="ipcam"):
        print("Getting last frame...")
        error = None
        try:
            self.__ftps.cwd(folder)
            ipcam_files = self.__ftps.nlst()
            latest_ipcam_file = max(ipcam_files)
            if not latest_ipcam_file:
                error = "No files found."
                raise Exception(error)
            if not self.last_file:
                self.last_file = latest_ipcam_file
            # Check if latest file is different from last file
            if latest_ipcam_file != self.last_file:
                latest_file = max([latest_ipcam_file, self.last_file])
                if latest_file == latest_ipcam_file:
                    self.last_file = latest_ipcam_file
                else:
                    error = "Latest file is not the same as the last file."
                    raise Exception(error)

            num_bytes = 720 * 1280 * 3
            file = f"/{folder}/" + self.last_file
            self.__ftps.voidcmd('TYPE I')
            filesize = self.__ftps.size(file)

            if filesize == 0:
                error = "File size is 0."
                raise Exception(error)

            offset = max(filesize - num_bytes, 0)
            offset = 0

            print(f"File Size: {convert_bytes(filesize)}")
            print(f"Downloading {file}")

            with BytesIO() as file_in_memory:
                output = self.__ftps.retrbinary(cmd='RETR ' + file,
                                                callback=file_in_memory.write,
                                                blocksize=8192*4)

                file_in_memory.seek(0)
                video_bytes = file_in_memory.read()
                video_bytes = bytearray(video_bytes)

                print(f"Downloaded {convert_bytes(len(video_bytes))}")

                with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix='.avi') as temp_video_file:

                    temp_video_file.write(video_bytes)
                    temp_video_path = temp_video_file.name

                cap = cv2.VideoCapture(temp_video_path)
                if not cap.isOpened():
                    error = "Error opening video file"
                    raise Exception(error)
                else:
                    cap.set(cv2.CAP_PROP_POS_FRAMES,
                            cap.get(cv2.CAP_PROP_FRAME_COUNT) - 2)
                    ret, last_frame = cap.read()
                    if not ret:
                        error = "Failed to read the last frame."
                        raise Exception(error)
                    else:
                        self.last_frame = last_frame
                self.__ftps.delete(file)
                cap.release()
                os.remove(temp_video_path)

        except Exception as e:
            error = str(e)
            raise Exception(error)

        return error


"""
Example Usage:

server = IP_ADDRESS
password = BAMBU_LABS_ACCESS_CODE

printer_camera = PrinterCamera(server, password)
printer_camera.connect()

frame = printer_camera.get_frame()
"""

if __name__ == "__main__":
    # server = "192.168.1.121"
    # password = "15509206"

    server = "192.168.1.125"
    password = "14053862"

    printer_camera = PrinterCamera(server, password)
    printer_camera.connect()

    try:
        frame = printer_camera.get_frame()
    except Exception as e:
        print(str(e))
        printer_camera.disconnect()
        exit(1)

    print("Frame size: ", frame.shape)
    print("Frame type: ", frame.dtype)

    cv2.imshow("Frame", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    printer_camera.disconnect()
    exit(0)