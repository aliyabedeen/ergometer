from decimal import Decimal
import tkinter as tk
import csv
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import numpy as np
import time
from plc_interface import PLCInterface


class InputTable:
    def __init__(self, root, mode=None, plc=None):
        self.root = root
        self.mode = mode
        self.plc=plc
        self.ani = None
        if mode == "Isometric":
            self.columns = ["Name", "Time(s)", "Target (% of Max Torque)", "Cont. Time(s)", "Rest Time(s)", "Enable"]
        elif mode == "Isotonic":
            self.columns = ["Name", "Time(s)", "Torque Applied (Nm)", "Contraction Time(s)", "Rest Time(s)", "Enable"]
        elif mode == "Isokinetic":
            self.columns = ["Name", "Time(s)", "Speed Limit (Deg/s)", "Contraction Time(s)", "Rest Time(s)", "Enable"]
        else:
            self.columns = ["Name", "Time(s)", "Target", "Cont. Time(s)", "Rest Time(s)", "Enable"]

        self.spinboxes={}
        # Set background color based on mode
        if mode == "Isometric":
            bg_color = "#cce6ff"  # light blue
        elif mode == "Isotonic":
            bg_color = "#ccffe6"  # light green
        elif mode == "Isokinetic":
            bg_color = "#ffe6e6"  # light red
        else:
            bg_color = "white"

        self.root.configure(bg=bg_color)

        # Canvas and Scrollbar
        canvas = tk.Canvas(root, bg=bg_color)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        self.scrollable_frame = tk.Frame(canvas, bg=bg_color)
        canvas_frame = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Make the inner frame resize with the canvas
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        # Configure canvas scrolling
        canvas.configure(yscrollcommand=scrollbar.set)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

                # Mode-specific spinboxes
        self.spinbox_frame = tk.Frame(self.scrollable_frame, bg=bg_color)
        self.spinbox_frame.grid(row=0, column=0, columnspan=len(self.columns), sticky="ew", pady=(10, 5))
        
        if self.mode == "Isometric":
            self.create_spinbox(self.spinbox_frame, "Torque Target (Nm):", 0, 0)
  
        elif self.mode == "Isotonic":
            self.create_spinbox(self.spinbox_frame, "Range of Motion (deg):", 0, 0)

        elif self.mode == "Isokinetic":
            self.create_spinbox(self.spinbox_frame, "Min Torque Threshold (Nm):", 0, 0)
            self.create_spinbox(self.spinbox_frame, "Range of Motion (deg):", 0, 2)
           

        


        

        # Mouse scrolling (cross-platform)
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        # Configure columns to resize
        for col in range(len(self.columns)):
            self.scrollable_frame.grid_columnconfigure(col, weight=1, minsize=100)
        self.scrollable_frame.grid_columnconfigure(0, weight=2, minsize=100)


        

       
        # mouse stuff
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))


        for col in range(len(self.columns)):
            self.scrollable_frame.grid_columnconfigure(col, weight=1, minsize=100)
        self.scrollable_frame.grid_columnconfigure(0, weight=2, minsize=100)

        self.entries = []
        self.vars = []

        for col, col_name in enumerate(self.columns):
            label = tk.Label(self.scrollable_frame, text=col_name, borderwidth=1, relief="solid",
                             font=("Times New Roman", 12, "bold"))
            label.grid(row=1, column=col, sticky="nsew")

        for row in range(2, 18):
            row_entries = []
            for col in range(len(self.columns) - 1):
                entry_width = 25 if col == 0 else 15
                entry = tk.Entry(self.scrollable_frame, relief="solid", width=entry_width, font=("Georgia", 15))
                entry.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
                row_entries.append(entry)

            var = tk.BooleanVar()
            cb = tk.Checkbutton(self.scrollable_frame, variable=var)
            cb.grid(row=row, column=len(self.columns) - 1, sticky="nsew", padx=1, pady=1)
            self.vars.append(var)
            self.entries.append(row_entries)

        # Preset buttons
       # Preset buttons next to the "Enable" column (i.e., column 6)
        preset_frame = tk.Frame(self.scrollable_frame, bg=bg_color)
        preset_frame.grid(row=1, column=len(self.columns), rowspan=21, sticky="nsw", padx=(10, 0), pady=(5, 5))

        preset_label = tk.Label(preset_frame, text="Presets", font=("Georgia", 10, "bold"), bg=bg_color)
        preset_label.pack(pady=(0, 5))

        preset_names = {
            "Isometric": ["MVIC", "ISO RAMP", "Isometric Preset 3"],
            "Isotonic": ["Isotonic Preset 1", "Isotonic Preset 2", "Isotonic Preset 3"],
            "Isokinetic": ["Frequency Ramp", "Oxidative Capacity", "Practice"]
        }

        # Fallback in case mode is not set
        names = preset_names.get(self.mode, ["Preset 1", "Preset 2", "Preset 3"])

        for i, label in enumerate(names):
            btn = tk.Button(
                preset_frame,
                text=label,
                command=lambda i=i+1: self.load_preset(i),  # preset_number starts from 1
                font=("Georgia", 10),
                width=18
            )
            btn.pack(pady=2)
        

        # start_plot_button = tk.Button(self.scrollable_frame, text="Start Live Graph", command=self.start_live_graph)
        # start_plot_button.grid(row=23, column=0, columnspan=len(self.columns), sticky="ew", pady=(10, 10))

        self.blink_count = 0
        self.blinking = False


    def create_spinbox(self, parent, label_text, row, col):
                label = tk.Label(parent, text=label_text, font=("Georgia", 11), bg=parent["bg"])
                label.grid(row=row, column=col, sticky="w", padx=(5, 2))
                spin = tk.Spinbox(parent, from_=0, to=1000, width=8, font=("Georgia", 11))
                spin.grid(row=row, column=col+1, sticky="w", padx=(0, 10))
                self.spinboxes[label_text.strip(":")] = spin


    def pretension_action(self):
        # Example: start pretension routine on PLC, then blink light
        if self.plc:
            success = self.plc.start_pretension()  # You must implement start_pretension()
            if success:
                print("Pretension routine started.")
                self.blink_count = 0
                self.blinking = True
                self.blink_light()
            else:
                print("Pretension Failed")
        else:
            # Just blink light as fallback
            print("No PLC connected, blinking light only.")
            self.blink_count = 0
            self.blinking = True
            self.blink_light()


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


    def load_preset(self, preset_number):
    # Example hardcoded presets; customize as needed
        presets = {
            "Isometric": {
                1: [["Rest", "5", "0", "0", "5", True], 
                    ["Contraction", "4", "100", "4", "0", True],
                    ["Recovery","5","0","0","5", True]],
                    
                2: [["Rest","90",	"0",	"0",	"90"	,True],
                    ["Stage 1",	"595",	"20",	"2",	"3",	True],
                    ["MVIC",	"5",	"100"	,"3",	"2",	True],
                    ["Stage 2"	,"595",	"40",	"2"	,"3",	True],
                    ["MVIC"	,"5"	,"100",	"3",	"2",	True],
                    ["Stage 3","595"	,"60"	,"2"	,"3",	True],
                    ["MVIC"	,"5"	,"100",	"3",	"2",	True],
                    ["Recovery",	"5",	"0"	,"0",	"5",	True]],
                    
                3: [["D", "3", "50", "1.5", "1.5", True]]
            },
            "Isotonic": {
                1: [["Rest",	"2",	"0",	"0",	"2",	True], 
                    ["Contraction set",	"2"	,"100",	"1",	"0",	True],
                    ["Recovery",	"2",	"0",	"0",	"2",	True]],

                2: [["F", "6", "50", "3", "2", True]],
                3: [["G", "4", "60", "2", "1", False]]
            },
            "Isokinetic": {
                1: [["Rest",	"90",	"0",	"0",	"90",	True],
                    ["C1",	"120",	"120",	"1",	"9",	True],
                    ["C2",	"119",	"120",	"1"	,"6",	True],
                    ["C3",	"120",	"120",	"1",	"4",	True],
                    ["C4"	,"120",	"120"	,"1",	"3",	True],
                    ["C5"	,"120", "120",	"1",	"1",	True],
                    ["Recovery",	"10",	"0",	"0",	"10",	True]],


                2: [["Rest",	"90",	"0",	"0",	"90",	True],
                    ["Contractions",	"24",	"120",	"1",	"1"	,True],
                    ["Recovery",	"10",	"0",	"0",	"10"	,True]],

                
                3: [["Rest",	"5",	"0",	"0",	"5",	True],
                    ["Contractions",	"6",	"120",	"1",	"1"	,True],
                    ["Recovery",	"10",	"0",	"0",	"10"	,True]],
            }
    }

        # Clear existing entries
        for row_entries in self.entries:
            for entry in row_entries:
                entry.delete(0, tk.END)
        for var in self.vars:
            var.set(False)

        # Load preset data into the table
        data = presets.get(self.mode, {}).get(preset_number, [])
        for i, row in enumerate(data):
            if i >= len(self.entries):
                break
            for j in range(len(row) - 1):  # Exclude checkbox
                self.entries[i][j].insert(0, row[j])
            self.vars[i].set(row[-1])
            self.root.update_idletasks()


    def build_test_plan(self):
        frame_rate = 30  # Hz
        full_signal = []
        for row_idx, row_entries in enumerate(self.entries):
            if not self.vars[row_idx].get():
                continue
            try:
                total_time = float(row_entries[1].get())
                target = float(row_entries[2].get())
                cont_time = float(row_entries[3].get())
                rest_time = float(row_entries[4].get())
            except ValueError:
                continue

            total_samples = int(total_time * frame_rate)
            cont_samples = int(cont_time * frame_rate)
            rest_samples = int(rest_time * frame_rate)

            signal = [target] * cont_samples + [0] * rest_samples
            if len(signal) < total_samples:
                signal += [0] * (total_samples - len(signal))
            else:
                signal = signal[:total_samples]
            full_signal.extend(signal)
            print("Built signal length:", len(full_signal))

        return np.array(full_signal)
    
    def send_spinbox_values_to_plc(self):
        if self.plc:
            self.plc.write_spinbox_values(self.spinboxes)
        else:
            print("No PLC connected.")


    def start_live_graph(self):
        self.send_spinbox_values_to_plc()

        full_signal = self.build_test_plan()  # build signal first
        full_length = len(full_signal)
        
        graph_window = tk.Toplevel(self.root)
        graph_window.title("Live Graph")
        graph_window.geometry("1400x900")        # ← set window size: width x height
        graph_window.minsize(800, 600)           # ← optional: enforce a minimum size

        # bigger figure
        fig, ax = plt.subplots(figsize=(12, 8), dpi=100)  
        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        # make the plot fill the window
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


        frame_rate = 30
        window_seconds = 4
        window_size = int(frame_rate * window_seconds)
        # time_data = np.linspace(-window_seconds, 0, window_size)
        time_data = np.linspace(-2,2, window_size)

        input_data = np.zeros(window_size)
        torque_data = np.full(window_size, np.nan)

               # choose labels based on mode
        if self.mode in ("Isotonic", "Isokinetic"):
            planned_lbl = "Planned Position (%)"
            live_lbl    = "Live Position (%)"
            ylabel      = "Position (%)"
        else:
            planned_lbl = "Planned Input"
            live_lbl    = "Live Torque (%)"
            ylabel      = "Torque (%)"

        input_line, = ax.plot(
            time_data, input_data,
            label=planned_lbl,
            color="blue",
            linewidth=10
        )
        torque_line, = ax.plot(
            time_data, torque_data,
            label=live_lbl,
            color="orange",
            linewidth=10
        )

        ax.set_ylim(0, 110)
        ax.set_xlim(-2, 2)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel(ylabel)
        ax.legend()
        ax.grid(True)


        index = 0
        torque_tag = 'matlabTorque'
        center_index = window_size // 2
        self.last_velocity_limit = None

        def update(frame):
            nonlocal index, center_index

            # Stop when signal ends
            if index >= full_length:
                if self.ani:
                    self.ani.event_source.stop()
                if self.plc:
                    self.plc.disable_test_mode()
                return [input_line, torque_line]

            # Slide window of planned input
            input_data[:-1] = input_data[1:]
            input_data[-1] = full_signal[index]

            # Slide window of live data up to center
            torque_data[:center_index] = torque_data[1:center_index+1]

            if self.mode == "Isokinetic":
                next_vel = full_signal[index]
                is_last = (index == full_length - 1)
                # only write when stepping into a non-zero speed,
                # or when you're at the very end and need to drop to zero
                if (next_vel > 0 and next_vel != self.last_velocity_limit) or (is_last and next_vel == 0):
                    self.plc.write('matlabVelocityLimit', int(next_vel))
                    self.last_velocity_limit = next_vel

            # Read raw PLC value
            try:
                if self.plc:
                    if self.mode in ("Isotonic", "Isokinetic"):
                        tag = 'matlabPosition'
                    else:
                        tag = 'matlabTorque'
                    result = self.plc.read(tag)
                    raw_val = float(result.value) if result and result.value is not None else 0
                else:
                    raw_val = 0
            except Exception as e:
                print(f"PLC Read Error: {e}")
                raw_val = 0

            # Choose denominator spinbox key
            if self.mode in ("Isotonic", "Isokinetic"):
                key = "Range of Motion (deg)"
            elif self.mode == "Isometric":
                key = "Torque Target (Nm)"
            else:
                key = None

            # Compute percentage or raw
            if key and key in self.spinboxes:
                denom = float(self.spinboxes[key].get()) or 1
                scaled = 100 * raw_val / denom
            else:
                scaled = raw_val

            # Insert into center of window
            torque_data[center_index] = scaled

            # Update plot lines
            input_line.set_ydata(input_data)
            torque_line.set_ydata(torque_data)

            index += 1
            return [input_line, torque_line]


            # input_line.set_ydata(input_data)
            # torque_line.set_ydata(torque_data)

            # index += 1
            # return [input_line, torque_line]

        self.ani = animation.FuncAnimation(
            fig,
            update,
            interval=1000 / frame_rate,
            blit=True,
            cache_frame_data=False,
        )
        canvas.draw()




if __name__ == "__main__":
    root = tk.Tk()
    root.title("Input Table")
    root.geometry("1200x800")
    app = InputTable(root)
    root.mainloop()
