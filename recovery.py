import os
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, Listbox, END
import importlib
import threading

try:
    import wmi
except ImportError:
    wmi = None

# --- Global variables ---
plugins = []
selected_device = None

# --- Load plugins ---
def load_plugins():
    plugin_folder = "plugins"
    if not os.path.exists(plugin_folder):
        os.makedirs(plugin_folder)

    for file in os.listdir(plugin_folder):
        if file.endswith(".py") and file != "__init__.py":
            module_name = f"{plugin_folder}.{file[:-3]}"
            try:
                module = importlib.import_module(module_name)
                plugins.append(module)
            except Exception as e:
                print(f"Error loading plugin {file}: {e}")

# --- Device selection with list (like testdisk) ---
def select_device():
    global selected_device

    if not wmi:
        messagebox.showerror("Error", "Module 'wmi' not installed. Run: pip install wmi")
        return

    c = wmi.WMI()
    disks = c.Win32_DiskDrive()

    if not disks:
        messagebox.showwarning("No devices", "No disks found!")
        return

    win = Toplevel(root)
    win.title("Select device")
    win.geometry("500x250")

    listbox = Listbox(win, width=70, height=10)
    listbox.pack(pady=10)

    disk_map = []
    for d in disks:
        idx = int(d.Index)
        size_gb = int(d.Size) // (1024**3) if d.Size else 0
        name = f"Disk {idx}: {d.Caption} ({size_gb} GB)"
        listbox.insert(END, name)
        disk_map.append(idx)

    def confirm():
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a disk.")
            return
        disk_idx = disk_map[sel[0]]
        global selected_device
        selected_device = f"\\\\.\\PhysicalDrive{disk_idx}"
        messagebox.showinfo("Device selected", f"Using device: {selected_device}")
        win.destroy()

    btn_ok = tk.Button(win, text="OK", command=confirm)
    btn_ok.pack(pady=5)

# --- Run deep recovery (plugin) ---
def run_deep_recovery():
    if not selected_device:
        messagebox.showwarning("No device", "Please select a device first!")
        return
    import plugins.sd_plugin as sd

    output_folder = filedialog.askdirectory(title="Choose folder for recovered files")
    if not output_folder:
        return

    cancel_requested = {"value": False}

    def worker():
        tool = sd.GeodesyRecoveryTool(selected_device, output_folder)
        tool.recover(cancel_requested=cancel_requested)
        if cancel_requested["value"]:
            messagebox.showinfo("Cancelled", "❌ Recovery cancelled.")
        else:
            messagebox.showinfo("Deep Recovery", f"Recovery finished!\nFiles saved to: {output_folder}")
        win.destroy()

    win = Toplevel(root)
    win.title("Deep recovery")
    win.geometry("300x120")
    tk.Label(win, text=f"Recovering from: {selected_device}").pack(pady=10)

    btn_cancel = tk.Button(win, text="Cancel", command=lambda: cancel_requested.update({"value": True}))
    btn_cancel.pack(pady=10)

    threading.Thread(target=worker, daemon=True).start()
    win.grab_set()

# --- Create disk image (plugin) ---
def create_disk_image():
    if not selected_device:
        messagebox.showwarning("No device", "Please select a device first!")
        return
    import plugins.sd_plugin as sd
    save_path = filedialog.asksaveasfilename(title="Save disk image as", defaultextension=".img")
    if not save_path:
        return
    sd.create_disk_image_with_progress(selected_device, save_path)

# --- GUI ---
root = tk.Tk()
root.title("Geodesy SD Card Recovery")
root.geometry("350x200")

btn_device = tk.Button(root, text="Select device", command=select_device)
btn_device.pack(pady=15)

btn_recover = tk.Button(root, text="Deep recovery (raw device)", command=run_deep_recovery)
btn_recover.pack(pady=15)

btn_image = tk.Button(root, text="Create disk image", command=create_disk_image)
btn_image.pack(pady=15)

# Load plugins
load_plugins()

root.mainloop()
