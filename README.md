# dx-lr22-lora

Python helper for the DX-SMART **DX-LR22** LoRa UART module (Semtech LLCC68, 868/915 MHz, 22 dBm), used through the kit's CH340 USB-serial adapter.

## Serial settings (found by probing the module)

| Setting | Value |
| --- | --- |
| Baud | 9600, 8N1, no flow control |
| Line ending | CRLF (`\r\n`) on every command, otherwise `ERROR=104` |
| AT mode | send `+++\r\n` to toggle: `Entry AT` / `Exit AT` |
| Default mode | transparent: serial bytes in go out over the air, received packets come out of the serial port |

Factory parameters reported by `AT+HELP` (firmware V1.2.4):

```
MODE:0
LEVEL:2 >> 2149bps
SLEEP:2
Frequency:915150000hz >> 41
MAC:ff,ff
CRC:1(true)
IQ:1(true)
Power:22dBm
```

## Usage

```bash
pip install pyserial
python lr22.py info                 # print AT+HELP parameters
python lr22.py at AT+HELP           # send raw AT commands
python lr22.py send "hello"         # transmit a message
python lr22.py listen               # print anything received
python lr22.py chat                 # interactive send/receive
python lr22.py --port COM5 listen   # different port (default COM12)
```

Two modules must share the same channel, air rate (LEVEL) and address to talk to each other.
