from network import LoRa
import socket
import ubinascii
import binascii
import struct
import time
from machine import I2C, Pin
from pycom import pulses_get
from AXP2101 import AXP2101
from micropyGPS import MicropyGPS


# Initialize AXP2101 power management
try:
    I2CBUS = I2C(0, pins=('G21', 'G22'))
    axp = AXP2101(I2CBUS)
    axp.setALDO2Voltage(2800)   # T-Beam LORA VCC 3v3
    axp.setALDO3Voltage(3300)   # T-Beam GPS VDD 3v3
    axp.enableALDO2()           # Turn on LORA VCC
    axp.enableALDO3()           # Turn on GPS VDD
    axp.enableTemperatureMeasure()
    axp.enableBattDetection()
    axp.enableVbusVoltageMeasure()
    axp.enableBattVoltageMeasure()
    axp.enableSystemVoltageMeasure()
    axp.setChargingLedMode(AXP2101.XPOWERS_CHG_LED_CTRL_CHG)
except Exception as err:
    print("AXP Not Available, probably a TTGO < 1: ", err)

# Initialize LoRa in LORAWAN mode
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)

# DevAddr, NwkSKey, and AppSKey provided by TTN
dev_addr = struct.unpack(">l", ubinascii.unhexlify('260B0812'))[0]
nwk_swkey = ubinascii.unhexlify('853278249074BA65C49E9E9E557E4E20')
app_swkey = ubinascii.unhexlify('D340B519AD49E290BCF1D20FDEEF6223')

# Join the network using ABP (Activation By Personalization)
lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))

# Wait until the module has joined the network
while not lora.has_joined():
    print('Ainda não conectado...')
    time.sleep(2)

print('Conectado')

# Create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# Set the LoRaWAN data rate
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 0)

# Make the socket blocking
s.setblocking(True)

# Function to convert a float to bytes
def float_to_bytes(float_value):
    return struct.pack('>f', float_value)

# Function to create the payload
def create_payload(latitude, longitude, nivel_contentor, estado_contentor, estado_bateria, trafego_utilizacao):
    lat_bytes = float_to_bytes(latitude)
    lon_bytes = float_to_bytes(longitude)

    # Nível de contentor em 7 bits e estado de contentor em 1 bit
    nivel_estado_contentor = ((nivel_contentor & 0x7F) << 1) | (estado_contentor & 0x01)

    # Estado de bateria em 7 bits e tráfego de utilização em 7 bits
    estado_bateria_trafego1 = ((estado_bateria & 0x7F) << 1) | ((trafego_utilizacao >> 6) & 0x01)
    estado_bateria_trafego2 = trafego_utilizacao & 0x3F

    # Combine the bytes into a payload
    payload = lat_bytes + lon_bytes + bytes([nivel_estado_contentor, estado_bateria_trafego1, estado_bateria_trafego2])

    # Convert bytes to hexadecimal representation
    hex_payload = payload

    return binascii.hexlify(hex_payload).decode('ascii')

latitude = 38.76319885253906
longitude = -9.108799934387207
estado_bateria = 3
trafego_utilizacao = 65
switch_status = 1
distance_mm = 10

payload = create_payload(latitude, longitude, int(distance_mm), switch_status, estado_bateria, trafego_utilizacao)
s.send(payload)
time.sleep(1)
