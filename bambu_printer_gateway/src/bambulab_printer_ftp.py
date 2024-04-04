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
        
    def storbinary(self, cmd, fp, blocksize=8192, callback=None, rest=None):
        self.voidcmd('TYPE I')
        conn = self.transfercmd(cmd, rest)
        try:
            while 1:
                buf = fp.read(blocksize)
                if not buf:
                    break
                conn.sendall(buf)
                if callback:
                    callback(buf)
            # shutdown ssl layer
            if isinstance(conn, ssl.SSLSocket):
                # conn.unwrap()  # Fix for storbinary waiting indefinitely for response message from server
                pass
        finally:
            conn.close()  # This is the addition to the previous comment.
        return self.voidresp()


class PrinterFTPClient:
    def __init__(self,
                 server_ip: str,
                 access_code: str,
                 user: str = 'bblp',
                 port: int = 990) -> None:
        self.ftps = ImplicitFTP_TLS()
        
        self.server_ip = server_ip
        self.port = port
        self.user = user
        self.access_code = access_code
        

    def upload_file(self, file: BinaryIO, file_path: str) -> str:
        logging.info("Connecting to FTP server...")
        self.ftps.connect(host=self.server_ip, port=self.port)
        self.ftps.login(self.user, self.access_code)
        logging.info("Connected to FTP server")
        logging.info(self.ftps.prot_p())

        r = self.ftps.storbinary(f'STOR {file_path}', file, blocksize=32768, callback=lambda x: logging.info(f"Uploaded {x} bytes"))
        self.ftps.close()        
        logging.info(f"File uploaded: {r}")
        return r
    
    def delete_file(self, file_path: str) -> None:
        self.ftps.connect(host=self.server_ip, port=self.port)
        self.ftps.login(self.user, self.access_code)
        try:
            self.ftps.delete(file_path)
        except ftplib.error_perm as e:
            logging.error(f"Failed to delete file: {e}")
        finally:
            self.ftps.close()
            
    def close(self) -> None:
        self.ftps.quit()
    
    