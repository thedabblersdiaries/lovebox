#!/usr/bin/env python3

import time
import signal
import sys
import LCD1602
import RPi.GPIO as GPIO
import gspread
from google.oauth2.service_account import Credentials

# ================= GPIO =================
LED_PIN = 17
BUTTON_PIN = 18

LED_ON = GPIO.LOW
LED_OFF = GPIO.HIGH
BUTTON_PRESSED = GPIO.LOW
BUTTON_RELEASED = GPIO.HIGH

# ================= LCD =================
LCD_ADDR = 0x27
MAX_CHAR_PER_LINE = 16
PAGE_DISPLAY_TIME = 2.0
PAGE_GAP_TIME = 0.6

# ================= Google Sheets =================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
creds = Credentials.from_service_account_file(
    "credentials.json", scopes=SCOPES
)
gclient = gspread.authorize(creds)
msg_sheet = gclient.open("Lovebox").sheet1

# ================= State =================
messages = []
current_index = 0
page_index = 0

last_poll_time = 0
POLL_INTERVAL = 30

# ================= Setup =================
def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.output(LED_PIN, LED_OFF)

    LCD1602.init(LCD_ADDR, 1)
    LCD1602.clear()

# ================= Message Logic =================
def load_messages():
    global messages, current_index, page_index
    rows = msg_sheet.get_all_records()
    messages = [
        (i + 2, row["Content"])
        for i, row in enumerate(rows)
        if row.get("Seen") == 0
    ]

    if not messages:
        current_index = 0
        page_index = 0
    else:
        current_index = min(current_index, len(messages) - 1)
        page_index = 0

def break_message(msg):
    words = msg.split()
    lines = []
    current = ""

    for word in words:
        if len(current) + len(word) + (1 if current else 0) > MAX_CHAR_PER_LINE:
            lines.append(current)
            current = word
        else:
            current = word if not current else f"{current} {word}"

    if current:
        lines.append(current)

    return lines

# ================= LCD Helpers =================
def lcd_write_centered(row, text):
    LCD1602.write(0, row, text.center(16)[:16])

# ================= Display =================
def show_next_page():
    global page_index

    LCD1602.clear()

    if not messages:
        GPIO.output(LED_PIN, LED_OFF)
        lcd_write_centered(0, "No messages")
        lcd_write_centered(1, "right now!")
        return

    GPIO.output(LED_PIN, LED_ON)

    _, text = messages[current_index]
    lines = break_message(text)

    i = page_index * 2

    lcd_write_centered(0, lines[i])
    if i + 1 < len(lines):
        lcd_write_centered(1, lines[i + 1])

    page_index += 1
    if page_index * 2 >= len(lines):
        page_index = 0  # loop message

# ================= Button =================
def next_message():
    global current_index, page_index

    if not messages:
        return

    row, _ = messages[current_index]
    msg_sheet.update_cell(row, 3, 1)  # Seen = 1

    current_index += 1
    page_index = 0

    if current_index >= len(messages):
        load_messages()

    LCD1602.clear()

# ================= Polling =================
def poll_for_messages():
    global last_poll_time
    now = time.time()

    if now - last_poll_time >= POLL_INTERVAL:
        last_poll_time = now
        load_messages()

# ================= Cleanup =================
def cleanup(signal_num=None, frame=None):
    GPIO.output(LED_PIN, LED_OFF)
    GPIO.cleanup()
    LCD1602.clear()
    sys.exit(0)

# ================= Main Loop =================
def main():
    setup()
    load_messages()
    show_next_page()

    signal.signal(signal.SIGINT, cleanup)

    last_button = GPIO.HIGH
    last_page_time = time.time()

    while True:
        now = time.time()

        # ---- Page looping ----
        if now - last_page_time >= PAGE_DISPLAY_TIME + PAGE_GAP_TIME:
            show_next_page()
            last_page_time = now

        # ---- Button handling ----
        current_button = GPIO.input(BUTTON_PIN)

        if current_button == BUTTON_PRESSED and last_button == GPIO.HIGH:
            next_message()
            time.sleep(0.3)  # debounce
            show_next_page()
            last_page_time = time.time()

        last_button = current_button

        # ---- Poll Google Sheets ----
        poll_for_messages()

        time.sleep(0.05)

if __name__ == "__main__":
    main()
