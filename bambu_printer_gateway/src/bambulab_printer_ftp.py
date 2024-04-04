import ftplib
import ssl

import logging
from typing import BinaryIO


class ImplicitFTP_TLS(ftplib.FTP_TLS):
    """FTP_TLS subclass that automatically wraps sockets in SSL to support implicit FTPS."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sock = None

    @property
    def sock(self):
        """Return the socket."""
        return self._sock

    @sock.setter
    def sock(self, value):
        """When modifying the socket, ensure that it is ssl wrapped."""
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value)
        self._sock = value


class PrinterFTPClient:
    def __init__(self,
                 server_ip: str,
                 access_code: str,
                 user: str = 'bblp',
                 port: int = 990) -> None:
        self.ftps = ImplicitFTP_TLS()
        logging.info("Connecting to FTP server...", server_ip, port, user, access_code)
        # Connect to the FTP server
        self.ftps.connect(host=server_ip, port=port)
        self.ftps.login(user, access_code)
        logging.info("Connected to FTP server")
        logging.info(self.ftps.prot_p())

    def upload_file(self, file: BinaryIO, file_path: str) -> None:
        self.ftps.storbinary(f'STOR {file_path}', file) # TODO: Check folder path
    
    def delete_file(self, file_path: str) -> None:
        self.ftps.delete(file_path)
        
    def close(self) -> None:
        self.ftps.quit()
    
    