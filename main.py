#!/usr/bin/env python3
from serial import Serial
from time import sleep

def config_lora(port, command):
    # Send command
    port.flush()
    print('-->', command)
    port.write(f"{command}\r\n".encode('ascii'))
    # Wait for response
    while not port.in_waiting:
        sleep(0.2)
    # Print response(s)
    recv = port.read_all().decode('ascii').split('\n')
    recv = [s.strip() for s in recv if s.strip() != '']
    for message in recv:
        print('<--', message)

with Serial("/dev/ttyACM0", 9600) as port:
    # Setup LoRa radio module
    # https://reyax.com//upload/products_download/download_file/LoRa%20AT%20Command%20RYLR40x_RYLR89x_EN.pdf
    port.read_all()
    config_lora(port, "AT")
    config_lora(port, "AT+PARAMETER=12,7,1,4") # Set LoRa parameters
    config_lora(port, "AT+BAND=868500000") # 868.5 MHz (Europe license-free band)
    config_lora(port, "AT+MODE=0") # Disable sleep mode
    config_lora(port, "AT+ADDRESS=86")
    config_lora(port, "AT+NETWORKID=3")
    config_lora(port, "AT+CRFOP=00")
    print("Setup complete")

    while True:
        if port.in_waiting:
            recv = port.read_all().decode('ascii').split('\n')
            recv = [s.strip() for s in recv if s.strip() != '']
            for message in recv:
                print("<--", message)
                if message.startswith("+RCV"):
                    print("wowie a message for us!")
        sleep(1)
