from io import BytesIO
import os
import cProfile
import pstats

from PIL import Image
from concurrent.futures import ThreadPoolExecutor

from .gcode import GCode
from .grapher import Grapher

__all__ = ["gcode2img"]


def profile_code():
    profiler = cProfile.Profile()
    profiler.enable()

    # Replace this with your actual code to generate the image
    imager = gcode2img()
    img_bytes = imager.gcode2img(filename="cube.gcode", gif=False, frames=30)

    profiler.disable()
    return profiler


def print_stats(profiler):
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(10)  # Print top 10 functions by cumulative time


class gcode2img:
    def __init__(self):
        self.gcode = None

    def gcode2img(self, gcode: GCode | str | None = None,
                  filename: str | None = None,
                  base_dir: str | None = None,
                  gif: bool = False,
                  frames: int = 30) -> BytesIO:
        if gcode:
            if isinstance(gcode, str):
                self.gcode = GCode(gcode)
            elif isinstance(gcode, GCode):
                self.gcode = gcode
            else:
                raise ValueError("gcode must be a new-line-separated string or GCode object")
        elif filename:
            base_dir = base_dir or os.getcwd()
            full_path = os.path.join(base_dir, filename)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    self.gcode = GCode(f.read())
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"File {full_path} not found") from exc
        else:
            raise ValueError("Either gcode or filename must be provided")

        grapher = Grapher(self.gcode)
        grapher.trace()

        def generate_frame(i):
            print(f"Generating frame {i + 1} of {frames}")
            return grapher.render(percentage=(i + 1) / frames)

        output = BytesIO()
        if gif:
            with ThreadPoolExecutor() as executor:
                gif_frames = list(executor.map(generate_frame, range(frames)))

            gif_frames[0].save(output, format="GIF", save_all=True,
                               append_images=gif_frames[1:], loop=0)
        else:
            img = grapher.render()
            img.save(output, format="PNG")

        output.seek(0)
        return output


if __name__ == "__main__":
    profiler = profile_code()
    print_stats(profiler)
