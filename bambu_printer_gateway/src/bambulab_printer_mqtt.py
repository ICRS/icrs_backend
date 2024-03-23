import json
import ssl

import paho.mqtt.client as mqtt

class PrinterMQTTClient:
    def __init__(self, hostname, access, printer_serial, username="bblp", port=8883, timeout=60):
        self._hostname = hostname
        self._access = access
        self._username = username
        self._printer_serial = printer_serial
        
        self._port = port
        self._timeout = 60
        
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.username_pw_set(username, access)
        self._client.tls_set(tls_version=ssl.PROTOCOL_TLS, cert_reqs=ssl.CERT_NONE)
        self._client.tls_insecure_set(True)


        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        
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
        print("Connected with result code " + str(rc))
        client.subscribe(f"device/{self._printer_serial}/report")
        # return None

    def connect(self):
        self._client.connect_async(self._hostname, self._port, self._timeout)
    
    def start(self):
        self._client.loop_start()
        
    def loop_forever(self):
        self._client.loop_forever()

    def stop(self):
        self._client.loop_stop()
                
    def get_last_print_percentage(self):
        return self._data["mc_percent"] if "mc_percent" in self._data else None
    
    def get_remaining_time(self):
        return self._data["mc_remaining_time"] if "mc_remaining_time" in self._data else None


"""
Example Use case

hostname = IP_ADDRESS
access = BAMBULABS_ACCESS_TOKEN
username = "bblp"
printer_serial = PRINTER_SERIAL_NUMBER


printerMQTTClient = PrinterMQTTClient(hostname, access, username, printer_serial)
printerMQTTClient.connect()
printerMQTTClient.start()

"""
