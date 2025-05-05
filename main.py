#!/usr/bin/env python3
from serial import Serial
from time import sleep
from sys import stdout
import subprocess

def serial_recv(port):
    if port.in_waiting:
        # Format response(s)
        recv = port.read_all().decode('ascii').split('\n')
        recv = [s.strip() for s in recv if s.strip() != '']
        return recv
    else:
        return []

def serial_send(port, command, timeout=5):
    # Send command
    port.flush()
    print('-->', command)
    port.write(f"{command}\r\n".encode('ascii'))

    # Wait for response
    for i in range(timeout*10):
        recv = serial_recv(port)
        if len(recv) > 0:
            break
        sleep(0.1)
    else:
        recv = [] 

    # Print response(s)
    for message in recv:
        print('<--', message)
    
    return recv

radio_error_codes = {'+ERR='+str(k):v for k,v in {
    # Taken from the documentation
    1: "There is not \"enter\" or 0x0D 0x0A in the end of the AT Command.",
    2: "The head of AT command is not \"AT\" string.",
    3: "There is not \"=\" symbol in the AT command.",
    4: "Unknown command.",
    10: "TX is over times.",
    11: "RX is over times.",
    12: "CRC error.",
    13: "TX data more than 240 bytes.",
    15: "Unknown error."
}.items()}

def config_lora(port, command):
    # Clear input buffer
    #port.read_all()
    # Send command and wait for response
    recv = serial_send(port, command)
    # Check if there was an error
    for line in recv:
        if "ERR" in line:
            # If there was, kill the program and display the error meaning
            raise Exception("Radio module error: "+radio_error_codes[line])
    # Otherwise return the received data
    return recv

def lora_send(port, address, text):
    # Filter CLRF because it would signal end of serial data
    text = text.replace('\r\n', '\n')
    assert len(text) <= 240, "Text too long, max 240 bytes"
    serial_send(port, f"AT+SEND={address},{len(text)},{text}", timeout=20)

with Serial("/dev/ttyACM0", 9600) as port:
    # Setup LoRa radio module
    # https://reyax.com//upload/products_download/download_file/LoRa%20AT%20Command%20RYLR40x_RYLR89x_EN.pdf
    commands = [
        "AT", # Check if the module is connected & ready
        "AT+PARAMETER=10,7,1,7", # Set LoRa parameters
        "AT+BAND=868500000", # 868.5 MHz (Europe license-free band)
        "AT+MODE=0", # Disable sleep mode
        "AT+NETWORKID=3",
        "AT+ADDRESS=86",
        "AT+CRFOP=00" # Output power in dBm (00-15)
    ]

    for command in commands:
        response = config_lora(port, command)
        if len(response) == 0:
            raise Exception("No reply from radio module")
        elif len(response) > 1:
            print("More than one response... weird")

        for line in response:
            if line != "+OK":
                raise Exception("AA something broke")

    print("Setup complete")

    spinner = 0
    while True:
        recv = serial_recv(port)
        if recv:
            # Overtype spinner
            print('\r', end='')
        for message in recv:
            print("<--", message)
            if message.startswith("+RCV"):
                print("wowie a message for us!")
                # Remove '+RCV='
                message = message.removeprefix("+RCV=")
                # Extract first two fields and simultaneously remove them
                sender, _, message = message.partition(',')
                data_len, _, message = message.partition(',')
                data_len = int(data_len)
                # Read the message field
                data = message[:data_len]
                # Remove the message field
                message = message[data_len+1:]
                # Extract the remaining two fields
                rssi, snr = message.split(',')
                # Tidy up
                del _, message

                match data:
                    case "":
                        lora_send(port, sender, "")
                    case "ping":
                        lora_send(port, sender, "pong!")
                    case _:
                        result = subprocess.run(data.split(' '), capture_output=True)
                        output = (result.stdout+result.stderr).decode('ascii')
                        lora_send(port, sender, output[:240]) 


        animation = "|/─\\"
        spinner += 1
        if spinner >= len(animation):
            spinner = 0
        print('\r '+animation[spinner], end=' ')
        stdout.flush()
        sleep(1)
