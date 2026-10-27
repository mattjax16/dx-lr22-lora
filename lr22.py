"""DX-LR22 (LLCC68 LoRa) helper over a USB-serial port.

Facts found by probing the module on COM12:
  - UART 9600 8N1, every command ends with CRLF
  - "+++\r\n" toggles AT mode  ("Entry AT" / "Exit AT")
  - outside AT mode the module is transparent: bytes in -> radio, radio -> bytes out

Usage:
  python lr22.py info              # print AT+HELP parameters
  python lr22.py at AT+HELP        # send one or more raw AT commands
  python lr22.py listen            # print anything received over the air
  python lr22.py send "hello"      # transmit a message
  python lr22.py chat              # type lines to send, received lines print as they arrive
Options: --port COM12 --baud 9600
"""
import argparse
import sys
import threading
import time

import serial


def open_port(port, baud):
    s = serial.Serial(port, baud, timeout=0.3)
    # CH340 boards can reset or change mode when DTR/RTS toggle; keep them low.
    s.dtr = False
    s.rts = False
    time.sleep(0.2)
    s.reset_input_buffer()
    return s


def read_for(s, seconds):
    end = time.time() + seconds
    buf = b""
    while time.time() < end:
        chunk = s.read(512)
        if chunk:
            buf += chunk
            end = max(end, time.time() + 0.3)
    return buf.decode(errors="replace")


def cmd(s, line, wait=1.0):
    s.write(line.encode() + b"\r\n")
    return read_for(s, wait)


def enter_at(s):
    """Toggle into AT mode, toggling back once if we were already in it."""
    reply = cmd(s, "+++")
    if "Exit AT" in reply:
        time.sleep(0.5)
        reply = cmd(s, "+++")
    if "Entry AT" not in reply:
        raise SystemExit(f"Could not enter AT mode, got: {reply!r}")


def exit_at(s):
    reply = cmd(s, "+++", wait=1.5)
    if "Exit AT" not in reply:
        print(f"warning: unexpected reply leaving AT mode: {reply!r}", file=sys.stderr)


def run_at(s, commands):
    enter_at(s)
    try:
        for c in commands:
            print(f"> {c}")
            print(cmd(s, c).rstrip())
    finally:
        exit_at(s)


def listen(s):
    print("Listening (Ctrl+C to stop)...")
    while True:
        data = s.read(512)
        if data:
            sys.stdout.write(data.decode(errors="replace"))
            sys.stdout.flush()


def chat(s):
    def rx():
        while True:
            data = s.read(512)
            if data:
                sys.stdout.write(f"\n<< {data.decode(errors='replace').rstrip()}\n")
                sys.stdout.flush()

    threading.Thread(target=rx, daemon=True).start()
    print("Type a line and press Enter to transmit (Ctrl+C to quit).")
    for line in sys.stdin:
        s.write(line.rstrip("\r\n").encode() + b"\r\n")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--port", default="COM12")
    p.add_argument("--baud", type=int, default=9600)
    p.add_argument("action", choices=["info", "at", "listen", "send", "chat"])
    p.add_argument("args", nargs="*")
    a = p.parse_args()

    with open_port(a.port, a.baud) as s:
        try:
            if a.action == "info":
                run_at(s, ["AT+HELP"])
            elif a.action == "at":
                run_at(s, a.args or ["AT"])
            elif a.action == "send":
                s.write(" ".join(a.args).encode() + b"\r\n")
                s.flush()
                print("sent")
            elif a.action == "listen":
                listen(s)
            elif a.action == "chat":
                chat(s)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
