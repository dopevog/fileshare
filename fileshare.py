import http.server
import html
import socketserver
import random
import os
import socket
import sys
import shutil
from shutil import make_archive
import pathlib
import signal
import platform
import argparse
import urllib.request
import urllib.parse
import urllib.error
import re
from io import BytesIO
import qrcode
import base64


MacOS = "Darwin"
Linux = "Linux"
Windows = "Windows"
operating_system = platform.system()
message = """
This port is being used. Try another port.                      
"""


def cursor(status):
    if operating_system != Windows:
        print("\033[?25" + ("h" if status else "l"), end="")


def clean_exit():
    cursor(True)

    print("\r", end="")

    print("  ")

    sys.exit()


def FileTransferServerHandlerClass(file_name, auth, debug, no_force_download):
    class FileTransferServerHandler(http.server.SimpleHTTPRequestHandler):
        _file_name = file_name
        _auth = auth
        _debug = debug
        _no_force_download = no_force_download

        def do_AUTHHEAD(self):
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="fileshare"')
            self.send_header("Content-type", "text/html")
            self.end_headers()

        def do_GET(self):
            if self._auth is not None:
                if self.headers.get("Authorization") != "Basic " + (
                    self._auth.decode()
                ):
                    self.do_AUTHHEAD()
                    return

            request_path = self.path[1:]
            if request_path != self._file_name:
                self.send_response(403)
                self.send_header("Content-type", "text/html")
                self.end_headers()
            else:
                super().do_GET()

        def guess_type(self, path):
            if not self._no_force_download:
                return "application/octet-stream"

            super().guess_type(path)

        def log_message(self, format, *args):
            if self._debug:
                super().log_message(format, *args)

    return FileTransferServerHandler


def FileUploadServerHandlerClass(output_dir, auth, debug):
    class FileUploadServerHandler(http.server.BaseHTTPRequestHandler):
        absolute_path = os.path.abspath(output_dir)
        home = os.path.expanduser("~")
        nice_path = absolute_path.replace(home, "~")
        _output_dir = output_dir
        _auth = auth
        _debug = debug

        def do_AUTHHEAD(self):
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="fileshare"')
            self.send_header("Content-type", "text/html")
            self.end_headers()

        def do_GET(self):
            if self._auth is not None:
                if self.headers.get("Authorization") != "Basic " + (
                    self._auth.decode()
                ):
                    self.do_AUTHHEAD()
                    return

            f = self.send_head()
            if f:
                self.copyfile(f, self.wfile)
                f.close()

        def do_HEAD(self):
            f = self.send_head()
            if f:
                f.close()

        def do_POST(self):
            """Serve a POST request."""
            r, info = self.deal_post_data()
            print((r, info, "by: ", self.client_address))

            f = BytesIO()
            f.write(b'<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN"><html>')
            f.write(b"<title>fileshare</title>")
            f.write(
                b'<meta name="viewport" content="width=device-width, initial-scale=1">'
            )
            f.write(
                b'<link href="https://fonts.googleapis.com/css?family=Comfortaa" rel="stylesheet">'
            )
            f.write(b'<link rel="icon" href="logo.png" type="image/png">')
            f.write(b"<center>")
            f.write(b"<body>")
            f.write(
                b"<h2 style=\"font-family: 'Comfortaa', cursive;color:'#263238';\">Upload Result Page</h2>"
            )
            f.write(b"<hr>")

            if r:
                f.write(
                    b"<strong style=\"font-family: 'Comfortaa', cursive;color:'#263238';\">Success: </strong>"
                )
            else:
                f.write(
                    b"<strong style=\"font-family: 'Comfortaa', cursive;color:'#263238';\">Failed: </strong>"
                )

            f.write(
                (
                    "<span style=\"font-family: 'Comfortaa', cursive;color:'#263238';\">%s</span><br>"
                    % info
                ).encode()
            )
            f.write(
                (
                    "<br><a href=\"%s\" style=\"font-family: 'Comfortaa', cursive;color:'#263238';\">back</a>"
                    % self.headers["referer"]
                ).encode()
            )
            f.write(
                b"<hr><small style=\"font-family: 'Comfortaa', cursive;color:'#263238';\">Made By: "
            )
            f.write(b'<a href="https://github.com/dopevog/">')
            f.write(b"Dopevog</a>\n")
            length = f.tell()
            f.seek(0)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(length))
            self.end_headers()
            if f:
                self.copyfile(f, self.wfile)
                f.close()

        def log_message(self, format, *args):
            if self._debug:
                super().log_message(format, *args)

        def deal_post_data(self):
            uploaded_files = []
            content_type = self.headers["content-type"]
            if not content_type:
                return (False, "Content-Type header doesn't contain boundary")
            boundary = content_type.split("=")[1].encode()
            remainbytes = int(self.headers["content-length"])
            line = self.rfile.readline()
            remainbytes -= len(line)

            if boundary not in line:
                return (False, "Content NOT begin with boundary")
            while remainbytes > 0:
                line = self.rfile.readline()
                remainbytes -= len(line)
                fn = re.findall(
                    r'Content-Disposition.*name="file"; filename="(.*)"',
                    line.decode("utf-8", "backslashreplace"),
                )
                if not fn:
                    return (False, "Can't find out file name...")
                file_name = fn[0]
                fn = os.path.join(self._output_dir, file_name)
                line = self.rfile.readline()
                remainbytes -= len(line)
                line = self.rfile.readline()
                remainbytes -= len(line)
                try:
                    out = open(fn, "wb")
                except IOError:
                    return (
                        False,
                        "Can't create file to write, do you have permission to write?",
                    )
                else:
                    with out:
                        preline = self.rfile.readline()
                        remainbytes -= len(preline)
                        while remainbytes > 0:
                            line = self.rfile.readline()
                            remainbytes -= len(line)
                            if boundary in line:
                                preline = preline[0:-1]
                                if preline.endswith(b"\r"):
                                    preline = preline[0:-1]
                                out.write(preline)
                                uploaded_files.append(
                                    os.path.join(self.nice_path, file_name)
                                )
                                break
                            else:
                                out.write(preline)
                                preline = line
            return (True, "File '%s' upload success!" % ",".join(uploaded_files))

        def send_head(self):
            f = BytesIO()
            displaypath = html.escape(urllib.parse.unquote(self.nice_path))

            f.write(b"<title>fileshare</title>")
            f.write(
                b'<meta name="viewport" content="width=device-width, initial-scale=1">'
            )
            f.write(
                b'<link href="https://fonts.googleapis.com/css?family=Comfortaa" rel="stylesheet">'
            )
            f.write(b'<link rel="icon" href="logo.png" type="image/png">')
            f.write(b"<body>")
            f.write(b"<center>")
            f.write(b'<img src="logo.png">')
            f.write(
                (
                    "<body>\n<h2 style=\"font-family: 'Comfortaa', cursive;color:'#263238';\">Please choose file to upload to %s</h2>\n"
                    % displaypath
                ).encode()
            )
            f.write(b"<hr>")
            f.write(
                b'<form ENCTYPE="multipart/form-data" method="post"><input style="font-family:\'Comfortaa\', cursive;color:\'#263238\';" name="file" type="file" multiple/><input type="submit" value="upload"/></form>'
            )
            f.write(b"</center>")
            f.write(b"</body>")
            f.write(b"</html>")

            length = f.tell()
            f.seek(0)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(length))
            self.end_headers()
            return f

        def copyfile(self, source, outputfile):
            shutil.copyfileobj(source, outputfile)

    return FileUploadServerHandler


def get_ssid():

    if operating_system == MacOS:
        ssid = (
            os.popen(
                "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I | awk '/ SSID/ {print substr($0, index($0, $2))}'"
            )
            .read()
            .strip()
        )
        return ssid

    elif operating_system == "Linux":
        ssid = os.popen("iwgetid -r 2>/dev/null",).read().strip()
        if not ssid:
            ssid = (
                os.popen(
                    "nmcli -t -f active,ssid dev wifi | egrep '^yes' | cut -d\\' -f2 | sed 's/yes://g' 2>/dev/null"
                )
                .read()
                .strip()
            )
        return ssid

    else:
        interface_info = os.popen("netsh.exe wlan show interfaces").read()
        for line in interface_info.splitlines():
            if line.strip().startswith("Profile"):
                ssid = line.split(":")[1].strip()
                return ssid


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        print("Network is unreachable")
        clean_exit()


def get_local_ips_available():
    """Get a list of all local IPv4 addresses except localhost"""
    try:
        import netifaces

        ips = []
        for iface in netifaces.interfaces():
            ips.extend(
                [
                    x["addr"]
                    for x in netifaces.ifaddresses(iface).get(netifaces.AF_INET, [])
                    if x and "addr" in x
                ]
            )

        localhost_ip = re.compile("^127.+$")
        return [x for x in sorted(ips) if not localhost_ip.match(x)]

    except ModuleNotFoundError:
        pass


def random_port():
    return random.randint(1024, 65535)


def print_qr_code(address):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(address)
    qr.make()

    qr.print_tty()


def start_download_server(file_path, **kwargs):
    PORT = int(kwargs["custom_port"]) if kwargs.get(
        "custom_port") else random_port()
    LOCAL_IP = kwargs["ip_addr"] if kwargs["ip_addr"] else get_local_ip()
    SSID = get_ssid()
    auth = kwargs.get("auth")
    debug = kwargs.get("debug", False)

    if not os.path.exists(file_path):
        print("No such file or directory")
        clean_exit()

    delete_zip = 0
    abs_path = os.path.normpath(os.path.abspath(file_path))
    file_dir = os.path.dirname(abs_path)
    file_path = os.path.basename(abs_path)

    os.chdir(file_dir)

    if os.path.isdir(file_path):
        zip_name = pathlib.PurePosixPath(file_path).name

        try:
            path_to_zip = make_archive(zip_name, "zip", file_path)
            file_path = os.path.basename(path_to_zip)
            delete_zip = file_path
        except PermissionError:
            print("Permission denied")
            clean_exit()

    file_path = file_path.replace(" ", "%20")

    handler = FileTransferServerHandlerClass(
        file_path, auth, debug, kwargs.get("no_force_download", False)
    )
    httpd = socketserver.TCPServer(("", PORT), handler)

    address = "http://" + str(LOCAL_IP) + ":" + str(PORT) + "/" + file_path

    print("Scan the following QR code to start downloading.")
    if SSID:
        print(
            "Make sure that your smartphone is connected to \033[1;94m{}\033[0m".format(
                SSID
            )
        )

    if debug:
        print(address)

    print_qr_code(address)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    if delete_zip != 0:
        os.remove(delete_zip)

    clean_exit()


def start_upload_server(file_path, debug, custom_port, ip_addr, auth):

    if custom_port:
        PORT = int(custom_port)
    else:
        PORT = random_port()

    if ip_addr:
        LOCAL_IP = ip_addr
    else:
        LOCAL_IP = get_local_ip()

    SSID = get_ssid()

    if not os.path.exists(file_path):
        print("No such file or directory")
        clean_exit()

    if not os.path.isdir(file_path):
        print("%s is not a folder." % file_path)
        clean_exit()

    handler = FileUploadServerHandlerClass(file_path, auth, debug)

    try:
        httpd = socketserver.TCPServer(("", PORT), handler)
    except OSError:
        print(message)
        clean_exit()

    address = "http://" + str(LOCAL_IP) + ":" + str(PORT) + "/"

    print("Scan the following QR code to start uploading.")
    if SSID:
        print(
            "Make sure that your smartphone is connected to \033[1;94m{}\033[0m".format(
                SSID
            )
        )

    if debug:
        print(address)

    print_qr_code(address)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    clean_exit()


def b64_auth(a):
    splited = a.split(":")
    if len(splited) != 2:
        msg = "The format of auth should be [username:password]"
        raise argparse.ArgumentTypeError(msg)
    return base64.b64encode(a.encode())


def main():
    if operating_system != Windows:
        signal.signal(signal.SIGTSTP, signal.SIG_IGN)

    parser = argparse.ArgumentParser(
        description="Transfer files over WiFi between your computer and your smartphone from the terminal"
    )

    parser.add_argument(
        "file_path",
        action="store",
        help="path that you want to transfer or store the received file.",
    )
    parser.add_argument(
        "--debug", "-d", action="store_true", help="show the encoded url."
    )
    parser.add_argument(
        "--receive",
        "-r",
        action="store_true",
        help="enable upload mode, received file will be stored at given path.",
    )
    parser.add_argument("--port", "-p", dest="port", help="use a custom port")
    parser.add_argument(
        "--ip_addr",
        dest="ip_addr",
        choices=get_local_ips_available(),
        help="specify IP address",
    )
    parser.add_argument(
        "--auth",
        action="store",
        help="add authentication, format: username:password",
        type=b64_auth,
    )
    parser.add_argument(
        "--no-force-download",
        action="store_true",
        help="Allow browser to handle the file processing instead of forcing it to download.",
    )

    args = parser.parse_args()

    if operating_system == Windows:
        import colorama

        colorama.init()
        print("\033[2J", end="")

    cursor(False)

    if args.receive:
        start_upload_server(
            file_path=args.file_path,
            debug=args.debug,
            custom_port=args.port,
            ip_addr=args.ip_addr,
            auth=args.auth,
        )
    else:
        start_download_server(
            args.file_path,
            debug=args.debug,
            custom_port=args.port,
            ip_addr=args.ip_addr,
            auth=args.auth,
            no_force_download=args.no_force_download,
        )


if __name__ == "__main__":
    main()
