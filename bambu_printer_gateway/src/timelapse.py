import asyncio
import base64
import collections
from io import BytesIO
import io
import logging
from typing import List
from PIL import Image

from bambulabs_api import GcodeState, Printer


class Timelapse:
    def __init__(self, printer: Printer, sleep=5) -> None:
        self.state_queue = collections.deque([], maxlen=5)
        self.last_timelapse = []
        self.current_timelapse_buffer: List[Image.Image] = []
        self.printer = printer

        self.timelapse_sleep = sleep

    async def timelapse_task(self):
        while True:
            try:
                state = GcodeState(self.printer.get_state())
                if state == GcodeState.RUNNING:
                    self.current_timelapse_buffer.append(
                        Image.open(
                            io.BytesIO(base64.b64decode(
                                self.printer.get_camera_frame())))
                    )
                elif state != GcodeState.PAUSE:
                    if self.current_timelapse_buffer:
                        self.last_timelapse = self.current_timelapse_buffer
                        self.current_timelapse_buffer = []

            except Exception as e:
                logging.error(f"Error encountered with timelapse: {e}")

            await asyncio.sleep(self.timelapse_sleep)

    def get_timelapse(self, timelapse_speed, timelapse_skip):
        if not self.last_timelapse:
            return None

        im: list[Image.Image] = self.last_timelapse

        try:
            with BytesIO() as buffer:
                im[0].save(buffer, format='GIF', save_all=True,
                           append_images=im[1:][::timelapse_skip],
                           optimize=False,
                           duration=int((1000 * 1/timelapse_speed)/6),
                           loop=0)
                buffer.seek(0)
                return buffer.getbuffer().tobytes()
        except Exception as e:
            logging.error(f"Error creating timelapse: {e}")
            return None
