import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import numpy as np
import soundfile as sf
import hashlib
import shutil

class StemCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stem QA & Processing Tool")
        self.root.geometry("750x800")

        # Variables for UI
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        
        # Checkbox Variables (QA)
        self.do_sr_bit = tk.BooleanVar(value=True)
        self.do_clipping = tk.BooleanVar(value=True)
        self.do_lengths = tk.BooleanVar(value=True)
        self.do_silence = tk.BooleanVar(value=True)
        self.do_identical = tk.BooleanVar(value=True)
        
        # Processing Variables
        self.do_dual_mono = tk.BooleanVar(value=True)
        self.rename_type = tk.StringVar(value="Suffix")
        self.rename_text = tk.StringVar(value="_Processed")
        self.allow_overwrite = tk.BooleanVar(value=False)

        self.build_gui()

    def build_gui(self):
        # --- Directories ---
        frame_dirs = tk.LabelFrame(self.root, text="Directories", padx=10, pady=10)
        frame_dirs.pack(fill="x", padx=10, pady=5)

        tk.Button(frame_dirs, text="Select Input Folder", command=self.get_input_dir, width=20).grid(row=0, column=0, pady=2)
        tk.Label(frame_dirs, textvariable=self.input_dir).grid(row=0, column=1, sticky="w", padx=10)

        tk.Button(frame_dirs, text="Select Output Folder", command=self.get_output_dir, width=20).grid(row=1, column=0, pady=2)
        tk.Label(frame_dirs, textvariable=self.output_dir).grid(row=1, column=1, sticky="w", padx=10)

        # --- Options ---
        frame_opts = tk.LabelFrame(self.root, text="Analysis & Processing Options", padx=10, pady=10)
        frame_opts.pack(fill="x", padx=10, pady=5)

        # Left Column: Analysis
        tk.Checkbutton(frame_opts, text="Check Sample Rate & Bit Depth", variable=self.do_sr_bit).grid(row=0, column=0, sticky="w")
        tk.Checkbutton(frame_opts, text="Check for Clipping (> 0dBFS)", variable=self.do_clipping).grid(row=1, column=0, sticky="w")
        tk.Checkbutton(frame_opts, text="Check for Length Mismatches", variable=self.do_lengths).grid(row=2, column=0, sticky="w")
        tk.Checkbutton(frame_opts, text="Check for Complete Silence", variable=self.do_silence).grid(row=3, column=0, sticky="w")
        tk.Checkbutton(frame_opts, text="Check for Identical Audio Files", variable=self.do_identical).grid(row=4, column=0, sticky="w")
        
        # Right Column: Processing
        tk.Checkbutton(frame_opts, text="Collapse Dual-Mono to Mono", variable=self.do_dual_mono).grid(row=0, column=1, sticky="w", padx=20)
        
        tk.Label(frame_opts, text="Renaming Style:").grid(row=1, column=1, sticky="w", padx=20)
        rename_frame = tk.Frame(frame_opts)
        rename_frame.grid(row=2, column=1, sticky="w", padx=45)
        tk.Radiobutton(rename_frame, text="Prefix", variable=self.rename_type, value="Prefix", command=self.toggle_underscore).pack(side="left")
        tk.Radiobutton(rename_frame, text="Suffix", variable=self.rename_type, value="Suffix", command=self.toggle_underscore).pack(side="left")
        tk.Entry(rename_frame, textvariable=self.rename_text, width=12).pack(side="left", padx=5)

        tk.Checkbutton(frame_opts, text="Overwrite duplicates (Uncheck to number)", variable=self.allow_overwrite).grid(row=3, column=1, sticky="w", padx=20)

        # --- Dual Run Buttons ---
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Run Analysis Only", command=lambda: self.run_process(mode="analysis"), 
                  bg="#d1d1d1", width=25, font=("Arial", 10, "bold")).pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="Run Analysis & Export", command=lambda: self.run_process(mode="export"), 
                  bg="green", fg="white", width=25, font=("Arial", 10, "bold")).pack(side="left", padx=10)

        # --- Output Log ---
        self.log_text = scrolledtext.ScrolledText(self.root, height=22)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text.tag_config("warning", background="#ffcccc", foreground="black") 
        self.log_text.tag_config("action", background="#ffe4b5", foreground="black")  
        self.log_text.tag_config("good", background="#ccffcc", foreground="black")    

    def toggle_underscore(self):
        text = self.rename_text.get()
        if not text: return
        if self.rename_type.get() == "Prefix" and text.startswith("_") and not text.endswith("_"):
            self.rename_text.set(text[1:] + "_")
        elif self.rename_type.get() == "Suffix" and text.endswith("_") and not text.startswith("_"):
            self.rename_text.set("_" + text[:-1])

    def get_input_dir(self): self.input_dir.set(filedialog.askdirectory())
    def get_output_dir(self): self.output_dir.set(filedialog.askdirectory())

    def log(self, message):
        if "[WARNING]" in message: self.log_text.insert(tk.END, message + "\n", "warning")
        elif "[ACTION]" in message:
            if any(x in message.lower() for x in ["renamed", "auto-numbered"]):
                self.log_text.insert(tk.END, message + "\n")
            else: self.log_text.insert(tk.END, message + "\n", "action")
        elif "[GOOD]" in message: self.log_text.insert(tk.END, message + "\n", "good")
        else: self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def get_safe_filepath(self, directory, filename):
        if self.allow_overwrite.get(): return os.path.join(directory, filename), filename
        base, ext = os.path.splitext(filename)
        counter, out_path, final_name = 1, os.path.join(directory, filename), filename
        while os.path.exists(out_path):
            final_name = f"{base}_{counter}{ext}"
            out_path = os.path.join(directory, final_name)
            counter += 1
        return out_path, final_name

    def apply_rename(self, original_filename):
        text = self.rename_text.get()
        if self.rename_type.get() == "Prefix": return text + original_filename
        base, ext = os.path.splitext(original_filename)
        return base + text + ext

    def run_process(self, mode="analysis"):
        in_dir, out_dir = self.input_dir.get(), self.output_dir.get()
        if not in_dir:
            messagebox.showerror("Error", "Select an input directory.")
            return
        if mode == "export" and not out_dir:
            messagebox.showerror("Error", "Select an output directory to export.")
            return

        self.log_text.delete(1.0, tk.END)
        self.log(f"Starting {mode.upper()}...\n" + "="*50)

        valid_exts = ('.wav', '.aiff', '.aif', '.flac')
        files = [f for f in os.listdir(in_dir) if f.lower().endswith(valid_exts)]
        if not files:
            self.log("No valid audio files found.")
            return

        first_sr, first_subtype, first_frames, audio_hashes = None, None, None, {}

        for file in files:
            file_path = os.path.join(in_dir, file)
            self.log(f"Analyzing: {file}")
            has_warnings = False
            try:
                info = sf.info(file_path)
                data, sr = sf.read(file_path)
            except Exception as e:
                self.log(f"  [WARNING] Error reading file: {e}")
                continue

            if self.do_sr_bit.get():
                if first_sr is None: 
                    first_sr, first_subtype = info.samplerate, info.subtype
                    self.log(f"  Baseline: {first_sr}Hz, {first_subtype}")
                elif info.samplerate != first_sr or info.subtype != first_subtype:
                    self.log(f"  [WARNING] Format Mismatch! {info.samplerate}Hz, {info.subtype}")
                    has_warnings = True

            if self.do_lengths.get():
                if first_frames is None: first_frames = info.frames
                elif info.frames != first_frames:
                    self.log(f"  [WARNING] Length Mismatch! Diff: {abs(info.frames - first_frames) / sr:.3f}s")
                    has_warnings = True

            if self.do_clipping.get() and np.max(np.abs(data)) >= 1.0:
                self.log("  [WARNING] Clipping detected (>= 0dBFS).")
                has_warnings = True

            if self.do_silence.get() and np.max(np.abs(data)) == 0.0:
                self.log("  [WARNING] File is completely silent.")
                self.log("-" * 50)
                continue

            if self.do_identical.get():
                data_hash = hashlib.md5(data.tobytes()).hexdigest()
                if data_hash in audio_hashes:
                    self.log(f"  [WARNING] Audio content is IDENTICAL to: {audio_hashes[data_hash]}")
                    has_warnings = True
                else: audio_hashes[data_hash] = file

            if mode == "export":
                is_processed = False
                target_name = self.apply_rename(file)
                
                if self.do_dual_mono.get() and info.channels == 2 and np.array_equal(data[:, 0], data[:, 1]):
                    self.log("  [ACTION] Dual-mono detected. Collapsing...")
                    out_path, final_name = self.get_safe_filepath(out_dir, target_name)
                    if final_name != target_name: self.log(f"  [ACTION] Auto-numbered to: {final_name}")
                    sf.write(out_path, data[:, 0], sr, subtype=info.subtype)
                    is_processed = True

                if not is_processed:
                    out_path, final_name = self.get_safe_filepath(out_dir, target_name)
                    if final_name != target_name: self.log(f"  [ACTION] Auto-numbered to: {final_name}")
                    shutil.copy2(file_path, out_path)
                    self.log(f"  [ACTION] Exported and renamed to output folder.")

            if not has_warnings: self.log("  [GOOD] File passed all QA checks.")
            self.log("-" * 50)
            
        self.log("\nProcess Complete!")

if __name__ == "__main__":
    root = tk.Tk()
    app = StemCheckerApp(root)
    root.mainloop()
