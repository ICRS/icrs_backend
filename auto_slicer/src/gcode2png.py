import os
import click
import logging
import math
import sys

from mayavi import mlab
from tvtk.api import tvtk

from .gcodeParser import GcodeParser, preg_match


logger = logging.getLogger(__name__)
FORMAT = (
    "[%(asctime)s %(filename)s->%(funcName)s():%(lineno)s]%(levelname)s: %(message)s" # noqa
)
logging.basicConfig(format=FORMAT)
logger.setLevel(os.environ.get("LOGLEVEL", "INFO"))  # noqa: notice, DEBUG is SUPER slow 

logger2 = logging.getLogger("tvtk")
logger2.setLevel(level=logging.CRITICAL)
logger3 = logging.getLogger("mayavi")
logger3.setLevel(level=logging.CRITICAL)


class GcodeRenderer:
    def __init__(self):
        self.imgwidth = 1600
        self.imgheight = 1200

        self.path = ""
        self.support = False
        self.moves = False
        self.show = False
        self.bed = False

        self.scene = None

        self.coords = {"object": {}, "moves": {}, "support": {}}
        self.coords["object"]["x"] = [0]
        self.coords["object"]["y"] = [0]
        self.coords["object"]["z"] = [0]
        self.coords["moves"]["x"] = [0]
        self.coords["moves"]["y"] = [0]
        self.coords["moves"]["z"] = [0]
        self.coords["support"]["x"] = [0]
        self.coords["support"]["y"] = [0]
        self.coords["support"]["z"] = [0]

        self.bedsize = [250, 210]  # should match bed_texture.jpg
        red = (1, 0, 0)
        lightgrey = (0.7529, 0.7529, 0.7529)
        blue = (0, 0.4980, 0.9960)
        mediumgrey = (0.7, 0.7, 0.7)
        darkgrey1 = (0.4509, 0.4509, 0.4509)

        self.bgcolor = darkgrey1
        self.supportcolor = lightgrey
        self.extrudecolor = red
        self.bedcolor = mediumgrey
        self.movecolor = blue

        mlab.options.offscreen = True

    def run(
        self,
        path: str,
        support: bool,
        moves: bool,
        bed: bool,
        show: bool,
        target: str,
        imgx: int,
        imgy: int,
    ):
        """Run general processing

        Args:
            path(str): gcode file to read
            support(bool): render supports
            moves(bool): render moves
            bed(bool): render bed
            show(bool): if set to true then show only window with preview,
                without file save
            target(str): filename to write output image, if set
            imgx(int): image size x to render (pixels)
            imgy(int): image size y to render (pixels)

        """
        self.path = path
        self.target = target
        self.support = support
        self.moves = moves
        self.bed = bed
        self.imgwidth = imgx
        self.imgheight = imgy
        self.show = show

        if self.show:
            mlab.options.offscreen = False

        self.createScene()

        self.createBed()

        self.loadGcode(self.path)
        self.plotModel()
        self.plotMoves()
        self.plotSupport()
        self.generateScene()

        self.showScene()

        mlab.close(all=True)

        return self.get_image()

    def processSegment(self, segment, target):
        """Process given gcode segment"""

        logger.debug("segment= %s" % str(segment))
        m = []
        # we assume that everything is a move, this is not great but helps
        # in avoiding specific things to be rendered
        target = "moves"
        rule = "undefined"

        if preg_match(r"(custom|wipe)", segment.type, m):
            target = "moves"
            rule = "custom"

        elif preg_match(r"(intern|skirt|support)", segment.type, m):
            target = "support"
            rule = "support"

        elif preg_match(
            r"(bridge|external|fill|infill|overhang|perimeter|skin|solid|top|wal)",  # noqa
            segment.type,
            m,
        ):
            target = "object"
            rule = "solid"

        # special treatment for special moves
        if target == "object":
            if segment.style in ["fly", "retract"]:
                target = "moves"
                rule = "obj_special"

        self.coords[target]["x"].append(segment.coords["X"])
        self.coords[target]["y"].append(segment.coords["Y"])
        self.coords[target]["z"].append(segment.coords["Z"])
        logger.debug("rule: %s, segment assigned to %s" % (rule, target))

    def loadGcode(self, path: str):
        """Load gcode to render from given path

        Processes gcode file and saves each gcode command to x/y/z action.

        """

        logger.info("loading file %s ..." % path)
        parser = GcodeParser()
        model = parser.parseFile(path)
        logger.info("model.layers=%s ..." % len(model.layers))

        for layer in model.layers:
            for seg in layer.segments:
                self.processSegment(seg, seg.style)

        logger.info("done")

    def createScene(self):
        """Create 3D scene in mayavi"""
        logger.info("creating scene")
        fig1 = mlab.figure(bgcolor=self.bgcolor, size=(
            self.imgwidth, self.imgheight))
        fig1.scene.parallel_projection = False
        fig1.scene.render_window.point_smoothing = False
        fig1.scene.render_window.line_smoothing = False
        fig1.scene.render_window.polygon_smoothing = False
        fig1.scene.render_window.multi_samples = 8
        if self.show:
            fig1.scene.show_axes = False
        self.scene = fig1
        logger.info("done")

    def createBed(self):
        """Create bed mesh with a texture"""
        if not self.bed:
            logger.info("skipping creating bed")
            return

        logger.info("creating bed")

        _x = self.bedsize[0]
        _y = self.bedsize[1]

        x1, y1, z1 = (0, _y, 0)
        x2, y2, z2 = (_x, _y, 0)
        x3, y3, z3 = (0, 0, 0)
        x4, y4, z4 = (_x, 0, 0)

        bed = mlab.mesh(
            [[x1, x2], [x3, x4]],
            [[y1, y2], [y3, y4]],
            [[z1, z2], [z3, z4]],
            color=self.bedcolor,
        )

        bed_texture = sys.path[0] + "/bed_texture.jpg"
        logger.info("loading bed image %s" % bed_texture)

        img = tvtk.JPEGReader(file_name=bed_texture)
        texture = tvtk.Texture(
            input_connection=img.output_port, interpolate=1, repeat=0
        )
        bed.actor.actor.texture = texture
        bed.actor.tcoord_generator_mode = "plane"

        logger.info("done")

    def plotModel(self) -> None:
        """
        Generate layers defined as objects without supports or other moves
        """
        logger.info(
            "object x/y/z = %s/%s/%s"
            % (
                len(self.coords["object"]["x"]),
                len(self.coords["object"]["y"]),
                len(self.coords["object"]["z"]),
            )
        )

        if not len(self.coords["object"]["x"]):
            logger.warning("no object, nothing to process")
            return

        logger.info(
            "dropping first 5 lines from model to avoid rendering weird purge lines"  # noqa
        )
        for i in range(5):
            if len(self.coords["object"]["x"]) > 0:
                self.coords["object"]["x"].pop(0)
                self.coords["object"]["y"].pop(0)
                self.coords["object"]["z"].pop(0)

        logger.info("generating model")
        mlab.plot3d(
            self.coords["object"]["x"],
            self.coords["object"]["y"],
            self.coords["object"]["z"],
            color=self.extrudecolor,
            # line_width=2.0,
            # representation="wireframe",
            tube_radius=0.5,
        )

        logger.info("done")

    def plotMoves(self):
        """Generate layers defined as moves"""
        logger.info(
            "moves x/y/z = %s/%s/%s"
            % (
                len(self.coords["moves"]["x"]),
                len(self.coords["moves"]["y"]),
                len(self.coords["moves"]["z"]),
            )
        )

        if not self.moves:
            logger.info("skipping generating moves")
            return

        if not len(self.coords["moves"]["x"]):
            logger.info("no moves, nothing to process")
            return

        logger.info("generating moves")
        mlab.plot3d(
            self.coords["moves"]["x"],
            self.coords["moves"]["y"],
            self.coords["moves"]["z"],
            color=self.movecolor,
            tube_radius=0.5,
        )
        logger.info("done")

    def plotSupport(self):
        """Generate layers defined as supports"""
        logger.info(
            "support x/y/z = %s/%s/%s"
            % (
                len(self.coords["support"]["x"]),
                len(self.coords["support"]["y"]),
                len(self.coords["support"]["z"]),
            )
        )

        if not self.support:
            logger.info("skipping generating supports")
            return

        if not len(self.coords["support"]["x"]):
            logger.info("no supports, nothing to process")
            return

        logger.info("generating supports")
        mlab.plot3d(
            self.coords["support"]["x"],
            self.coords["support"]["y"],
            self.coords["support"]["z"],
            color=self.supportcolor,
            tube_radius=0.5,
        )
        logger.info("done")

    def generateScene(self):
        """Generate overall 3D scene with camera"""
        logger.info("generating scene")

        # setting distance to auto will take bed and model and final print head
        # moves into account, and usually preview ends being too small
        # distance = "auto"

        # get printed object min/max dimensions, will be used to
        # calculate automatically best camera position
        # notice that if model is misplaced then it will be not on the bed,
        # but we still want to see the preview.

        x_min = min(self.coords["object"]["x"])
        x_max = max(self.coords["object"]["x"])
        y_min = min(self.coords["object"]["y"])
        y_max = max(self.coords["object"]["y"])
        z_min = min(self.coords["object"]["z"])
        z_max = max(self.coords["object"]["z"])
        dimension_x = x_max - x_min
        dimension_y = y_max - y_min
        dimension_z = z_max - z_min
        obj_pos_x = (x_min + x_max) / 2
        obj_pos_y = (y_min + y_max) / 2
        obj_pos_z = (z_min + z_max) / 2

        distance = 2 * math.sqrt(
            math.pow(dimension_x, 2)
            + math.pow(dimension_y, 2)
            + math.pow(dimension_z, 2)
        )
        focalpoint = (obj_pos_x, obj_pos_y, obj_pos_z)
        # 225,45 is standard PrusaSlicer preview angle from point 0,0
        # but way higher, towards the center of the print object
        mlab.view(azimuth=225,
                  elevation=45,
                  distance=distance,
                  focalpoint=focalpoint)
        logger.info("done")

    def showScene(self):
        """show 3D scene in mlab as actual interactive window"""
        if not self.show:
            logger.info("skipping showing scene")
            return

        logger.info("showing scene")
        mlab.show()
        logger.info("done")

    def save(self):
        """Save 3D view to image"""
        if not self.target:
            logger.info("skipping saving image")
            return

        logger.info("preparing to save image")
        img_path = self.target
        logger.info("mlab.savefig=%s" % img_path)
        mlab.savefig(img_path)
        logger.info("img.save=%s" % img_path)

    def get_image(self):
        """Return image as numpy array"""
        return mlab.screenshot(antialiased=True)


@click.command()
@click.option("--bed", default=True, help="Show bed")
@click.option("--supports", default=False, help="Show supports")
@click.option("--moves", default=False, help="Show moves")
@click.option("--show", default=False, help="Show preview window")
@click.option("--imgx", default=1600, help="Saved image X in pixels")
@click.option("--imgy", default=1200, help="Saved image Y in pixels")
@click.argument("source", type=click.Path(exists=True))
@click.argument("target", type=click.Path(), required=False)
def gcode2png(source, bed, supports, moves, show, target, imgx, imgy):
    """Process input filename and based on file name create PNG file

    Example input is test.gcode, then output will be test.png

    Output will be overwritten, if exists.

    """

    renderer = GcodeRenderer()
    if target is not None:
        target = click.format_filename(target)
    renderer.run(
        path=source,
        support=supports,
        moves=moves,
        bed=bed,
        show=show,
        target=target,
        imgx=imgx,
        imgy=imgy,
    )


if __name__ == "__main__":
    gcode2png()
