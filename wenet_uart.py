from pyftdi.usbtools import UsbTools
from pyftdi.ftdi import Ftdi
from pyftdi.serialext import serial_for_url
import socket
import time
import argparse
import logging
import json
from datetime import datetime, timezone
import sys

def build_json_payload(string_payload):
    assert(len(string_payload) <= 252)
    return json.dumps({'type': 'WENET_TX_TEXT', 'packet': string_payload})

parser = argparse.ArgumentParser(description="Wenet UART reader")
parser.add_argument('--baudrate', type=int, default=460800, help='Baudrate for UART communication')
parser.add_argument('--ip_address', type=str, default='127.0.0.1', help='IP address to bind the socket server')
parser.add_argument('--port', type=int, default=55674, help='Port to bind the socket server')
args = parser.parse_args()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
    handlers=[
        logging.FileHandler("my_service.log"),
        logging.StreamHandler()
    ])

url = None
while True:
    logger.info("Searching for device...")
    while url is None:
        UsbTools.flush_cache()
        avail_devices = UsbTools.list_devices('ftdi:///?', Ftdi.VENDOR_IDS, Ftdi.PRODUCT_IDS, Ftdi.DEFAULT_VENDOR)
        logger.debug(avail_devices)
        for device in avail_devices:
            if device[0].description == 'FT230X Basic UART':
                logger.info("Found FT230X Basic UART device")
                url = f"ftdi://ftdi:ft-x:{device[0].sn}/1"
                break
        if(url is None):
            # Devices was not found, wait and exit
            # This will allow docker to restart the container with delay to avoid spamming
            logger.error("Device not found, waiting to exit...")
            time.sleep(15)
            sys.exit(1)

    logger.info("Connecting")
    with serial_for_url(url, baudrate=args.baudrate) as serial_port:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            try:
                line = serial_port.readline().decode('utf-8').strip()
            except Exception as e:
                logger.error(f"Error reading from serial port: {e}")
                break
            if "BLE Data: " in line:
                line = line.split("BLE Data: ")[1]
                # Insert timestamp
                line = f"{datetime.now(timezone.utc).isoformat()},{line}"
                logger.info(f"Data Recieved: {line}")
                sock.sendto(build_json_payload(line).encode('utf-8'), (args.ip_address, args.port))
            else:
                logger.info(line)
    
    # Connection closed, try to reconnect
    logger.info("Connection closed, rescanning...")
    time.sleep(1)
    url = None