# SD_card_recovery_files# Geodesy SD Card Recovery

A Python GUI tool for recovering geodesy-related files from SD cards and raw devices with a simple graphical interface.

## ✨ Features
- Select physical device (disk, SD card) from a list.
- Create full disk image (`.img`) with progress bar and cancel option.
- Deep recovery of known geodesy file formats from raw devices.
- Supports both text and binary formats:
  - `.obs`, `.nav`, `.gpx`, `.kml`, `.csv`, `.txt`, `.xml`, `.json`
  - `.raw`, `.dat`, `.bin` and more.
- Extensible with plugins (see `plugins/` folder).

## 🚀 Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/SD_card_recovery_files.git
   cd SD_card_recovery_files
