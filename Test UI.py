import customtkinter as ctk
import random
import string

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

app = ctk.CTk()
app.geometry("900x520")
app.title("Remote Admin Tool")
app.resizable(False, False)

# SIDEBAR
sidebar = ctk.CTkFrame(app, width=180, corner_radius=0)
sidebar.pack(side="left", fill="y")

ctk.CTkLabel(
    sidebar,
    text="RAT Panel",
    font=ctk.CTkFont(size=18, weight="bold")
).pack(pady=20)

# MAIN
main = ctk.CTkFrame(app)
main.pack(side="right", expand=True, fill="both", padx=10, pady=10)

status = ctk.CTkLabel(main, text="Status: Disconnected")
status.pack(anchor="w", pady=(0, 10))

terminal = ctk.CTkTextbox(main, font=("Consolas", 12))
terminal.pack(expand=True, fill="both")

PROMPT = "> "
prompt_index = "1.0"
one_time_code = None

# TERMINAL CONTROL
def write(text=""):
    global prompt_index
    terminal.insert("end", text + "\n")
    terminal.insert("end", PROMPT)
    terminal.see("end")
    prompt_index = terminal.index("end-1c")

def prevent_edit(event):
    if terminal.compare("insert", "<", prompt_index):
        return "break"

def handle_backspace(event):
    if terminal.compare("insert", "<=", prompt_index):
        return "break"

def handle_enter(event):
    command = terminal.get(prompt_index, "end-1c").strip()
    terminal.insert("end", "\n")
    write(f"[input received] {command}")
    return "break"

terminal.bind("<Key>", prevent_edit)
terminal.bind("<BackSpace>", handle_backspace)
terminal.bind("<Return>", handle_enter)
terminal.bind("<Button-1>", lambda e: terminal.mark_set("insert", "end"))

# CODE LOGIC
def generate_code():
    global one_time_code
    one_time_code = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=6)
    )
    write(f"[+] One-time code generated: {one_time_code}")

def connect():
    global one_time_code

    if not one_time_code:
        write("[!] No active code. Generate one first.")
        return

    dialog = ctk.CTkInputDialog(
        title="Connect",
        text="Enter one-time code:"
    )
    entered = dialog.get_input()

    if entered != one_time_code:
        write("[!] Invalid code")
        return

    status.configure(text="Status: Connected")
    write("[+] Connection successful")
    one_time_code = None  # invalidate code

def disconnect():
    status.configure(text="Status: Disconnected")
    write("[-] Client disconnected")

# SIDEBAR BUTTONS
ctk.CTkButton(sidebar, text="Generate Code", command=generate_code).pack(
    pady=8, padx=20, fill="x"
)

ctk.CTkButton(sidebar, text="Connect", command=connect).pack(
    pady=8, padx=20, fill="x"
)

ctk.CTkButton(sidebar, text="Disconnect", command=disconnect).pack(
    pady=8, padx=20, fill="x"
)

ctk.CTkButton(sidebar, text="Exit", command=app.destroy).pack(
    pady=8, padx=20, fill="x"
)

# INIT
write("Application started.")
write("Generate a one-time code to begin.")

app.mainloop()
