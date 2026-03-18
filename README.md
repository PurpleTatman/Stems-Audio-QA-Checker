# Stems-Audio-QA-Checker

A simple utility to batch-check and organize audio stems before you send them off. It focuses on catching common export errors that DAWs usually miss.

<img width="742" height="823" alt="Stem_QA_Screenshot" src="https://github.com/user-attachments/assets/57421ea9-4e13-42ec-a077-1e68cc6bc481" />

### What it checks:
* **Clipping:** Anything hitting 0dBFS or above.
* **Mismatches:** Flags differences in sample rate, bit-depth, or file length across the batch.
* **Silence:** Detects dead-silent files.
* **Duplicates:** Identifies files with identical audio data and flags dual-mono files (stereo files with identical L/R info).

### What it does:
* **Analysis Mode:** Logs issues without touching your files.
* **Export Mode:** Renames files (Prefix/Suffix) and collapses dual-mono files into true mono to save space.
* **Safety:** Does not overwrite by default; it appends a numbered suffix (e.g., "_1") if a filename already exists in the output folder.

### Setup:
* **Windows:** Grab the .exe from the Releases tab.
* **Mac:** Coming soon. 
* **Source:** Requires Python with soundfile and numpy installed (pip install soundfile numpy).
