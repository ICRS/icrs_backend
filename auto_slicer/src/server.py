import json
import base64
from io import BytesIO
import os
import logging
import subprocess
import threading
import numpy as np
import requests
import shutil

import pika
import xml.etree.ElementTree as ET
from fastapi import APIRouter, Query, Response

from PIL import Image

from .printer_asset_utils import AVAILABLE_LAYER_HEIGHT, AVAILABLE_PRINTERS, \
    get_machine, process_from_machine_layer, printer_pla


router = APIRouter()

rabbitmq_settings = json.load(open("rabbitmq.json", "r", encoding="utf-8"))
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
RABBITMQ_QUEUE = rabbitmq_settings["QUEUE"]

credentials = pika.PlainCredentials(
    username=str(RABBITMQ_USERNAME),
    password=str(RABBITMQ_PASSWORD)
)


def render_gcode(filename: str) -> np.array:
    """
    Render gcode file to img

    Args
    ----
        filename (str): filename of the gcode file
    """
    # renderer = GcodeRenderer()  # noqa: F841
    # img = renderer.run(
    #     path=filename,
    #     support=True,
    #     moves=True,
    #     bed=True,
    #     show=False,
    #     target="output.png",
    #     imgx=600,
    #     imgy=400,
    # )
    # print(img)
    img = None
    return img


def gcode_time(filename: str) -> tuple[str] | None:
    """
    Get the model print time and estimated time from the gcode file

    Args:
        filename (str): filename of the gcode file

    Returns:
        tuple[str] | None: model print time and estimated time,
            None if not found
    """
    with open(filename, "r") as file:
        lines = file.readlines()[:4]
        return extract_print_time(lines)


def extract_print_time(lines: list[str]) -> tuple[str] | None:
    """
    Extract the print time from the lines of a gcode file

    Args:
        lines (list[str]): lines of the gcode file

    Returns:
        tuple[str] | None: model print time and estimated time,
    """
    for line in lines:
        if line.startswith("; model printing time:"):
            times = line[1:].split(";")
            model_time = times[0].split(":")[-1].strip()
            estimated_time = times[-1].split(":")[-1].strip()

            return model_time, estimated_time


def bambu_time_conversion(time: str) -> int:
    """
    Convert time from bambu format to minutes.
    Expected Bambu format: "10d 1h 30m 15s"

    Args:
        time (str): time in bambu format

    Returns:
        int: time in seconds
    """
    t = time.split(" ")
    c = 0
    for i in t:
        if "s" in i:
            c += int(i[:-1])
        elif "m" in i:
            c += int(i[:-1])*60
        elif "h" in i:
            c += int(i[:-1])*3600
        elif "d" in i:
            c += int(i[:-1])*86400
    return c


def extract_weight(filename: str) -> float:
    """
    Get weight from xml file (slice_info.config)

    Args:
        filename (str): file of xml config

    Returns:
        float: weight of the file
    """
    tree = ET.parse(filename)
    tree_root = tree.getroot()
    plate_root = tree_root.find("plate")
    return float(
        next(
            (c.get("value") for c in plate_root.findall(
                "metadata") if c.get("key") == "weight"),
            0.0)
    )


def generate_foldername(filename: str, url: str, shortcode: str) -> str:
    """
    Generates the folder name for storing temporary files,
    gcode outputs and 3mfs

    Args:
        filename (str): filename of the current file
        url (str): url/discord endpoint to download the file from
        shortcode (str): shortcode of the user

    Returns:
        str: shortcode + url_params + filename
    """
    return "_".join([shortcode, url.split("?")[-1], filename])


def slice_file_bin(
    url: str,
    filename: str,
    shortcode: str,
    infill: int = 15,
    filament_path: str = "assets/filament/Generic PLA.json",
    machine_path: str = "assets/machine/Bambu Lab P1P 0.4 nozzle.json",
    process_path: str = "assets/process/0.28mm Extra Draft @BBL P1P.json",
    timeout: int = 60,
) -> subprocess.CompletedProcess[bytes]:
    """
    Slice the file using the bambu-studio binary

    Args:
        url (str): url of the file to download and print
        filename (str): filename of the file
        shortcode (str): shortcode of the user
        infill (int, optional): infill percentage. Defaults to 15.
        filament_path (str, optional): filament settings path.
            Defaults to "assets/filament/Generic PLA.json".
        machine_path (str, optional): machine settings path.
            Defaults to "assets/machine/Bambu Lab P1P 0.4 nozzle.json".
        process_path (str, optional): process settings path.
            Defaults to "assets/process/0.28mm Extra Draft @BBL P1P.json".
        timeout (int, optional): timeout of the process -
            after timeout delete produced files. Defaults to 60.

    Returns:
        subprocess.CompletedProcess[bytes]: details of the completed
            job/process
    """

    folder_name = "tmp/" + generate_foldername(
        filename=filename,
        url=url,
        shortcode=shortcode)

    os.makedirs(folder_name, exist_ok=True)
    temporary_file_path = f"{folder_name}/{filename}"
    with requests.get(url) as f:
        with open(temporary_file_path, "wb") as file:
            file.write(f.content)

    command = ["./bambu-studio",
               '--curr-bed-type', 'Textured PEI Plate',
               "--sparse-infill-density", f"{infill}",
               "--avoid-extrusion-cali-region",
               "--allow-rotations",
               "--avoid-extrusion-cali-region",
               "--orient", "1",
               "--arrange", "1",
               "--load-settings",
               f"{machine_path};{process_path}",
               "--load-filaments", f"\"{filament_path}\"",
               "--ensure-on-bed",
               "--slice", "1",
               "--outputdir", folder_name,
               "--export-3mf", "output.3mf",
               temporary_file_path]

    logging.info(command)
    result = subprocess.run(command)

    os.remove(temporary_file_path)

    threading.Timer(
        timeout, lambda:
            shutil.rmtree(folder_name, ignore_errors=True)
    ).start()

    return result


@router.post("/slice/file")
async def slice_file(
    shortcode: str,
    filename: str,
    url: str,
    layer_height: float = AVAILABLE_LAYER_HEIGHT,
    infill: int = Query(default=15, ge=5, le=30),
    printer_type: str = AVAILABLE_PRINTERS,
) -> dict:
    # logging.info(slice_request)
    try:
        filament_file_name = printer_pla(printer_type)
        process_file_name = process_from_machine_layer(
            machine=printer_type,
            layer_height=layer_height)
        machine_file_name = get_machine(printer_type)

        if url:
            logging.info(f"{filament_file_name}")
            logging.info(f"{process_file_name}")
            logging.info(f"{machine_file_name}")
            result = slice_file_bin(
                shortcode=shortcode,
                url=url,
                infill=infill,
                filename=filename,
                filament_path="assets/filament/"+filament_file_name,
                process_path="assets/process/"+process_file_name,
                machine_path="assets/machine/"+machine_file_name)
            logging.debug(f"Slicing Result: {result}")

            folder_name = "tmp/" + generate_foldername(
                filename=filename,
                url=url,
                shortcode=shortcode)

            model_time, estimated_time = gcode_time(
                f"{folder_name}/plate_1.gcode")

            try:
                img = render_gcode(f"{folder_name}/plate_1.gcode")
                # convert np.array to image in base64
                render_response = None

                if img:
                    img = Image.fromarray(img)

                    with BytesIO() as output:
                        img.save(output, format="JPEG")
                        contents = output.getvalue()
                        render_b64 = base64.b64encode(contents)

                    render_response = Response(render_b64,
                                               media_type="image/jpeg")
            except Exception as e:
                logging.exception(f"Render image failed: {e}")
                render_response = None

            return_object = {
                # "slice_result": dict(result),
                "filename": str(filename),
                "url": str(url),
                "shortcode": str(shortcode),
                "printer_type": str(printer_type),
                "layer_height": float(layer_height),
                "infill": int(infill),
                "plates": 1,
                "model_time": str(model_time),
                "estimated_time": str(estimated_time),
                "thumbnail": render_response,
            }

            # requests.post(BOT_ENDPOINT+"/confirm", json=return_object)

            return return_object

    except Exception as e:
        logging.exception(f"Slice file failed: {e}")
        pass


@router.post("/slice/release")
async def release_file(
    shortcode: str,
    filename: str,
    url: str,
    release: bool = False
) -> dict:
    """
    Release the file to the printer queue

    Args:
        shortcode (str): shortcode of the user
        filename (str): filename of the file
        url (str): url of the stl file to be printed
        release (bool, optional): whether to print release the file to the
            queue. Defaults to False.

    Returns:
        dict: whether or not the file was released
    """
    try:
        if release:
            folder_name = "tmp/" + \
                generate_foldername(filename=filename,
                                    url=url, shortcode=shortcode)
            # =================================================================
            data = {
                "filename": filename,
                "printer_type": "",  # noqa: printer_type should be the printer type ("p1p" or "p1s" atm)
                "shortcode": shortcode,
                "gcode": "",        # noqa: gcode should be str or bytes
                "print_time": 0,
                "print_weight": 0,
            }
            data["printer_type"] = "p1p"        # TODO: Confirm printer type
            with open(f"{folder_name}/plate_1.gcode", "r") as f:
                gcode = f.read()
                data["gcode"] = str(gcode)

            data["print_weight"] = int(
                extract_weight(
                    f"{folder_name}/slice_info.config")
            )
            data["print_time"] = bambu_time_conversion(
                extract_print_time(data["gcode"].split("\n")[:4])[1])

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=str(RABBITMQ_HOST),
                    port=int(RABBITMQ_PORT),
                    credentials=credentials
                )
            )

            channel = connection.channel()
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

            channel.basic_publish(
                exchange='',
                routing_key=RABBITMQ_QUEUE,
                body=json.dumps(data),
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent
                )
            )

            connection.close()
            # =================================================================================
            logging.info(
                f" [x] Sent Data({data['filename']}) to RabbitMQ({RABBITMQ_QUEUE})"  # noqa
            )

        return {"status": "success"}
    except Exception as e:
        logging.exception(f"Release file failed: {e}")
        return {"status": "failed"}
