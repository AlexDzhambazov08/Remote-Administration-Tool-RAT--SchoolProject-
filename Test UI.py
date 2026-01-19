import customtkinter

#---------------------------
#window with code
class ToplevelWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("450x200")
        self.resizable(False, False)
        self.title("One-time use code")

        self.label = customtkinter.CTkLabel(self, text="*generated code here*")
        self.label.pack(padx=20, pady=20)

        self.label = customtkinter.CTkLabel(self, text="This code is supposed to be given to the machine that will be connecting!")
        self.label.pack(padx=20, pady=20)

#--------------------------------
class App(customtkinter.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("500x400")
        self.resizable(False, False)
        self.title("Remote Administration Tool")

        self.button_1 = customtkinter.CTkButton(self, text="Setup connection", command=self.open_toplevel, fg_color="#c73d06", hover_color="#962f06")
        self.button_1.pack(side="top", padx=20, pady=20)

        self.toplevel_window = None

    def open_toplevel(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow(self)  # create window if its None or destroyed
        else:
            self.toplevel_window.focus()  # if window exists focus it


app = App()
app.mainloop()