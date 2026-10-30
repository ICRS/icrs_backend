"""
Camera client for printers that serve their camera as RTSPS on port 322
(P2S, X1, H2D with "LAN Only Liveview" on). P1/A1 printers use the port 6000
stream instead, which bambulabs_api's PrinterCamera already handles.
"""

__all__ = ["RtspsCamera", "RTSPS_PORT"]

import base64
import logging
import os
import time
from threading import Thread

# Must be set before the first VideoCapture; RTP over UDP can't pass the NAT
# between the cluster and the printers.
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")
import cv2  # noqa: E402

RTSPS_PORT = 322


class RtspsCamera:
    """
    Drop-in replacement for bambulabs_api's PrinterCamera (same start, stop,
    get_frame, last_frame and alive), so Printer.get_camera_frame() works
    unchanged. Every frame is decoded to keep the stream in sync, but only
    one every FRAME_INTERVAL seconds is JPEG-encoded and kept.
    """
    FRAME_INTERVAL = 0.5

    def __init__(self, hostname: str, access_code: str,
                 port: int = RTSPS_PORT, username: str = "bblp"):
        self.__url = (f"rtsps://{username}:{access_code}@{hostname}:{port}"
                      "/streaming/live/1")
        self.__hostname = hostname
        self.__thread = None
        self.last_frame = None
        self.alive = False

    def start(self):
        if self.alive:
            return False
        self.alive = True
        self.__thread = Thread(target=self.retriever, daemon=True)
        self.__thread.start()
        return True

    def stop(self):
        self.alive = False
        if self.__thread is not None:
            self.__thread.join()
            self.__thread = None

    def get_frame(self):
        if self.last_frame is None:
            raise Exception("No frame available.")  # noqa  # pylint: disable=broad-exception-raised
        return base64.b64encode(self.last_frame).decode("utf-8")

    def retriever(self):
        while self.alive:
            cap = cv2.VideoCapture(self.__url, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                logging.error(f"RTSPS camera at {self.__hostname} did not open")
                time.sleep(5)
                continue
            logging.info(f"RTSPS camera at {self.__hostname} connected")
            next_frame = 0.0
            while self.alive and cap.grab():
                now = time.monotonic()
                if now < next_frame:
                    continue
                next_frame = now + self.FRAME_INTERVAL
                ok, image = cap.retrieve()
                if ok:
                    ok, jpeg = cv2.imencode(".jpg", image)
                if ok:
                    self.last_frame = jpeg.tobytes()
            cap.release()
            if self.alive:
                logging.error(f"RTSPS camera at {self.__hostname} stream ended, reconnecting")
                time.sleep(5)
