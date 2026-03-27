import customtkinter as ctk
import random
import string
import subprocess
import threading

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

app = ctk.CTk()
client_process = None
server_process = None
app.geometry("900x520")
app.title("Remote Admin Tool")
app.resizable(False, False)

def on_closing():
    if client_process and client_process.poll() is None:
        client_process.terminate()
    if server_process and server_process.poll() is None:
        server_process.terminate()
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_closing)

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
def write_output(text=""):
    global prompt_index
    terminal.delete(prompt_index, "end")
    terminal.insert("end", text + "\n")
    terminal.insert("end", PROMPT)
    terminal.see("end")
    prompt_index = terminal.index("end-1c")

def show_prompt():
    global prompt_index
    if terminal.get("end-3c", "end-1c") == PROMPT:  # remove duplicate prompt
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
                status.configure(text="Status: Disconnected")
                write("[-] Disconnected from server")
                return "break"
        except Exception as e:
            write(f"[!] Error sending command: {e}")
            client_process = None
            status.configure(text="Status: Disconnected")
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

# CODE LOGIC
def generate_code():
    global one_time_code, server_process
    # Server expects a hardcoded one-time code (see server.py)
    one_time_code = "123456"
    write(f"[+] One-time code generated: {one_time_code}")
    write("[!] Be careful who you give access!")

    if server_process is None or server_process.poll() is not None:
        server_process = subprocess.Popen(['python', 'server.py'])
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


    # Reset the terminal so it behaves like a command console
    terminal.delete("1.0", "end")
    write("[+] Connecting...")

    # Launch client as a subprocess and pipe its stdin/stdout
    if client_process is None or client_process.poll() is not None:
        client_process = subprocess.Popen(
            ['python', '-u', 'client.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Provide prompts expected by client.py
        client_process.stdin.write(server_ip + "\n")
        client_process.stdin.write(entered + "\n")
        client_process.stdin.flush()

        threading.Thread(target=_read_client_output, args=(client_process,), daemon=True).start()

        status.configure(text="Status: Connected")
        # NOTE: To make onetime code non reusable add this line:
        # one_time_code = None
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

ctk.CTkButton(sidebar, text="Exit", command=on_closing).pack(
    pady=8, padx=20, fill="x"
)

# INIT
write("Application started.")
write("Generate a one-time code to start your server.")

app.mainloop()
