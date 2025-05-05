#!/usr/bin/env python3
from serial import Serial
from time import sleep
from sys import stdout
import subprocess

def serial_recv(port, timeout=0.1) -> list:
    output = []

    # Wait for response
    for i in range(int(timeout*10)):
        if port.in_waiting:
            # Format response(s)
            recv = port.read_all().decode('ascii').split('\n')
            recv = [s.strip() for s in recv if s.strip() != '']
            output += recv

        if len(output) > 0:
            break
        sleep(0.1)

    return output

def serial_send(port, command, timeout=5) -> list:
    # Send command
    port.flush()
    print('-->', command)
    port.write(f"{command}\r\n".encode('ascii'))

    # Print response(s)
    recv = serial_recv(port, timeout)
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

def config_lora(port, command) -> list:
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

def lora_send(port, address, text, timeout=20) -> list:
    """Send a text message to some LoRa address. Device should first be set up with config_lora().
    Inputs:
        port: Serial port of LoRa device
        address: Destination NETWORKID
        text: String message, up to 240 bytes. \\r and \\n are filtered.
        timeout: Maximum time to wait for transmit in seconds
    Returns:
        Reponses from LoRa device after transmitting. Typically ["+OK"].
        Reading incoming messages should be done with lora_recv().
    """
    # Filter newlines because it would signal end of serial data
    for remove in '\r\n':
        text = text.replace(remove, '')

    assert len(text) <= 240, "Text too long, max 240 bytes"
    return serial_send(port, f"AT+SEND={address},{len(text)},{text}", timeout=timeout)

def lora_recv(port, timeout=0.1) -> list:
    """Checks for any received messages from LoRa network. Device should first be set up with config_lora().
    Inputs:
        port: Serial port of LoRa device
        timeout: Maximum time to wait for a message
    Returns:
        List of messages, where each message is a list with the following values:
        [sender_address, message, rssi, snr]
        There may be more than one message, depending on how long it's been since lora_recv() was last called.
        This function should be called regularly to avoid unread messages potentially overflowing the Pico's UART buffer!
        If the timeout was exceeded, an empty list is returned.
    """
    output = []
    
    recv = serial_recv(port, timeout)
    """
    if recv:
        # Overtype spinner
        print('\r', end='')
    """
    for message in recv:
        #print("<--", message)
        if message.startswith("+RCV"):
            #print("wowie a message for us!")
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

            output.append([sender, data, rssi, snr])

    return output




receiver = True


with Serial("/dev/ttyACM0", 9600) as port:
    # Setup LoRa radio module
    # https://reyax.com//upload/products_download/download_file/LoRa%20AT%20Command%20RYLR40x_RYLR89x_EN.pdf
    commands = [
        "AT", # Check if the module is connected & ready
        "AT+PARAMETER=10,7,1,7", # Set LoRa parameters
        "AT+BAND=868500000", # 868.5 MHz (Europe license-free band)
        "AT+MODE=0", # Disable sleep mode
        "AT+NETWORKID=3",
        "AT+ADDRESS=" + "86" if receiver else "69",
        "AT+CRFOP=00" # Output power in dBm (00-15)
    ]

    for command in commands:
        responses = config_lora(port, command)
        if len(responses) == 0:
            raise Exception("No reply from radio module")
        elif len(responses) > 1:
            print("More than one response... weird")

        for line in responses:
            if line != "+OK":
                raise Exception("AA something broke")

    print("Setup complete")

    spinner = 0

    while True:
        if receiver:
            data = lora_recv(port)
            for mesg in data:
                sender, data, rssi, snr = mesg

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

        else:
            mesg = input("Message? ")
            lora_send(port, 86, mesg) # Send to my pc
            print(lora_recv(port, timeout=20)) # Await response
