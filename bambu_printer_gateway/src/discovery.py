"""
Find Bambu printers on the LAN by serial number.

Every Bambu printer serves MQTT over TLS on port 8883 with a certificate whose
subject CN is the printer's serial. Reading that certificate identifies the
printer at an IP without needing its access code, and unlike SSDP it works
across routed subnets (e.g. from the cluster to lobstar_lan).

Usage: python -m src.discovery 192.168.1.0/24,192.168.2.0/24
"""

__all__ = ["cert_serial", "find_printer", "scan", "port_open"]

import ipaddress
import logging
import socket
import ssl
import sys
from concurrent.futures import ThreadPoolExecutor

MQTT_PORT = 8883
_CN_OID = bytes([0x06, 0x03, 0x55, 0x04, 0x03])  # 2.5.4.3 commonName


def port_open(ip: str, port: int, timeout: float = 2) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False


def cert_serial(ip: str, timeout: float = 2) -> str | None:
    """Return the subject CN (the serial) of the printer cert at ip, if any."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # self-signed Bambu CA
    try:
        with socket.create_connection((ip, MQTT_PORT), timeout=timeout) as s, \
                ctx.wrap_socket(s) as t:
            der = t.getpeercert(binary_form=True)
    except (OSError, ssl.SSLError):
        return None
    if not der:
        return None
    # ssl can't decode an unverified cert, so pull the CN out of the DER.
    # The issuer's CN comes first and the subject's last.
    i = der.rfind(_CN_OID)
    if i == -1:
        return None
    n = der[i + 6]
    return der[i + 7:i + 7 + n].decode(errors="replace")


def _hosts(subnets: str) -> list[str]:
    return [str(h) for net in subnets.split(",") if net.strip()
            for h in ipaddress.ip_network(net.strip(), strict=False).hosts()]


def scan(subnets: str) -> dict[str, str]:
    """Map serial -> IP for every printer found in the given subnets."""
    with ThreadPoolExecutor(128) as ex:
        hosts = _hosts(subnets)
        return {serial: ip for ip, serial in zip(hosts, ex.map(cert_serial, hosts))
                if serial}


def find_printer(serial: str, hint: str | None, subnets: str) -> str | None:
    """
    Find the IP of the printer with this serial. The hint (last known IP) is
    checked first; the subnets are only scanned if it no longer matches.
    """
    if hint and cert_serial(hint) == serial:
        return hint
    if not subnets:
        return None
    logging.info(f"Printer {serial} not at {hint}, scanning {subnets}")
    return scan(subnets).get(serial)


if __name__ == "__main__":
    for found_serial, found_ip in sorted(scan(sys.argv[1]).items(), key=lambda x: x[1]):
        print(found_ip, found_serial)
