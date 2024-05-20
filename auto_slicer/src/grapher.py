from functools import cache
import logging
import plotly.graph_objects as go
from PIL import Image
import numpy as np
import io
from .gcode import GCode

__all__ = ['Grapher']


class Grapher:
    def __init__(self, gcode: GCode):
        self.gcode = gcode
        self.fig = None
        self.dimensions = {"X": 0, "Y": 0, "Z": 0}
        self.absolute_positioning = True
        self.units = 'mm'
        self.x_coords = np.array([], dtype=float)
        self.y_coords = np.array([], dtype=float)
        self.z_coords = np.array([], dtype=float)

    def trace(self):
        # Create a 3D plot
        self.fig = go.Figure()
        self.fig.update_scenes(aspectmode='cube')

        camera = dict(
            up=dict(x=0, y=0, z=1),
            center=dict(x=0, y=0, z=0),
            eye=dict(x=0.9, y=0.9, z=0.9)
        )

        self.fig.update_layout(scene_camera=camera)

        conf = self.gcode.configs()
        dimensions = conf.get("printable_area").split(",")[2].strip()
        x, y = dimensions.split("x")
        z = conf.get("printable_height").strip()

        self.dimensions["X"] = float(x)
        self.dimensions["Y"] = float(y)
        self.dimensions["Z"] = float(z)

        self.fig.update_layout(scene=dict(
            xaxis=dict(range=[0, self.dimensions["X"]],
                       showticklabels=False,
                       showgrid=True, zeroline=True),
            yaxis=dict(range=[0, self.dimensions["Y"]],
                       showticklabels=False,
                       showgrid=True, zeroline=True),
            zaxis=dict(range=[0, self.dimensions["Z"]],
                       showticklabels=False,
                       showgrid=True, zeroline=True)
        ))

        self.fig.update_layout(
            paper_bgcolor='rgb(115, 115, 115)',
            scene=dict(
                xaxis=dict(
                    backgroundcolor="rgb(185, 185, 185)",
                    gridcolor="black",
                    showbackground=True,
                    zerolinecolor="black"),
                yaxis=dict(
                    backgroundcolor="rgb(185, 185, 185)",
                    gridcolor="black",
                    showbackground=True,
                    zerolinecolor="white"),
                zaxis=dict(
                    backgroundcolor="rgb(185, 185, 185)",
                    gridcolor="black",
                    showbackground=True,
                    zerolinecolor="black")),
            margin=dict(r=10, l=10, b=10, t=10))

        current_position = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        x_moves, y_moves, z_moves = [current_position['X']], [current_position['Y']], [current_position['Z']]

        m = 0
        m_total = len(self.gcode.moves())
        for move in self.gcode.moves():
            print(f"Tracing move {m}/{m_total}")
            number = move.number
            params = move.parameters

            if number in {'0', '1'}:  # Linear move
                x = float(params.get('X', current_position['X']))
                y = float(params.get('Y', current_position['Y']))
                z = float(params.get('Z', current_position['Z']))

                if not self.absolute_positioning:
                    x += current_position['X']
                    y += current_position['Y']
                    z += current_position['Z']

                x_moves.append(x)
                y_moves.append(y)
                z_moves.append(z)

                current_position.update({'X': x, 'Y': y, 'Z': z})

            elif number in {'2', '3'}:  # Arc move
                x_center = float(params.get('I', 0) + current_position['X'])
                y_center = float(params.get('J', 0) + current_position['Y'])
                radius = np.sqrt((current_position['X'] - x_center) ** 2 + (current_position['Y'] - y_center) ** 2)
                start_angle = np.arctan2(current_position['Y'] - y_center, current_position['X'] - x_center)
                end_angle = np.arctan2(float(params.get('Y', current_position['Y'])) - y_center,
                                       float(params.get('X', current_position['X'])) - x_center)
                angles = np.linspace(start_angle, end_angle, 100)
                arc_x = x_center + radius * np.cos(angles)
                arc_y = y_center + radius * np.sin(angles)
                arc_z = np.linspace(current_position['Z'], float(params.get('Z', current_position['Z'])), 100)

                x_moves.extend(arc_x)
                y_moves.extend(arc_y)
                z_moves.extend(arc_z)

                current_position.update({'X': arc_x[-1], 'Y': arc_y[-1], 'Z': arc_z[-1]})

            elif number == '20':  # Set units to inches
                self.units = 'inches'

            elif number == '21':  # Set units to mm
                self.units = 'mm'

            elif number == '28':  # Move to origin
                x_moves.append(0)
                y_moves.append(0)
                z_moves.append(0)
                current_position = {'X': 0, 'Y': 0, 'Z': 0}

            elif number == '90':  # Absolute positioning
                self.absolute_positioning = True

            elif number == '91':  # Relative positioning
                self.absolute_positioning = False

            elif number == '92':  # Set position
                current_position.update({
                    'X': float(params.get('X', current_position['X'])),
                    'Y': float(params.get('Y', current_position['Y'])),
                    'Z': float(params.get('Z', current_position['Z']))
                })

            m += 1

        self.x_coords = np.array(x_moves)
        self.y_coords = np.array(y_moves)
        self.z_coords = np.array(z_moves)

    def render(self, percentage: float = 1.0) -> Image.Image:
        if self.fig is None:
            raise RuntimeError("You need to call trace() before render().")

        pct = int(len(self.x_coords) * percentage)
        x_coords = self.x_coords[:pct]
        y_coords = self.y_coords[:pct]
        z_coords = self.z_coords[:pct]

        logging.info(f"Rendering {len(x_coords)} coordinates")

        self.fig.add_trace(go.Scatter3d(
            x=x_coords, y=y_coords, z=z_coords,
            mode='lines',
            line=dict(color='red', width=0.02),
            showlegend=False
        ))
        self.fig.add_trace(go.Scatter3d(
            x=x_coords, y=y_coords, z=z_coords-0.01,
            mode='lines',
            line=dict(color='black', width=0.01),
            showlegend=False
        ))

        logging.info("Converting to image...")
        img_bytes = self.fig.to_image(format='png',
                                      scale=0.25,
                                      width=640,
                                      height=480,
                                      validate=False)
        buf = io.BytesIO(img_bytes)
        buf.seek(0)
        logging.info("Converting to image... Done")

        return Image.open(buf)
