import random
import string
import subprocess
import threading
import sys
import tkinter as tk  # Added for animation canvas - aleks
import colorsys  # Added for RGB logic - aleks

if len(sys.argv) > 1:
    if sys.argv[1] == "--server":
        import server
        sys.exit()
    elif sys.argv[1] == "--client":
        import client
        sys.exit()

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Palette ──────────────────────────────────────────────────────────────────
BG        = "#141414"   # pure dark neutral
SIDEBAR   = "#1c1c1c"   # slightly lighter neutral sidebar
CARD      = "#191919"   # dark card bg
BORDER    = "#2e2e2e"   # subtle grey border
ACCENT    = "#c47c3a"   # muted orange — buttons only
ACCENT_HV = "#a3622c"   # deeper orange hover — buttons only
DANGER    = "#a84040"   # muted red for disconnect/exit
DANGER_HV = "#8c3333"
MUTED     = "#6b6b6b"   # neutral grey muted text
FG        = "#dcdcdc"   # clean light grey text
GREEN     = "#4a9e6b"   # muted green status
RED       = "#b85c5c"   # muted red status
FONT_UI   = ("Segoe UI", 13)
FONT_MONO = ("Cascadia Code", 12) if True else ("Consolas", 12)

app = ctk.CTk()
app.configure(fg_color=BG)
client_process = None
server_process = None
app.geometry("960x560")
app.title("Remote Admin Tool")
app.resizable(False, False)

def get_target_cmd(target_name):
    if getattr(sys, 'frozen', False):
        return [sys.executable, f"--{target_name}"]
    else:
        return [sys.executable, "-u", f"{target_name}.py"]

def on_closing():
    if client_process and client_process.poll() is None:
        client_process.terminate()
    if server_process and server_process.poll() is None:
        server_process.terminate()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", on_closing)


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
sidebar = ctk.CTkFrame(app, width=200, corner_radius=0, fg_color=SIDEBAR)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

ctk.CTkLabel(
    sidebar,
    text="RAT Panel",
    font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
    text_color=FG,
).pack(pady=(28, 4), padx=20)

ctk.CTkLabel(
    sidebar,
    text="Remote Admin Tool",
    font=ctk.CTkFont(family="Segoe UI", size=10),
    text_color=MUTED,
).pack(pady=(0, 24), padx=20)

# Divider
ctk.CTkFrame(sidebar, height=1, fg_color=BORDER).pack(fill="x", padx=16, pady=(0, 20))


def sidebar_btn(text, cmd, color=ACCENT, hover=ACCENT_HV):
    return ctk.CTkButton(
        sidebar,
        text=text,
        command=cmd,
        fg_color=color,
        hover_color=hover,
        text_color=FG,
        font=ctk.CTkFont(family="Segoe UI", size=13),
        corner_radius=8,
        height=38,
    )


# ── MAIN AREA ─────────────────────────────────────────────────────────────────
main = ctk.CTkFrame(app, fg_color=BG)
main.pack(side="right", expand=True, fill="both", padx=16, pady=16)

# Status bar row
status_row = ctk.CTkFrame(main, fg_color="transparent")
status_row.pack(fill="x", pady=(0, 10))

status_dot = ctk.CTkLabel(status_row, text="●", font=ctk.CTkFont(size=12), text_color=RED)
status_dot.pack(side="left", padx=(0, 6))

status = ctk.CTkLabel(
    status_row,
    text="Disconnected",
    font=ctk.CTkFont(family="Segoe UI", size=12),
    text_color=MUTED,
)
status.pack(side="left")

# Terminal
terminal = ctk.CTkTextbox(
    main,
    font=ctk.CTkFont(family="Cascadia Code", size=12),
    fg_color=CARD,
    text_color=FG,
    border_color=BORDER,
    border_width=1,
    corner_radius=10,
    scrollbar_button_color=BORDER,
    scrollbar_button_hover_color=ACCENT,
)
terminal.pack(expand=True, fill="both")

PROMPT = "› "
prompt_index = "1.0"
one_time_code = None


# ── TERMINAL CONTROL ──────────────────────────────────────────────────────────
def write_output(text=""):
    global prompt_index
    terminal.delete(prompt_index, "end")
    terminal.insert("end", text + "\n")
    terminal.insert("end", PROMPT)
    terminal.see("end")
    prompt_index = terminal.index("end-1c")


def show_prompt():
    global prompt_index
    if terminal.get("end-3c", "end-1c") == PROMPT:
        terminal.delete("end-3c", "end-1c")
    terminal.insert("end", PROMPT)
    terminal.see("end")
    prompt_index = terminal.index("end-1c")


def write(text=""):
    write_output(text)
    show_prompt()


def _read_client_output(proc):
    prompt_parts = [
        "Enter server IP:",
        "Enter one-time code:",
        "Enter command (use '/exit' or 'exit' to quit):",
        "Server response: ACCEPT",
        "Server response: REJECT",
        "Server reply:",
    ]
    try:
        for line in proc.stdout:
            if not line:
                break
            cleaned = line.rstrip("\n")
            for part in prompt_parts:
                cleaned = cleaned.replace(part, "")
            cleaned = cleaned.strip()
            if not cleaned:
                continue
            app.after(0, lambda l=cleaned: write_output(l))
    except Exception:
        pass


def prevent_edit(event):
    if terminal.compare("insert", "<", prompt_index):
        return "break"


def handle_backspace(event):
    if terminal.compare("insert", "<=", prompt_index):
        return "break"


def handle_enter(event):
    global client_process
    command = terminal.get(prompt_index, "end-1c").strip()
    if not command:
        return "break"
    terminal.insert("end", "\n")
    if client_process and client_process.poll() is None:
        try:
            client_process.stdin.write(command + "\n")
            client_process.stdin.flush()
            if command in ("/exit", "exit"):
                client_process = None
                set_status_disconnected()
                write("[-] Disconnected from server")
                return "break"
        except Exception as e:
            write(f"[!] Error sending command: {e}")
            client_process = None
            set_status_disconnected()
            return "break"
    else:
        write("[!] Not connected. Click Connect to establish a connection.")
        return "break"
    show_prompt()
    return "break"


terminal.bind("<Key>", prevent_edit)
terminal.bind("<BackSpace>", handle_backspace)
terminal.bind("<Return>", handle_enter)
terminal.bind("<Button-1>", lambda e: terminal.mark_set("insert", "end"))


def set_status_connected():
    status_dot.configure(text_color=GREEN)
    status.configure(text="Connected", text_color=GREEN)


def set_status_disconnected():
    status_dot.configure(text_color=RED)
    status.configure(text="Disconnected", text_color=MUTED)


# ── CODE LOGIC ────────────────────────────────────────────────────────────────
def generate_code():
    global one_time_code, server_process
    one_time_code = "123456"
    write(f"[+] One-time code generated: {one_time_code}")
    write("[!] Be careful who you give access!")
    if server_process is None or server_process.poll() is not None:
        server_process = subprocess.Popen(get_target_cmd("server"))
        write("[+] Server started")
    else:
        write("[!] Server is already running")


def connect():
    global one_time_code, client_process
    ip_dialog = ctk.CTkInputDialog(title="Connect", text="Enter server IP:")
    server_ip = ip_dialog.get_input()
    if not server_ip:
        write("[!] Server IP not provided")
        return
    code_dialog = ctk.CTkInputDialog(title="Connect", text="Enter one-time code:")
    entered = code_dialog.get_input()
    terminal.delete("1.0", "end")
    write("[+] Connecting...")
    if client_process is None or client_process.poll() is not None:
        client_process = subprocess.Popen(
            get_target_cmd("client"),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        client_process.stdin.write(server_ip + "\n")
        client_process.stdin.write(entered + "\n")
        client_process.stdin.flush()
        threading.Thread(target=_read_client_output, args=(client_process,), daemon=True).start()
        set_status_connected()
        write("[+] Connected. Enter commands below.")
    else:
        write("[!] Client already running")


def disconnect():
    global client_process
    if client_process and client_process.poll() is None:
        try:
            client_process.stdin.write("/exit\n")
            client_process.stdin.flush()
        except Exception:
            pass
        client_process = None
    set_status_disconnected()
    write("[-] Client disconnected")


# ── SIDEBAR BUTTONS ───────────────────────────────────────────────────────────
sidebar_btn("Generate Code", generate_code).pack(pady=6, padx=20, fill="x")
sidebar_btn("Connect", connect).pack(pady=6, padx=20, fill="x")
sidebar_btn("Disconnect", disconnect, color=DANGER, hover=DANGER_HV).pack(pady=6, padx=20, fill="x")

ctk.CTkFrame(sidebar, height=1, fg_color=BORDER).pack(fill="x", padx=16, pady=(14, 14))

sidebar_btn("Exit", on_closing, color=DANGER, hover=DANGER_HV).pack(pady=6, padx=20, fill="x")


# ── INIT ──────────────────────────────────────────────────────────────────────
write("Application started.")
write("Generate a one-time code to start your server.")


# ══════════════════════════════════════════════════════════════════════════════
# Made by Aleks — ANIMATIONS
# ══════════════════════════════════════════════════════════════════════════════

# 1. Smooth Window Fade-In
# Made by Aleks
app.attributes("-alpha", 0.0)


def fade_in():
    alpha = app.attributes("-alpha")
    if alpha < 1.0:
        alpha += 0.05
        app.attributes("-alpha", alpha)
        app.after(20, fade_in)


# 2. Sidebar Entrance Slide
# Made by Aleks
sidebar.configure(width=0)


def slide_sidebar():
    cur_width = sidebar.winfo_width()
    if cur_width < 200:
        sidebar.configure(width=cur_width + 10)
        app.after(10, slide_sidebar)


# 3. Status Dot Pulsing Animation
# Made by Aleks
def pulse_dot(state=True):
    current_color = status_dot.cget("text_color")
    if current_color != MUTED:
        new_alpha = "#555555" if state else (GREEN if status.cget("text") == "Connected" else RED)
        status_dot.configure(text_color=new_alpha)
    app.after(800, lambda: pulse_dot(not state))


# 4. Terminal Border Glow on Focus
# Made by Aleks
def on_focus_in(event):
    terminal.configure(border_color=ACCENT, border_width=2)


def on_focus_out(event):
    terminal.configure(border_color=BORDER, border_width=1)


terminal._textbox.bind("<FocusIn>", on_focus_in)
terminal._textbox.bind("<FocusOut>", on_focus_out)


# 5. Button Hover Scale Effect Logic
# Made by Aleks
def setup_button_hovers():
    for widget in sidebar.winfo_children():
        if isinstance(widget, ctk.CTkButton):
            def enter(e, btn=widget):
                btn.configure(border_width=1, border_color=FG)

            def leave(e, btn=widget):
                btn.configure(border_width=0)

            widget.bind("<Enter>", enter)
            widget.bind("<Leave>", leave)


# 6. RGB Terminal Outline
# Made by Aleks
rgb_hue = 0


def update_rgb_border():
    global rgb_hue
    rgb_hue += 0.01
    if rgb_hue > 1.0:
        rgb_hue = 0
    # Convert HSV to RGB for smooth cycling
    r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(rgb_hue, 1, 1)]
    hex_color = f'#{r:02x}{g:02x}{b:02x}'

    terminal.configure(border_color=hex_color, border_width=2)
    app.after(50, update_rgb_border)


# Trigger Startup Animations
# Made by Aleks
app.after(100, fade_in)
app.after(150, slide_sidebar)
app.after(500, setup_button_hovers)
app.after(1000, pulse_dot)
app.after(1000, update_rgb_border)  # Start RGB Outline

# ══════════════════════════════════════════════════════════════════════════════

app.mainloop()