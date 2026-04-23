import customtkinter as ctk
import random
import string
import subprocess
import threading
import time

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Palette ──────────────────────────────────────────────────────────────────
BG = "#141414"
SIDEBAR = "#1c1c1c"
CARD = "#191919"
BORDER = "#2e2e2e"
ACCENT = "#c47c3a"
ACCENT_HV = "#a3622c"
DANGER = "#a84040"
DANGER_HV = "#8c3333"
MUTED = "#6b6b6b"
FG = "#dcdcdc"
GREEN = "#4a9e6b"
RED = "#b85c5c"
FONT_UI = ("Segoe UI", 13)
FONT_MONO = ("Cascadia Code", 12)

app = ctk.CTk()
app.attributes("-alpha", 0.0)
app.configure(fg_color=BG)
client_process = None
server_process = None
app.geometry("960x560")
app.title("Remote Admin Tool")
app.resizable(False, False)


# ── ANIMATIONS ───────────────────────────────────────────────────────────────

def fade_in_window():
    alpha = app.attributes("-alpha")
    if alpha < 1.0:
        alpha += 0.05
        app.attributes("-alpha", alpha)
        app.after(15, fade_in_window)


def animate_status_dot():
    if status.cget("text") == "Disconnected":
        current_color = status_dot.cget("text_color")
        # Алекс: По-плавно преливане на цветовете за "дишащ" ефект
        next_color = "#3d2b2b" if current_color == RED else RED
        status_dot.configure(text_color=next_color)
    app.after(1000, animate_status_dot)


def typewriter_text(text, index=0):  # Алекс: Анимация тип "пишеща машина" за терминала
    if index < len(text):
        terminal.insert("end", text[index])
        terminal.see("end")
        app.after(30, lambda: typewriter_text(text, index + 1))
    else:
        terminal.insert("end", "\n" + PROMPT)
        global prompt_index
        prompt_index = terminal.index("end-1c")


# ── COMPONENTS ───────────────────────────────────────────────────────────────

class ModernButton(ctk.CTkButton):  # Алекс: Подобрен бутон с динамична промяна на височината
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_height = kwargs.get("height", 38)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        self.configure(height=self.original_height + 4, border_width=1, border_color=FG)

    def on_leave(self, event):
        self.configure(height=self.original_height, border_width=0)


def on_closing():
    if client_process and client_process.poll() is None:
        client_process.terminate()
    if server_process and server_process.poll() is None:
        server_process.terminate()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", on_closing)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
sidebar = ctk.CTkFrame(app, width=220, corner_radius=0, fg_color=SIDEBAR)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

title_label = ctk.CTkLabel(
    sidebar,
    text="RAT Panel",
    font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
    text_color=FG,
)
title_label.pack(pady=(30, 4), padx=20)

ctk.CTkLabel(
    sidebar,
    text="SYSTEM SECURE ACCESS",  # Алекс: По-модерно звучене
    font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
    text_color=ACCENT,
).pack(pady=(0, 24), padx=20)

# Алекс: Разделител с лека прозрачност
ctk.CTkFrame(sidebar, height=2, fg_color=BORDER).pack(fill="x", padx=25, pady=(0, 20))


def sidebar_btn(text, cmd, color=ACCENT, hover=ACCENT_HV):
    return ModernButton(
        sidebar,
        text=text,
        command=cmd,
        fg_color=color,
        hover_color=hover,
        text_color=FG,
        font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        corner_radius=10,
        height=38,
    )


# ── MAIN AREA ─────────────────────────────────────────────────────────────────
main = ctk.CTkFrame(app, fg_color=BG)
main.pack(side="right", expand=True, fill="both", padx=20, pady=20)

status_row = ctk.CTkFrame(main, fg_color="transparent")
status_row.pack(fill="x", pady=(0, 15))

status_dot = ctk.CTkLabel(status_row, text="●", font=ctk.CTkFont(size=16), text_color=RED)
status_dot.pack(side="left", padx=(5, 8))

status = ctk.CTkLabel(
    status_row,
    text="Disconnected",
    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
    text_color=MUTED,
)
status.pack(side="left")

terminal = ctk.CTkTextbox(
    main,
    font=ctk.CTkFont(family="Cascadia Code", size=12),
    fg_color=CARD,
    text_color=FG,
    border_color=BORDER,
    border_width=2,  # Алекс: Малко по-дебела рамка за по-голям контраст
    corner_radius=15,
    scrollbar_button_color=BORDER,
    scrollbar_button_hover_color=ACCENT,
)
terminal.pack(expand=True, fill="both")

PROMPT = "› "
prompt_index = "1.0"


# ── TERMINAL LOGIC ────────────────────────────────────────────────────────────

def write_output(text=""):
    global prompt_index
    terminal.insert("end", text + "\n")
    terminal.insert("end", PROMPT)
    terminal.see("end")
    prompt_index = terminal.index("end-1c")


def handle_enter(event):
    global client_process
    command = terminal.get(prompt_index, "end-1c").strip()
    if not command: return "break"
    terminal.insert("end", "\n")

    if client_process and client_process.poll() is None:
        client_process.stdin.write(command + "\n")
        client_process.stdin.flush()
        if command in ("/exit", "exit"):
            client_process = None
            set_status_disconnected()
            write_output("[-] Session ended.")
    else:
        write_output("[!] System offline. Please connect first.")

    terminal.see("end")
    return "break"


terminal.bind("<Return>", handle_enter)


def set_status_connected():
    status_dot.configure(text_color=GREEN)
    status.configure(text="System Online", text_color=GREEN)  # Алекс: Промяна на текста за по-професионално излъчване


def set_status_disconnected():
    status_dot.configure(text_color=RED)
    status.configure(text="Disconnected", text_color=MUTED)


# ── ACTIONS ───────────────────────────────────────────────────────────────────

def generate_code():
    code = "".join(random.choices(string.digits, k=6))
    write_output(f"[+] Security Code Generated: {code}")


def connect():
    set_status_connected()
    write_output("[+] Establishing encrypted tunnel...")


def disconnect():
    set_status_disconnected()
    write_output("[-] Connection terminated by user.")


# ── SIDEBAR BUTTONS ───────────────────────────────────────────────────────────
sidebar_btn("Generate Code", generate_code).pack(pady=8, padx=20, fill="x")
sidebar_btn("Connect", connect).pack(pady=8, padx=20, fill="x")
sidebar_btn("Disconnect", disconnect, color=DANGER, hover=DANGER_HV).pack(pady=8, padx=20, fill="x")

ctk.CTkFrame(sidebar, height=1, fg_color=BORDER).pack(fill="x", padx=25, pady=(15, 15))
sidebar_btn("Exit System", on_closing, color=DANGER, hover=DANGER_HV).pack(pady=8, padx=20, fill="x")

# ── INIT ──────────────────────────────────────────────────────────────────────
fade_in_window()
animate_status_dot()

# Алекс: Стартираме терминала с пишеща машина за готин ефект
typewriter_text("Initializing remote administration protocols...")

app.mainloop()