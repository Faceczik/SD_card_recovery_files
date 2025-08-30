import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading

class GeodesyRecoveryTool:
    def __init__(self, device_path, output_folder, formats_file="formats.txt"):
        self.device_path = device_path
        self.output_folder = output_folder
        self.text_formats, self.binary_formats = self.load_formats(formats_file)
        os.makedirs(self.output_folder, exist_ok=True)

    def load_formats(self, formats_file):
        text_formats, binary_formats = [], []
        current_section = None

        if not os.path.exists(formats_file):
            print(f"⚠️ Warning: formats file {formats_file} not found. Using default.")
            return [".txt", ".csv", ".obs", ".nav"], [".bin", ".raw", ".dat"]

        with open(formats_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    if "text" in line.lower():
                        current_section = "text"
                    elif "binary" in line.lower():
                        current_section = "binary"
                    continue
                if current_section == "text":
                    text_formats.append(line.lower())
                elif current_section == "binary":
                    binary_formats.append(line.lower())

        return text_formats, binary_formats

    def recover(self, cancel_requested=None):
        """Main recovery process with cancel support"""
        block_size = 4096
        file_counter = 0

        try:
            with open(self.device_path, "rb") as device:
                block = device.read(block_size)
                buffer = b""
                current_format = None

                while block:
                    if cancel_requested and cancel_requested["value"]:
                        print("❌ Recovery cancelled.")
                        return

                    ext = self.detect_format(block)

                    if ext in self.text_formats:
                        if current_format != ext and buffer:
                            self.save_text_file(buffer, current_format, file_counter)
                            file_counter += 1
                            buffer = b""
                        current_format = ext
                        buffer += block
                    elif ext in self.binary_formats:
                        self.save_binary_block(block, ext, file_counter)
                        file_counter += 1
                        current_format = None
                    else:
                        if buffer:
                            self.save_text_file(buffer, current_format, file_counter)
                            file_counter += 1
                            buffer = b""
                            current_format = None

                    block = device.read(block_size)

                if buffer:
                    self.save_text_file(buffer, current_format, file_counter)

        except PermissionError:
            print("❌ Permission denied. Run as administrator.")
        except FileNotFoundError:
            print("❌ Device not found. Check SD card path.")

    def detect_format(self, block):
        text = block[:100].decode("latin-1", errors="ignore").lower()
        if "rinex" in text: return ".rinex"
        if "obs" in text: return ".obs"
        if "nav" in text: return ".nav"
        if "gsi" in text: return ".gsi"
        if text.startswith("<?xml") or "<gpx" in text: return ".xml"
        if "," in text and any(k in text for k in ["north", "east", "coord"]): return ".csv"
        if text.startswith("tp3"): return ".tp3"
        return None

    def save_text_file(self, data, ext, index):
        if not ext: ext = ".txt"
        filename = f"recovered_text_{index}{ext}"
        path = os.path.join(self.output_folder, filename)
        with open(path, "wb") as f:
            f.write(data)
        print(f"[+] Text file saved: {filename}")

    def save_binary_block(self, block, ext, index):
        if not ext: ext = ".bin"
        filename = f"recovered_bin_{index}{ext}"
        path = os.path.join(self.output_folder, filename)
        with open(path, "wb") as f:
            f.write(block)
        print(f"[+] Binary block saved: {filename}")


# --- New: Create full disk image with progress + cancel ---
def create_disk_image_with_progress(device_path, output_path, block_size=4096):
    cancel_requested = {"value": False}

    def worker():
        try:
            try:
                total_size = os.path.getsize(device_path)
            except Exception:
                total_size = None

            read_size = 0
            with open(device_path, "rb") as src, open(output_path, "wb") as dst:
                while True:
                    if cancel_requested["value"]:
                        messagebox.showinfo("Cancelled", "❌ Disk image creation cancelled.")
                        win.destroy()
                        return

                    chunk = src.read(block_size)
                    if not chunk:
                        break
                    dst.write(chunk)
                    read_size += len(chunk)

                    if total_size:
                        percent = (read_size / total_size) * 100
                        progress_var.set(percent)
                        label.config(text=f"Copied: {read_size/1_048_576:.1f} MB ({percent:.2f}%)")
                    else:
                        label.config(text=f"Copied: {read_size/1_048_576:.1f} MB")
                    progress_bar.update_idletasks()

            messagebox.showinfo("Success", f"✅ Disk image created: {output_path}")
            win.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"❌ {e}")
            win.destroy()

    win = tk.Toplevel()
    win.title("Creating disk image")
    win.geometry("400x150")
    tk.Label(win, text=f"Source: {device_path}").pack(pady=5)
    tk.Label(win, text=f"Target: {output_path}").pack(pady=5)

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(win, variable=progress_var, maximum=100)
    progress_bar.pack(fill="x", padx=10, pady=10)

    label = tk.Label(win, text="Starting...")
    label.pack()

    btn_cancel = tk.Button(win, text="Cancel", command=lambda: cancel_requested.update({"value": True}))
    btn_cancel.pack(pady=5)

    threading.Thread(target=worker, daemon=True).start()
    win.grab_set()
