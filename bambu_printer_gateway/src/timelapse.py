import asyncio
import base64
import datetime
import io
import logging
from PIL import Image

from bambulabs_api import GcodeState, Printer
import cv2
import numpy as np
from .printer import PRINTER_NAME


WIDTH = 1280
HEIGHT = 720


class Timelapse:
    def __init__(self, printer: Printer, sleep=10) -> None:
        self.printer = printer
        self.running = False

        self.timelapse_sleep = sleep
        self.last_timelapse_file = None

    def __init_current_stream(self):
        self.current_timelapse_path = (
            f"videos/{PRINTER_NAME}_{datetime.datetime.now()}.webm")

        self.video_writer = cv2.VideoWriter(
            self.current_timelapse_path,
            cv2.VideoWriter_fourcc(*'VP90'),
            10,
            (WIDTH, HEIGHT),)

    async def timelapse_task(self):
        while True:
            try:
                state = GcodeState(self.printer.get_state())
                if state == GcodeState.RUNNING:
                    if not self.running:
                        self.__init_current_stream()

                    self.running = True
                    image = Image.open(
                        io.BytesIO(base64.b64decode(
                            self.printer.get_camera_frame())))

                    self.video_writer.write(
                        cv2.cvtColor(
                            np.asarray(image), cv2.COLOR_RGB2BGR)
                    )

                elif state != GcodeState.PAUSE:
                    if self.running:
                        self.running = False
                        self.video_writer.release()
                        del self.video_writer
                        self.last_timelapse_file = self.current_timelapse_path 

            except Exception as e:
                logging.error(f"Error encountered with timelapse: {e}")

            await asyncio.sleep(self.timelapse_sleep)

    def get_timelapse(self) -> None | bytes:
        if self.last_timelapse_file is None:
            return None
        else:
            with open(self.last_timelapse_file, "rb") as b:
                return b.read()
