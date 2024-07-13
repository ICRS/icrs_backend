import asyncio
import base64
import collections
from io import BytesIO
import io
import logging
from PIL import Image

from bambulabs_api import GcodeState, Printer


class Timelapse:
    def __init__(self, printer: Printer) -> None:
        self.state_queue = collections.deque([], maxlen=5)
        self.last_timelapse = []
        self.current_timelapse_buffer = []
        self.printer = printer

    async def timelapse_task(self):
        while True:
            state = GcodeState(self.printer.get_state())
            if state == GcodeState.RUNNING:
                self.current_timelapse_buffer.append(
                    Image.open(
                        io.BytesIO(base64.b64decode(
                            self.printer.get_camera_frame())))
                )
                print("adding image")
            elif state != GcodeState.PAUSE:
                if self.current_timelapse_buffer:
                    self.last_timelapse = self.current_timelapse_buffer
                    self.current_timelapse_buffer = []

            await asyncio.sleep(1)

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
