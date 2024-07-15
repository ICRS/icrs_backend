import asyncio
import base64
from io import BytesIO
import io
import logging
from PIL import Image

from bambulabs_api import GcodeState, Printer
import av

WIDTH = 1280
HEIGHT = 720


class Timelapse:
    def __init__(self, printer: Printer, sleep=10) -> None:
        self.last_timelapse: BytesIO = None
        self.printer = printer

        self.running = False

        self.__init_current_stream()

        self.timelapse_sleep = sleep

    def __init_current_stream(self):
        self.current_timelapse_buffer = io.BytesIO()

        self.current_output = av.open(
            self.current_timelapse_buffer, "w", format='webm')

        self.stream = self.current_output.add_stream("vp9", str(10))
        self.stream.height = HEIGHT
        self.stream.width = WIDTH

    async def timelapse_task(self):
        while True:
            try:
                state = GcodeState(self.printer.get_state())
                if state == GcodeState.RUNNING:
                    self.running = True

                    packet = self.stream.encode(
                        av.VideoFrame.from_image(Image.open(
                            io.BytesIO(base64.b64decode(
                                self.printer.get_camera_frame())))
                        ))
                    self.current_output.mux(packet)

                elif state != GcodeState.PAUSE:
                    if self.running:
                        self.running = False

                        packet = self.stream.encode(None)
                        self.current_output.mux(packet)
                        self.current_output.close()

                        # Make Current Timelapse the saved timelapse
                        self.last_timelapse.close()
                        self.last_timelapse = self.current_timelapse_buffer

                        self.__init_current_stream()

            except Exception as e:
                logging.error(f"Error encountered with timelapse: {e}")

            await asyncio.sleep(self.timelapse_sleep)

    def get_timelapse(self) -> None | bytes:
        if not self.last_timelapse:
            return None

        buffer = self.last_timelapse.getbuffer()

        if buffer.nbytes:
            return buffer.tobytes()
        else:
            return None
