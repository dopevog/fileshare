<p align="center"><img src="logo.png"><br></p>
<p align="center">
<a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
<a href="https://img.shields.io/badge/support-Linux%20|%20MacOS%20|%20Windows%20-blue.svg"><img src="https://img.shields.io/badge/support-Linux%20|%20MacOS%20|%20Windows%20-blue.svg"></a>
</p>
<p align="center">📨Share files easily over your local network from the terminal!📨</p>


## Installation

```bash
# clone the repo
$ git clone https://github.com/dopevog/fileshare.git

# change the working directory to fileshare
$ cd fileshare

# install the requirements
$ pip3 install -r requirements.txt
```


## Usage
```
usage: qr-filetransfer [-h] [--debug] [--receive] [--port PORT]
                       [--ip_addr {192.168.0.105}] [--auth AUTH]
                       file_path

Transfer files over WiFi between your computer and your smartphone from the
terminal

positional arguments:
  file_path             path that you want to transfer or store the received
                        file.

optional arguments:
  -h, --help            show this help message and exit
  --debug, -d           show the encoded url.
  --receive, -r         enable upload mode, received file will be stored at
                        given path.
  --port PORT, -p PORT  use a custom port
  --ip_addr {192.168.0.105}
                        specify IP address
  --auth AUTH           add authentication, format: username:password
  --no-force-download   Allow browser to handle the file processing instead of
                        forcing it to download.
```

**Note:** Both devices needs to be connected to the same network

**Exiting:** To exit the program, just press ```CTRL+C```.

---

Transfer a single file
```bash
$ python fileshare.py /path/to/file.png
```


Transfer a full directory. **Note:** the directory gets zipped before being transferred
```bash
$ python fileshare.py /path/to/directory/
```

Receive/upload a file from your phone to your computer
```bash
$ python fileshare.py -r /path/to/receive/file/to/
```

## License
This Project Has Been [MIT Licensed]()
