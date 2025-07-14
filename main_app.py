import tkinter as tk
from tkinter import messagebox
from input_table_module import InputTable 
from plc_interface import PLCInterface


class ModeSwitcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ergo UI")
        self.root.geometry("1450x600")

        #initializing the plc connection
        self.plc = PLCInterface('192.168.1.10')
        self.plc.connect()

        # Top frame
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(side="top", fill="x", pady=5)

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill="both", expand=True)

        self.countdown_seconds = 5
        self.countdown_label = None

        # Initialize layout elements
        self.init_mode_buttons()
        self.init_pretension_controls()
        self.init_live_graph_button()   # Add this for Start Live Grap


        self.active_frame = None

    def init_mode_buttons(self):
        self.add_mode_button("Isometric", "#007FFF", lambda: self.show_input_table("Isometric"))
        self.add_mode_button("Isotonic", "#00A86B", lambda: self.show_input_table("Isotonic"))
        self.add_mode_button("Isokinetic", "#E32636", lambda: self.show_input_table("Isokinetic"))

    def add_mode_button(self, text, border_color, command):
        button = tk.Button(
            self.top_frame,
            text=text,
            command=command,
            font=("Arial", 12, "bold"),
            relief="solid",
            bd=2,
            fg=border_color,
            highlightbackground=border_color,
            highlightcolor=border_color,
            highlightthickness=2
        )
        button.pack(side="left", padx=10)

    def init_pretension_controls(self):
        # Right-side frame for pretension controls
        self.right_frame = tk.Frame(self.top_frame)
        self.right_frame.pack(side="right", padx=10)

        pretension_label = tk.Label(self.right_frame, text="Pretension (Nm):", font=("Georgia", 11))
        pretension_label.pack(side="left", padx=(5, 2))

        self.pretension_spinbox = tk.Spinbox(self.right_frame, from_=0, to=1000, width=8, font=("Georgia", 11))
        self.pretension_spinbox.pack(side="left", padx=(0, 10))
        self.pretension_spinbox.delete(0, tk.END)
        self.pretension_spinbox.insert(0, "10")  # Default value

        # Blinking light
        self.light_canvas = tk.Canvas(self.right_frame, width=20, height=20, highlightthickness=0)
        self.light_id = self.light_canvas.create_oval(2, 2, 18, 18, fill="gray")
        self.light_canvas.pack(side="right", padx=5)

        # Pretension button
        self.pretension_button = tk.Button(
            self.right_frame,
            text="Pretension",
            command=self.pretension_action,
            font=("Arial", 11, "bold"),
            bg="#b2d1b2", fg="white",
            relief="raised",
            padx=8, pady=5
        )
        self.pretension_button.pack(side="right", padx=5)


        self.blink_count = 0
        self.blinking = False


    def pretension_action(self):
        if self.plc:
            try:
                # Step 1: Get value from spinbox
                value = float(self.pretension_spinbox.get())

                # Step 2: Write value to PLC
                success = self.plc.write('matlabPretension', value)
                if not success:
                    print("❌ Failed to write pretension value to PLC.")
                    return


                # Step 3: Enable pretension
                success = self.plc.start_pretension()

                if success:
                    # print(f"✅ Pretension {value} Nm routine started.") #test to check the value of the pretension being written
                    self.blink_count = 0
                    self.blinking = True
                    self.blink_light()
                else:
                    print("❌ Pretension start failed.")
            except ValueError:
                print("⚠️ Invalid pretension value in spinbox.")
            except Exception as e:
                print(f"❌ Error during pretension action: {e}")
        else:
            print("❌ No PLC connected.")

    def blink_light(self):
        if not self.blinking:
            return

        current_color = self.light_canvas.itemcget(self.light_id, "fill")
        next_color = "lightgreen" if current_color == "darkgreen" else "darkgreen"
        self.light_canvas.itemconfig(self.light_id, fill=next_color)

        self.blink_count += 1
        if self.blink_count < 12:
            self.root.after(500, self.blink_light)
        else:
            self.light_canvas.itemconfig(self.light_id, fill="white")
            self.blinking = False

    def show_input_table(self, mode):
        if self.active_frame:
            self.active_frame.destroy()

        self.active_frame = tk.Frame(self.main_frame)
        self.active_frame.pack(fill="both", expand=True)

        self.active_table = InputTable(self.active_frame, mode=mode, plc=self.plc)

    def on_closing(self):
        if self.plc:
            self.plc.disconnect()
        self.root.destroy()


    def init_live_graph_button(self):
        self.live_graph_button = tk.Button(
            self.top_frame,
            text="Start Live Graph",
            font=("Georgia", 11),
            padx=8, pady=5,
            command=self.start_live_graph_clicked
        )
        # Pack it before right_frame (pretension controls)
        self.live_graph_button.pack(side="right", padx=5)

        self.countdown_label = tk.Label(self.top_frame, text=f"Countdown: {self.countdown_seconds}", font=("Arial", 12), fg="red")
        self.countdown_label.pack(side="right", padx=(0, 10))

    def start_live_graph_clicked(self):

        # Determine test mode
       mode_map = {"Isometric": 1, "Isotonic": 2, "Isokinetic": 3}
       mode = self.active_table.mode if self.active_table else None
       mode_value = mode_map.get(mode)

       if self.plc and mode_value:
        self.plc.enable_test_mode(mode_value)


        if not self.active_table:
            messagebox.showwarning("No Mode Selected", "Please select a mode to load the input table first.")
            return

   
        self.active_table.send_spinbox_values_to_plc()

        self.live_graph_button.config(state="disabled")
        self.countdown_seconds = 5
        self.update_countdown()


    def update_countdown(self):
        if self.countdown_seconds > 0:
            self.countdown_label.config(text=f"Countdown: {self.countdown_seconds}")
            self.countdown_seconds -= 1
            self.root.after(1000, self.update_countdown)
        else:
            self.countdown_label.config(text=f"Countdown: 5")  # reset to 5 after finishing
            self.live_graph_button.config(state="normal")
            self.active_table.start_live_graph()


if __name__ == "__main__":
    root = tk.Tk()
    app = ModeSwitcherApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  # handle window close to clean up PLC
    root.mainloop()





