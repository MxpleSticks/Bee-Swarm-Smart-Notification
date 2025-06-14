# Bee Swarm Smart Notifier

## Overview
Bee Swarm Smart Notifier is a Python-based application designed to monitor in-game events and item drops in the Roblox game *Bee Swarm Simulator*. It uses Optical Character Recognition (OCR) via Tesseract to detect specific events and items on the screen and sends real-time notifications to Discord via webhooks. The application features a customizable GUI built with Tkinter, allowing users to configure detection settings, manage notifications, and toggle themes. **This tool complies with Roblox's Terms of Service (ToS)** as it only reads screen data and does not modify or automate gameplay.

## Important Notes
- **Executable Warning**: Do not convert this script to an `.exe` file, as Windows Defender or other antivirus software may flag it as a virus, preventing downloads or execution. Run the script directly using Python for safe operation.
- **Screen Size Adjustment**: The OCR captures a specific region of the screen (bottom-right corner, coordinates: 1300, 675, 1820, 1080) defined on **line 488** in the `detection_loop` method. If you have a larger or non-standard screen resolution (e.g., 4K), you may need to manually adjust these coordinates to ensure the OCR targets the correct area where game text appears.
- **Prerequisites**: You must install Python, Visual Studio Code (VSCode), Tesseract OCR, and specific Python packages before running the application.

## Installation Instructions

### 1. Install Python
- Download and install Python 3.x from [python.org](https://www.python.org/downloads/). Ensure you check the box to **add Python to PATH** during installation.
- Verify the installation by opening a terminal (Command Prompt, PowerShell, or Terminal) and running:
  ```
  python --version
  ```
  You should see the installed Python version.

### 2. Install Visual Studio Code (VSCode)
- Download and install VSCode from [code.visualstudio.com](https://code.visualstudio.com/). This is recommended for editing and running the script.
- Install the Python extension in VSCode for better code editing and debugging support.

### 3. Install Tesseract OCR
- Download and install Tesseract OCR from [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki). Follow the installation instructions for your operating system (Windows, macOS, or Linux).
- For Windows users, ensure Tesseract is added to your system PATH or specify its path in the script (e.g., `pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'` on line 13).
- Verify Tesseract installation by running:
  ```
  tesseract --version
  ```
  in a terminal.

### 4. Install Required Python Packages
- Open a terminal in VSCode (or your preferred terminal) and install the required Python packages using `pip`. Run the following commands:
  ```
  pip install pillow
  pip install pytesseract
  pip install requests
  pip install keyboard
  ```
- Note: Tkinter is included with standard Python installations, so you typically don’t need to install it separately. To verify Tkinter is available, run:
  ```
  python -m tkinter
  ```
  A small test window should appear if Tkinter is installed correctly.

### 5. Set Up the Script
- Save the provided Python script (e.g., `bee_swarm_notifier.py`) in a folder.
- Open the script in VSCode for editing or running.
- Update the Tesseract path in the script if necessary (line 13).
- **Adjust OCR Coordinates (if needed)**: On **line 488** in the `detection_loop` method, the script uses `ImageGrab.grab(bbox=(1300, 675, 1820, 1080))` to capture the bottom-right corner of the screen. If the game text appears elsewhere (e.g., due to a larger monitor), modify these coordinates to match the area where *Bee Swarm Simulator* displays event and item text. You can test coordinates by taking a screenshot and checking pixel values with an image editor.

### 6. Run the Application
- In VSCode, open a terminal (Terminal > New Terminal) and navigate to the folder containing the script:
  ```
  cd path/to/your/script/folder
  ```
- Run the script:
  ```
  python bee_swarm_notifier.py
  ```
- The GUI will open, allowing you to configure webhooks, events, items, and settings.

## Features
- **Real-time OCR Detection**: Monitors a specific screen region for game events and item drops using Tesseract OCR.
- **Discord Webhook Integration**: Sends notifications for detected events and items to specified Discord channels.
- **Customizable Notifications**: Supports different notification modes for items (Off, Silent, Notify).
- **Event Monitoring**: Detects key in-game events like Puffshroom spawns, Meteor Showers, and more.
- **Screenshot Support**: Optionally attaches screenshots to Discord notifications.
- **Configurable GUI**: Includes tabs for managing events, items, settings, and credits, with support for light and dark themes.
- **Hotkey Support**: Start and stop detection using customizable hotkeys (default: F7 to start, F8 to stop).
- **Persistent Configuration**: Saves user settings to a JSON file for easy reuse.

## Troubleshooting
- **OCR Missing Text**: If events or items aren’t detected, verify the `bbox` coordinates on **line 488** match the game’s text display area. Adjust them based on your screen resolution.
- **Tesseract Not Found**: Ensure Tesseract is installed and its path is correctly set on line 13 or in the system PATH.
- **Module Not Found**: Verify all Python packages are installed using the `pip` commands above.
- **Permission Issues**: If the `keyboard` module requires admin privileges, run VSCode or your terminal as an administrator.
- **Antivirus Blocking**: If your antivirus flags the script, ensure you’re running it as a `.py` file and not an `.exe`. Add an exception to your antivirus if needed.

## Notes
- Always ensure compliance with Roblox’s ToS when using this tool. It is designed to be a passive monitoring tool and does not interact with the game directly.
- For further assistance, refer to the script’s credits tab or check the Tesseract and Python package documentation.

*Last updated: June 14, 2025*
