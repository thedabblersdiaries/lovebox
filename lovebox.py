import tkinter as tk
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pygame

# ================== CONFIG ==================
SCREEN_W = 320
SCREEN_H = 240

SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
# ============================================

# ---------- Audio ----------
pygame.mixer.init()
pygame.mixer.music.load("ringtone.mp3")
pygame.mixer.music.set_volume(0.4)

# ---------- Google ----------
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
gclient = gspread.authorize(creds)

# Sheet for messages to display
msg_sheet = gclient.open("Lovebox").sheet1

# Sheet where users submit new messages
inbox_sheet = gclient.open("Lovebox_Inbox").sheet1

# ---------- Tk ----------
root = tk.Tk()
root.attributes("-fullscreen", True)
root.configure(bg="black")

canvas = tk.Canvas(root, width=SCREEN_W, height=SCREEN_H - 60, bg="black", highlightthickness=0)
canvas.pack()

btn_frame = tk.Frame(root, bg="black")
btn_frame.pack(fill="x")

# ---------- State ----------
messages = []
current_index = 0
polling_active = False

# ---------- Message Logic ----------
def load_messages():
    global messages, current_index
    rows = msg_sheet.get_all_records()
    messages = [(i + 2, row["Content"]) for i, row in enumerate(rows) if row.get("Seen") == 0]
    current_index = 0

def display_message():
    canvas.delete("all")

    if messages:
        next_btn.config(state="normal")
    else:
        next_btn.config(state="disabled")

    if not messages:
        canvas.create_text(
            SCREEN_W // 2,
            (SCREEN_H - 60) // 2,
            text="No messages\nright now!",
            fill="white",
            font=("Arial", 18),
            justify="center"
        )
        start_polling()
        return

    _, content = messages[current_index]
    canvas.create_text(
        SCREEN_W // 2,
        (SCREEN_H - 60) // 2,
        text=content,
        fill="white",
        font=("Arial", 18),
        width=SCREEN_W - 20,
        justify="center"
    )

def next_message():
    global current_index
    if messages:
        row, _ = messages[current_index]
        msg_sheet.update_cell(row, 3, 1)  # mark Seen = 1

    current_index += 1
    if current_index >= len(messages):
        messages.clear()
        pygame.mixer.music.stop()

    display_message()

# ---------- Polling ----------
def start_polling():
    global polling_active
    if not polling_active:
        polling_active = True
        root.after(30000, poll_for_messages)

def poll_for_messages():
    global polling_active
    load_messages()

    if messages:
        polling_active = False
        display_message()
        play_ringtone()
    else:
        root.after(30000, poll_for_messages)

# ---------- Ringtone ----------
def play_ringtone():
    if messages and not pygame.mixer.music.get_busy():
        pygame.mixer.music.play()
    if messages:
        root.after(30000, play_ringtone)

# ---------- Text Input with Virtual Keyboard ----------
def open_text_input():
    win = tk.Toplevel(root)
    win.attributes("-fullscreen", True)
    win.configure(bg="black")

    tk.Label(win, text="Write your message:", font=("Arial", 16), bg="black", fg="white").pack(pady=5)
    entry = tk.Text(win, height=3, width=25, font=("Arial", 14))
    entry.pack(pady=5)

    # ----- Virtual Keyboard -----
    keys = [
        "QWERTYUIOP",
        "ASDFGHJKL",
        "ZXCVBNM",
        "1234567890",
        " .,!?@#"
    ]

    def add_to_entry(char):
        entry.insert(tk.END, char)

    keyboard_frame = tk.Frame(win, bg="gray")
    keyboard_frame.pack()

    for row in keys:
        row_frame = tk.Frame(keyboard_frame, bg="gray")
        row_frame.pack()
        for char in row:
            tk.Button(
                row_frame, text=char, width=3, height=2,
                command=lambda c=char: add_to_entry(c)
            ).pack(side="left", padx=1, pady=1)

    # Backspace
    tk.Button(keyboard_frame, text="⌫", width=3, height=2, command=lambda: entry.delete("end-2c", tk.END)).pack(pady=2)

    # Send button
    def send_text():
        text = entry.get("1.0", "end").strip()
        if text:
            inbox_sheet.append_row([text, 0, datetime.now().isoformat()])
        win.destroy()

    control = tk.Frame(win, bg="black")
    control.pack(fill="x", pady=5)
    tk.Button(control, text="Send ❤️", font=("Arial", 14), command=send_text).pack(side="left", expand=True, fill="x")
    tk.Button(control, text="Back", font=("Arial", 14), command=win.destroy).pack(side="right", expand=True, fill="x")

# ---------- Buttons ----------
next_btn = tk.Button(btn_frame, text="Next", font=("Arial", 16), command=next_message)
next_btn.pack(side="left", expand=True, fill="x")

write_btn = tk.Button(btn_frame, text="Write Message ✏️", font=("Arial", 16), command=open_text_input)
write_btn.pack(side="right", expand=True, fill="x")

# ---------- Start ----------
load_messages()
display_message()
root.mainloop()
