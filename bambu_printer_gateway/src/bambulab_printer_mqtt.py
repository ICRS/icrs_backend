import json
import ssl
from typing import Any

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

class PrinterMQTTClient:
    """
    Printer class for handling MQTT communication with the printer

    Example::

        hostname = IP_ADDRESS
        access = BAMBULABS_ACCESS_TOKEN
        username = "bblp"
        printer_serial = PRINTER_SERIAL_NUMBER


        printerMQTTClient = PrinterMQTTClient(hostname, access, username, printer_serial)
        printerMQTTClient.connect()
        printerMQTTClient.start()
    """

    def __init__(self, hostname: str, access: str, printer_serial: str,
                 username: str = "bblp", port: int = 8883, timeout: int = 60):
        self._hostname = hostname
        self._access = access
        self._username = username
        self._printer_serial = printer_serial

        self._port = port
        self._timeout = timeout

        self._client = mqtt.Client(CallbackAPIVersion.VERSION2)
        self._client.username_pw_set(username, access)
        self._client.tls_set(tls_version=ssl.PROTOCOL_TLS,
                             cert_reqs=ssl.CERT_NONE)
        self._client.tls_insecure_set(True)

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        self.command_topic = f"device/{printer_serial}/command"

        self._data = {}

    def _on_message(self, client, userdata, msg) -> None:  # pylint: disable=unused-argument  # noqa
        # Current date and time
        doc = json.loads(msg.payload)

        # print(doc)

        if "print" in doc:
            self._data |= doc["print"]
            print(self._data)

    def _on_connect(self, client, serial, userdata, flags, rc) -> None:  # pylint: disable=unused-argument  # noqa
        """
        _on_connect Callback function for when the client
        receives a CONNACK response from the server.

        Parameters
        ----------
        client : mqtt.Client
            The client instance for this callback
        userdata : String
            User data
        flags : Arraylike
            Response flags sent by the broker
        rc : int
            The connection result
        """
        # print("Connected with result code " + str(rc))
        client.subscribe(f"device/{self._printer_serial}/report")
        # return None

    def connect(self) -> None:
        """
        Connects to the MQTT server asynchronously
        """
        self._client.connect_async(self._hostname, self._port, self._timeout)

    def start(self):
        """
        Starts the MQTT client
        """
        self._client.loop_start()

    def loop_forever(self):
        """
        Loop client forever (synchonous, blocking call)
        """
        self._client.loop_forever()

    def stop(self):
        """
        Stops the MQTT client
        """
        self._client.loop_stop()

    def get_last_print_percentage(self) -> int | str | None:
        """
        Get the last print percentage

        Returns:
            int | str | None: The last print percentage
        """
        return self._data.get("mc_percent", None)

    def get_remaining_time(self) -> int | str | None:
        """
        Get the remaining time for the print

        Returns:
            int | str | None: The remaining time for the print
        """
        return self._data.get("mc_remaining_time", None)

    def get_printer_state(self) -> str:
        """
        Get the printer state

        Returns:
            str: gcode_state
        """
        return self._data.get("gcode_state", "IDLE")

    def get_file_name(self) -> str:
        """
        Get the file name of the current/last print

        Returns:
            str: file name
        """
        return self._data.get("gcode_file", "")

    def get_print_speed(self) -> int:
        """
        Get the print speed

        Returns:
            int: print speed
        """
        return int(self._data.get("spd_mag", 100))

    def __publish_command(self, payload: dict[Any, Any]) -> None:
        """
        Generate a command payload and publish it to the MQTT server

        Args:
            payload (dict[Any, Any]): command to send to the printer
        """
        self._client.publish(self.command_topic, json.dumps(payload))

    def turn_light_off(self) -> None:
        """
        Turn off the printer light
        """
        self.__publish_command({"system": {"led_mode": "off"}})

    def turn_light_on(self) -> None:
        """
        Turn on the printer light
        """
        self.__publish_command({"system": {"led_mode": "on"}})

    def get_light_state(self) -> str:
        """
        Get the printer light state

        Returns:
            str: led_mode
        """
        light_report: list[dict[str, str]] = self._data.get(
            "lights_report", [])

        if not light_report:
            return "unknown"

        return light_report[0].get("mode", "unknown")

    def start_print(self) -> None:
        """
        Start the print

        Returns:
            str: print_status
        """
        # TODO: Implement this
        return 
    
    def stop_print(self) -> None:
        """
        Stop the print

        Returns:
            str: print_status
        """
        # TODO: Implement this
        return
    
    def pause_print(self) -> None:
        """
        Pause the print

        Returns:
            str: print_status
        """
        # TODO: Implement this
        return
        