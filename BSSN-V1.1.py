import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import threading
import time
import requests
from PIL import Image, ImageTk
import pytesseract
from PIL import ImageGrab
import re
from datetime import datetime
import keyboard

# Point to your Tesseract installation if it's not in your PATH
# Example for Windows:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class BeeSwarmNotifier:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bee Swarm Smart Notifier v1.1")
        self.root.geometry("550x400") # Slightly increased size
        self.root.resizable(False, False)
        self.root.overrideredirect(True)
        
        # Store window position for dragging
        self._x = 0
        self._y = 0
        
        # Configuration file path
        self.config_file = "bee_swarm_config.json"
        
        # Default configuration
        self.config = {
            "event_webhook": "",
            "item_webhook": "",
            "screenshot_enabled": True,
            "theme": "light",
            "always_on_top": False,
            "start_hotkey": "f7",  # Default start hotkey
            "stop_hotkey": "f8",   # Default stop hotkey
            "scan_interval": "3",
            "screenshot_webhook": "", # New screenshot webhook
            "full_screenshot_interval": "3", # New full screenshot interval
            "start_full_screenshot_hotkey": "f9", # New start full screenshot hotkey
            "stop_full_screenshot_hotkey": "f10", # New stop full screenshot hotkey
            "events": {
                "puffshroom": False,
                "sprout": False,
                "meteor_shower": False,
                "honey_storm": False,
                "windy_bee": False,
                "vicious_bee": False,
                "mondo_chicken": False,
                "stick_bug": False
            },
            "items": {}
        }
        
        # Event definitions
        self.event_definitions = {
            "puffshroom": "Puffshroom spawned (May be broken)",
            "sprout": "Sprout / Party Sprout",
            "meteor_shower": "Meteor Shower",
            "honey_storm": "Honey Storm",
            "windy_bee": "Windy Bee",
            "vicious_bee": "Vicious Bee",
            "mondo_chicken": "Mondo Chicken",
            "stick_bug": "Stick Bug Challenge"
        }
        
        # Common Bee Swarm items
        self.bee_swarm_items = sorted(list(set([
            "Aged Gingerbread Bear", "Atomic Treat", "Bitterberry", "Blackberry", "Blue Extract", "Blueberry",
            "Box-O-Frogs", "Caustic Wax", "Cloud Vial", "Coconut", "Comforting Vial", "Dandelion", "Debug Wax",
            "Diamond Egg", "Egg", "Enzymes", "Festive Bean", "Field Dice", "Gingerbread Bear", "Glitter",
            "Glue", "Gold Egg", "Gumdrops", "Hard Wax", "Honey", "Honey Chest", "Honey Pouch", "Honey Sack",
            "Honey Vault", "Honeysuckle", "Invigorating Vial", "Jelly Beans", "Loaded Dice", "Magic Bean",
            "Marshmallow Bee", "Micro-Converter", "Moon Charm", "Motivating Vial", "Mythic Egg", "Nectar Shower Vial",
            "Nectar Vial", "Neonberry", "Night Bell", "Oil", "Pineapple", "Purple Potion", "Raspberry",
            "Red Extract", "Refreshing Vial", "Royal Jelly", "Satisfying Vial", "Silver Egg", "Smooth Dice",
            "Snowflake", "Soft Wax", "Spirit Petal", "Star Egg", "Star Jelly", "Star Treat", "Stinger",
            "Strawberry", "Sunflower Seed", "Super Smoothie", "Ticket", "Treat", "Tropical Drink", "Turpentine"
        ])))
        
        # Detection state
        self.detection_running = False
        self.detection_thread = None
        self.start_hotkey_bound = False
        self.stop_hotkey_bound = False
        self.last_notification_time = {} # Stores last time a notification was sent: {("event"/"item", name): timestamp}
        self.COOLDOWN_TIME = 10 # seconds for double detection warning
        
        # Full screenshot state
        self.full_screenshot_running = False
        self.full_screenshot_thread = None
        self.start_full_screenshot_hotkey_bound = False
        self.stop_full_screenshot_hotkey_bound = False
        
        # Load configuration
        self.load_config()
        
        # Initialize GUI
        self.setup_gui()
        
        # Apply theme
        self.apply_theme()

        # Define a tiny font style for the close button
        style = ttk.Style()
        style.configure('Tiny.TButton', font=('Arial', 6))
        
        # Define a larger font style for event checkboxes
        style.configure('EventCheckbutton.TCheckbutton', font=('Arial', 12))

        # Apply always on top setting on startup
        self.apply_always_on_top()

        # Bind hotkeys
        self.bind_hotkeys()

    def setup_gui(self):
        # Create control buttons and the top bar container (which will be at the bottom)
        self.create_control_buttons()

        # Now pack the top_bar_container to the bottom of the root window
        self.top_bar_container.pack(side="bottom", fill="x", padx=0, pady=0) # Pack to bottom

        # Bind events for custom window dragging to the NOTEBOOK (tab bar)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.bind("<ButtonPress-1>", self._on_button_press)
        self.notebook.bind("<B1-Motion>", self._on_mouse_drag)
        self.notebook.bind("<ButtonRelease-1>", self._on_button_release)
        self.notebook.pack(side="top", fill="both", expand=True) # Pack to top and expand
        
        # Add a close button to the top-right of the window (within the tab bar visual area)
        self.close_button = ttk.Button(self.root, text="X", command=self.on_closing, width=2, style='Tiny.TButton') # Apply Tiny.TButton style
        # Position it relative to the top-right corner of the window
        self.close_button.place(relx=1.0, rely=0, anchor="ne", x=-0, y=0) # Adjusted position and padding
        
        # Create tabs
        self.create_events_tab()
        self.create_items_tab()
        self.create_screenshot_tab()
        self.create_settings_tab()
        self.create_credits_tab()
    
    def create_events_tab(self):
        self.events_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.events_frame, text="🎯 Events")
        
        # Webhook URL input
        webhook_frame = ttk.LabelFrame(self.events_frame, text="Event Webhook Configuration")
        webhook_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(webhook_frame, text="Event Webhook URL:").pack(anchor="w", padx=5, pady=2)
        self.event_webhook_var = tk.StringVar(value=self.config.get("event_webhook", ""))
        self.event_webhook_entry = ttk.Entry(webhook_frame, textvariable=self.event_webhook_var, width=80, show='*')
        self.event_webhook_entry.pack(fill="x", padx=5, pady=2)
        
        test_button = ttk.Button(webhook_frame, text="Send Test Event", command=self.test_event_webhook)
        test_button.pack(anchor="w", padx=5, pady=2)
        
        # Events list
        events_list_frame = ttk.LabelFrame(self.events_frame, text="Detectable Events")
        events_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create scrollable frame for events
        canvas = tk.Canvas(events_list_frame)
        scrollbar = ttk.Scrollbar(events_list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Dynamically size scrollable_frame to canvas width
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(canvas.winfo_children()[0], width=e.width))
        
        # Event checkboxes
        self.event_vars = {}
        row_idx = 0
        col_idx = 0
        for event_key, event_name in self.event_definitions.items():
            var = tk.BooleanVar(value=self.config["events"].get(event_key, False))
            self.event_vars[event_key] = var
            cb = ttk.Checkbutton(scrollable_frame, text=event_name, variable=var, command=self.save_config, style='EventCheckbutton.TCheckbutton')
            cb.grid(row=row_idx, column=col_idx, sticky="ew", padx=15, pady=10)
            
            col_idx += 1
            if col_idx >= 2: # Two columns per row
                col_idx = 0
                row_idx += 1

        # Configure column weights to make them expand
        scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(1, weight=1)
        
        # Configure row weights (optional, but good for vertical expansion if needed)
        for i in range(row_idx + 1): # Ensure all rows expand if space is available
            scrollable_frame.grid_rowconfigure(i, weight=1)
        
        canvas.pack(fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_items_tab(self):
        self.items_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.items_frame, text="💰 Item Drops")
        
        # Webhook URL input
        webhook_frame = ttk.LabelFrame(self.items_frame, text="Item Webhook Configuration")
        webhook_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(webhook_frame, text="Item Webhook URL:").pack(anchor="w", padx=5, pady=2)
        self.item_webhook_var = tk.StringVar(value=self.config.get("item_webhook", ""))
        self.item_webhook_entry = ttk.Entry(webhook_frame, textvariable=self.item_webhook_var, width=80, show='*')
        self.item_webhook_entry.pack(fill="x", padx=5, pady=2)
        
        test_button = ttk.Button(webhook_frame, text="Send Test Drop", command=self.test_item_webhook)
        test_button.pack(anchor="w", padx=5, pady=2)
        
        # Search frame
        search_frame = ttk.Frame(self.items_frame)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(search_frame, text="Search Items:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_items)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=5)
        
        # Items list
        items_list_frame = ttk.LabelFrame(self.items_frame, text="Item Tracking Settings")
        items_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview for items
        columns = ("Item", "Mode")
        self.items_tree = ttk.Treeview(items_list_frame, columns=columns, show="headings", height=15)
        
        self.items_tree.heading("Item", text="Item Name")
        self.items_tree.heading("Mode", text="Tracking Mode")
        
        self.items_tree.column("Item", width=200)
        self.items_tree.column("Mode", width=150)
        
        # Scrollbar for treeview
        items_scrollbar = ttk.Scrollbar(items_list_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=items_scrollbar.set)
        
        self.items_tree.pack(side="left", fill="both", expand=True)
        items_scrollbar.pack(side="right", fill="y")
        
        # Bind double-click to change mode
        self.items_tree.bind("<Double-1>", self.toggle_item_mode)
        
        # Initialize items in tree
        self.populate_items_tree()
        
        # Instructions
        instructions = ttk.Label(self.items_frame, text="Double-click an item to cycle through: Off → Silent → Notify → Off")
        instructions.pack(pady=5)
    
    def create_screenshot_tab(self):
        self.screenshot_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.screenshot_frame, text="📺 Live Feed")
        
        # Create scrollable frame for settings
        canvas = tk.Canvas(self.screenshot_frame)
        scrollbar = ttk.Scrollbar(self.screenshot_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Dynamically size scrollable_frame to canvas width
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(canvas.winfo_children()[0], width=e.width))
        
        # Screenshot setting
        self.screenshot_var = tk.BooleanVar(value=self.config.get("screenshot_enabled", True))
        screenshot_cb = ttk.Checkbutton(
            scrollable_frame, # Parent changed to scrollable_frame
            text="Attach Screenshot to Alerts", 
            variable=self.screenshot_var,
            command=self.save_config
        )
        screenshot_cb.pack(anchor="w", padx=10, pady=5)
        
        # Screenshot webhook input
        webhook_frame = ttk.LabelFrame(scrollable_frame, text="Screenshot Webhook Configuration") # Parent changed
        webhook_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(webhook_frame, text="Screenshot Webhook URL:").pack(anchor="w", padx=5, pady=2)
        self.screenshot_webhook_var = tk.StringVar(value=self.config.get("screenshot_webhook", ""))
        self.screenshot_webhook_entry = ttk.Entry(webhook_frame, textvariable=self.screenshot_webhook_var, width=80, show='*')
        self.screenshot_webhook_entry.pack(fill="x", padx=5, pady=2)
        
        test_button = ttk.Button(webhook_frame, text="Send Test Screenshot", command=self.test_screenshot_webhook)
        test_button.pack(anchor="w", padx=5, pady=2)
        
        # Screenshot interval input
        interval_frame = ttk.LabelFrame(scrollable_frame, text="Screenshot Interval Configuration") # Parent changed
        interval_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(interval_frame, text="Full Screenshot Interval (seconds):").pack(anchor="w", padx=5, pady=2)
        self.full_screenshot_interval_var = tk.StringVar(value=self.config.get("full_screenshot_interval", "3"))
        full_screenshot_interval_spin = ttk.Spinbox(interval_frame, from_=0.1, to=30, textvariable=self.full_screenshot_interval_var, width=10, increment=0.1)
        full_screenshot_interval_spin.pack(side="left", padx=10, pady=2)
        self.full_screenshot_interval_var.trace("w", self.save_config)

        # Screenshot hotkey settings
        hotkey_frame = ttk.LabelFrame(scrollable_frame, text="Screenshot Hotkey Settings") # Parent changed
        hotkey_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(hotkey_frame, text="Start Full Screenshot Hotkey:").pack(anchor="w", padx=5, pady=2)
        self.start_full_screenshot_hotkey_var = tk.StringVar(value=self.config.get("start_full_screenshot_hotkey", "f9"))
        start_full_screenshot_hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.start_full_screenshot_hotkey_var, width=15)
        start_full_screenshot_hotkey_entry.pack(anchor="w", padx=10, pady=2)
        self.start_full_screenshot_hotkey_var.trace("w", self.save_config)

        ttk.Label(hotkey_frame, text="Stop Full Screenshot Hotkey:").pack(anchor="w", padx=5, pady=2)
        self.stop_full_screenshot_hotkey_var = tk.StringVar(value=self.config.get("stop_full_screenshot_hotkey", "f10"))
        stop_full_screenshot_hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.stop_full_screenshot_hotkey_var, width=15)
        stop_full_screenshot_hotkey_entry.pack(anchor="w", padx=10, pady=2)
        self.stop_full_screenshot_hotkey_var.trace("w", self.save_config)
        
        # Status display
        status_frame = ttk.LabelFrame(scrollable_frame, text="Status") # Parent changed
        status_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.screenshot_status_text = scrolledtext.ScrolledText(status_frame, height=10, state="disabled")
        self.screenshot_status_text.pack(fill="both", expand=True, padx=5, pady=5)

        canvas.pack(side="left", fill="both", expand=True) # Ensure canvas expands correctly
        scrollbar.pack(side="right", fill="y")
    
    def create_settings_tab(self):
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="⚙️ Settings")
        
        # Create scrollable frame for settings
        canvas = tk.Canvas(self.settings_frame)
        scrollbar = ttk.Scrollbar(self.settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        settings_container = ttk.LabelFrame(scrollable_frame, text="Application Settings")
        settings_container.pack(fill="x", padx=10, pady=10)
        
        # Screenshot setting
        self.screenshot_var = tk.BooleanVar(value=self.config.get("screenshot_enabled", True))
        screenshot_cb = ttk.Checkbutton(
            settings_container, 
            text="Attach Screenshot to Alerts", 
            variable=self.screenshot_var,
            command=self.save_config
        )
        screenshot_cb.pack(anchor="w", padx=10, pady=5)
        
        # Always on top setting
        self.always_on_top_var = tk.BooleanVar(value=self.config.get("always_on_top", False))
        always_on_top_cb = ttk.Checkbutton(
            settings_container,
            text="Always on Top",
            variable=self.always_on_top_var,
            command=self.on_always_on_top_change
        )
        always_on_top_cb.pack(anchor="w", padx=10, pady=5)
        
        # Theme setting
        theme_frame = ttk.Frame(settings_container)
        theme_frame.pack(anchor="w", padx=10, pady=5)
        
        ttk.Label(theme_frame, text="GUI Theme:").pack(side="left", padx=5)
        self.theme_var = tk.StringVar(value=self.config.get("theme", "light"))
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, values=["light", "dark"], state="readonly")
        theme_combo.pack(side="left", padx=5)
        theme_combo.bind("<<ComboboxSelected>>", self.on_theme_change)
        
        # Detection settings
        detection_frame = ttk.LabelFrame(scrollable_frame, text="Detection Settings")
        detection_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(detection_frame, text="Scan Interval (seconds):").pack(anchor="w", padx=10, pady=2)
        self.scan_interval_var = tk.StringVar(value=self.config.get("scan_interval", "3"))
        scan_interval_spin = ttk.Spinbox(detection_frame, from_=0.1, to=30, textvariable=self.scan_interval_var, width=10, increment=0.1)
        scan_interval_spin.pack(side="left", padx=10, pady=2)
        self.scan_interval_var.trace("w", self.save_config)

        # Warning for scan interval
        ttk.Label(detection_frame, text="Higher interval = higher chance of missing detections, Lower interval = higher chance of double detections.", wraplength=250, font=("Arial", 8)).pack(side="left", padx=5, pady=2)

        # Hotkey settings
        hotkey_frame = ttk.LabelFrame(scrollable_frame, text="Hotkey Settings")
        hotkey_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(hotkey_frame, text="Start Detection Hotkey:").pack(anchor="w", padx=10, pady=2)
        self.start_hotkey_var = tk.StringVar(value=self.config.get("start_hotkey", "f7"))
        start_hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.start_hotkey_var, width=15)
        start_hotkey_entry.pack(anchor="w", padx=10, pady=2)
        self.start_hotkey_var.trace("w", self.save_config) # Save config on change

        ttk.Label(hotkey_frame, text="Stop Detection Hotkey:").pack(anchor="w", padx=10, pady=2)
        self.stop_hotkey_var = tk.StringVar(value=self.config.get("stop_hotkey", "f8"))
        stop_hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.stop_hotkey_var, width=15)
        stop_hotkey_entry.pack(anchor="w", padx=10, pady=2)
        self.stop_hotkey_var.trace("w", self.save_config) # Save config on change
        
        # Status display
        status_frame = ttk.LabelFrame(scrollable_frame, text="Status")
        status_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=10, state="disabled")
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_credits_tab(self):
        self.credits_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.credits_frame, text="📄 Credits")
        
        credits_container = ttk.Frame(self.credits_frame)
        credits_container.pack(expand=True)
        
        # App info
        title_label = ttk.Label(credits_container, text="Bee Swarm Smart Notifier", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        version_label = ttk.Label(credits_container, text="Version 1.1", font=("Arial", 12))
        version_label.pack(pady=5)
        
        desc_label = ttk.Label(credits_container, text="Advanced OCR-based game event detection tool", font=("Arial", 10))
        desc_label.pack(pady=5)
        
        # Developer info
        dev_frame = ttk.LabelFrame(credits_container, text="Developer")
        dev_frame.pack(fill="x", padx=20, pady=20)
        
        dev_label = ttk.Label(dev_frame, text="Created by MapleSticks", font=("Arial", 10))
        dev_label.pack(pady=5)
        
        # Features
        features_frame = ttk.LabelFrame(credits_container, text="Features")
        features_frame.pack(fill="x", padx=20, pady=10)
        
        features_text = """• Real-time OCR screen detection
• Discord webhook integration
• Customizable notification levels
• Comprehensive item tracking
• Event monitoring
• Screenshot attachments"""
        
        features_label = ttk.Label(features_frame, text=features_text, justify="left")
        features_label.pack(pady=5)
    
    def create_control_buttons(self):
        # Container for all top bar elements (buttons + close button)
        self.top_bar_container = ttk.Frame(self.root)
        self.top_bar_container.pack(fill="x", padx=0, pady=0) # No padding for container
        
        self.control_frame = ttk.Frame(self.top_bar_container) # Parent is now top_bar_container
        self.control_frame.pack(side="left", fill="x", expand=True, padx=10, pady=5) # Retain some padding for buttons
        
        # Close button is now placed at the top-right via root.place() - removed from here.
        # self.close_button = ttk.Button(self.top_bar_container, text="X", command=self.on_closing, width=4) # Smaller width
        # self.close_button.pack(side="right", padx=(20, 10), pady=5) # Big space on left, normal on right
        
        self.start_button = ttk.Button(self.control_frame, text="▶️ Start OCR", command=self.start_detection)
        self.start_button.pack(side="left", padx=2)
        
        self.stop_button = ttk.Button(self.control_frame, text="⏹️ Stop OCR", command=self.stop_detection, state="disabled")
        self.stop_button.pack(side="left", padx=2)
        
        self.start_full_screenshot_button = ttk.Button(self.control_frame, text="▶️ Start Live Feed", command=self.start_full_screenshot)
        self.start_full_screenshot_button.pack(side="left", padx=2)
        
        self.stop_full_screenshot_button = ttk.Button(self.control_frame, text="⏹️ Stop Live Feed", command=self.stop_full_screenshot, state="disabled")
        self.stop_full_screenshot_button.pack(side="left", padx=2)

        self.status_label = ttk.Label(self.control_frame, text="Status: Stopped", foreground="red")
        self.status_label.pack(side="right", padx=10)
    
    def _on_button_press(self, event):
        self._x = event.x
        self._y = event.y

    def _on_mouse_drag(self, event):
        deltax = event.x - self._x
        deltay = event.y - self._y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"={self.root.winfo_width()}x{self.root.winfo_height()}+{x}+{y}")

    def _on_button_release(self, event):
        pass # No specific action needed on release
    
    def populate_items_tree(self):
        # Clear existing items
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        
        # Add items with their current mode
        search_term = self.search_var.get().lower()
        for item in sorted(self.bee_swarm_items):
            if not search_term or search_term in item.lower():
                mode = self.config["items"].get(item, "off")
                mode_display = {"off": "🚫 Off", "silent": "📤 Silent", "notify": "🔔 Notify"}
                self.items_tree.insert("", "end", values=(item, mode_display[mode]))
    
    def filter_items(self, *args):
        self.populate_items_tree()
    
    def toggle_item_mode(self, event):
        selection = self.items_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item_name = self.items_tree.item(item_id)["values"][0]
        
        current_mode = self.config["items"].get(item_name, "off")
        mode_cycle = {"off": "silent", "silent": "notify", "notify": "off"}
        new_mode = mode_cycle[current_mode]
        
        self.config["items"][item_name] = new_mode
        self.save_config()
        self.populate_items_tree()
    
    def test_event_webhook(self):
        webhook_url = self.event_webhook_var.get().strip()
        if not webhook_url:
            messagebox.showwarning("Warning", "Please enter an event webhook URL first.")
            return
        
        try:
            payload = {
                "content": "🧪 **Test Event Notification**\nThis is a test message from Bee Swarm Smart Notifier!"
            }
            response = requests.post(webhook_url, json=payload)
            if response.status_code == 204:
                messagebox.showinfo("Success", "Test event sent successfully!")
            else:
                messagebox.showerror("Error", f"Failed to send test event. Status: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send test event: {str(e)}")
    
    def test_item_webhook(self):
        webhook_url = self.item_webhook_var.get().strip()
        if not webhook_url:
            messagebox.showwarning("Warning", "Please enter an item webhook URL first.")
            return
        
        try:
            payload = {
                "content": "🧪 **Test Item Drop**\n🎁 You received a Test Item!"
            }
            response = requests.post(webhook_url, json=payload)
            if response.status_code == 204:
                messagebox.showinfo("Success", "Test item drop sent successfully!")
            else:
                messagebox.showerror("Error", f"Failed to send test item. Status: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send test item: {str(e)}")
    
    def test_screenshot_webhook(self):
        webhook_url = self.screenshot_webhook_var.get().strip()
        if not webhook_url:
            messagebox.showwarning("Warning", "Please enter a screenshot webhook URL first.")
            return
        
        try:
            # Capture a test screenshot
            test_screenshot = ImageGrab.grab()
            temp_file = "test_screenshot.png"
            test_screenshot.save(temp_file)

            with open(temp_file, 'rb') as f:
                files = {'file': (temp_file, f, 'image/png')}
                payload = {"content": "🧪 **Test Full Screenshot**\nThis is a test full screenshot from Bee Swarm Smart Notifier!"}
                response = requests.post(webhook_url, data=payload, files=files)

            os.remove(temp_file) # Clean up temp file
            
            if response.status_code in [200, 204]: # Discord returns 204 No Content for successful webhook posts, but 200 with content also means success
                messagebox.showinfo("Success", "Test screenshot sent successfully!")
            else:
                messagebox.showerror("Error", f"Failed to send test screenshot. Status: {response.status_code} - {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send test screenshot: {str(e)}")
    
    def on_theme_change(self, event=None):
        self.save_config()
        self.apply_theme()
    
    def on_always_on_top_change(self):
        self.save_config()
        self.apply_always_on_top()
    
    def apply_theme(self):
        theme = self.config.get("theme", "light")
        if theme == "dark":
            self.root.configure(bg="#2b2b2b")
            style = ttk.Style()
            style.theme_use("alt")  # or "clam" for better dark theme support
        else:
            self.root.configure(bg="SystemButtonFace")
            style = ttk.Style()
            style.theme_use("default")

    def apply_always_on_top(self):
        self.root.attributes("-topmost", self.always_on_top_var.get())
    
    def start_detection(self):
        if self.detection_running:
            return
        
        # Validate configuration
        if not self.event_webhook_var.get().strip() and not self.item_webhook_var.get().strip():
            messagebox.showwarning("Warning", "Please configure at least one webhook URL before starting detection.")
            return
        
        self.detection_running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text="Status: Running", foreground="green")
        
        # Start detection thread
        self.detection_thread = threading.Thread(target=self.detection_loop, daemon=True)
        self.detection_thread.start()
        
        self.log_status("Detection started successfully!")
    
    def stop_detection(self):
        self.detection_running = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_label.configure(text="Status: Stopped", foreground="red")
        self.log_status("Detection stopped.")
    
    def detection_loop(self):
        try:
            scan_interval = float(self.scan_interval_var.get())
        except ValueError:
            scan_interval = 3.0
        
        while self.detection_running:
            try:
                # Capture screen region (bottom-right corner)
                screenshot = ImageGrab.grab(bbox=(1300, 675, 1820, 1080))  # Matched AHK perfect coordinates
                
                # Perform OCR
                try:
                    text = pytesseract.image_to_string(screenshot)
                    self.process_detected_text(text, screenshot)
                except Exception as e:
                    self.log_status(f"OCR Error: {str(e)}")
                
                time.sleep(scan_interval)
                
            except Exception as e:
                self.log_status(f"Detection Error: {str(e)}")
                time.sleep(scan_interval)
    
    def process_detected_text(self, text, screenshot):
        text_lower = text.lower()
        self.log_status(f"Processing text: {text_lower}") # Added for debugging
        
        # Check for events
        event_patterns = {
            "puffshroom": r"puffshroom.*spawn",
            "sprout": r"a .* sprout has appeared.*|.* has planted .* sprout.*",
            "meteor_shower": r"meteor.*shower",
            "honey_storm": r"a honeystorm has been summoned!|.* has summoned a honeystorm!",
            "windy_bee": r"found a windy bee",
            "vicious_bee": r"vicious bee is attacking",
            "mondo_chicken": r"mondo chick has spawned.*",
            "stick_bug": r"started the stick bug challenge.*"
        }
        
        for event_key, pattern in event_patterns.items():
            if self.config["events"].get(event_key, False) and re.search(pattern, text_lower):
                self.send_event_notification(event_key, text, screenshot)
        
        # Check for item drops
        for item_name, mode in self.config["items"].items():
            if mode != "off" and item_name.lower() in text_lower:
                self.log_status(f"Found '{item_name}' in text. Sending item notification.")
                self.send_item_notification(item_name, mode, text, screenshot)
    
    def send_event_notification(self, event_key, detected_text, screenshot):
        webhook_url = self.event_webhook_var.get().strip()
        if not webhook_url:
            return
        
        event_name = self.event_definitions[event_key]
        timestamp = datetime.now().strftime("%H:%M:%S")
        notification_id = ("event", event_key)
        
        content = f"🎯 **EVENT DETECTED** ({timestamp})\n📍 {event_name}"
        
        # Check for possible double detection
        current_time = time.time()
        if notification_id in self.last_notification_time and \
           (current_time - self.last_notification_time[notification_id]) < self.COOLDOWN_TIME:
            self.log_status(f"Suppressed duplicate event notification for {event_name}")
            return # Do not send if within cooldown

        self.last_notification_time[notification_id] = current_time

        payload = {"content": content}
        
        try:
            if self.screenshot_var.get():
                # Save screenshot to a temporary file and attach it
                temp_file = "event_screenshot.png"
                screenshot.save(temp_file)
                
                with open(temp_file, 'rb') as f:
                    files = {'file': (temp_file, f, 'image/png')}
                    response = requests.post(webhook_url, data=payload, files=files)
                os.remove(temp_file) # Clean up temp file
            else:
                response = requests.post(webhook_url, json=payload) # Send without screenshot if disabled
            
            if response.status_code in [200, 204]:
                self.log_status(f"Event notification sent: {event_name}. Status: {response.status_code}")
            else:
                self.log_status(f"Failed to send event notification: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_status(f"Error sending event notification: {str(e)}")
    
    def send_item_notification(self, item_name, mode, detected_text, screenshot):
        webhook_url = self.item_webhook_var.get().strip()
        if not webhook_url:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        notification_id = ("item", item_name)

        if mode == "notify":
            content = f"@everyone\n🎁 **RARE DROP: You received a {item_name}!** ({timestamp})"
        else:  # silent
            content = f"🎁 You received a {item_name}! ({timestamp})"
        
        payload = {"content": content}
        
        try:
            if self.screenshot_var.get():
                # Save screenshot to a temporary file and attach it
                temp_file = "item_screenshot.png"
                screenshot.save(temp_file)
                
                with open(temp_file, 'rb') as f:
                    files = {'file': (temp_file, f, 'image/png')}
                    response = requests.post(webhook_url, data=payload, files=files)
                os.remove(temp_file) # Clean up temp file
            else:
                response = requests.post(webhook_url, json=payload) # Send without screenshot if disabled
            
            if response.status_code in [200, 204]:
                self.log_status(f"Item notification sent: {item_name} ({mode}). Status: {response.status_code}")
            else:
                self.log_status(f"Failed to send item notification: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_status(f"Error sending item notification: {str(e)}")
    
    def log_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # Update status text widget in thread-safe manner
        self.root.after(0, self._update_status_text, log_message)
    
    def _update_status_text(self, message):
        self.status_text.configure(state="normal")
        self.status_text.insert("end", message)
        self.status_text.see("end")
        self.status_text.configure(state="disabled")
    
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def save_config(self):
        try:
            # Update config with current values
            self.config["event_webhook"] = self.event_webhook_var.get() if hasattr(self, 'event_webhook_var') else ""
            self.config["item_webhook"] = self.item_webhook_var.get() if hasattr(self, 'item_webhook_var') else ""
            self.config["screenshot_enabled"] = self.screenshot_var.get() if hasattr(self, 'screenshot_var') else True
            self.config["theme"] = self.theme_var.get() if hasattr(self, 'theme_var') else "light"
            self.config["always_on_top"] = self.always_on_top_var.get() if hasattr(self, 'always_on_top_var') else False
            self.config["start_hotkey"] = self.start_hotkey_var.get() if hasattr(self, 'start_hotkey_var') else "f7"
            self.config["stop_hotkey"] = self.stop_hotkey_var.get() if hasattr(self, 'stop_hotkey_var') else "f8"
            self.config["scan_interval"] = self.scan_interval_var.get() if hasattr(self, 'scan_interval_var') else "3"
            
            # New screenshot settings
            self.config["screenshot_webhook"] = self.screenshot_webhook_var.get() if hasattr(self, 'screenshot_webhook_var') else ""
            self.config["full_screenshot_interval"] = self.full_screenshot_interval_var.get() if hasattr(self, 'full_screenshot_interval_var') else "3"
            self.config["start_full_screenshot_hotkey"] = self.start_full_screenshot_hotkey_var.get() if hasattr(self, 'start_full_screenshot_hotkey_var') else "f9"
            self.config["stop_full_screenshot_hotkey"] = self.stop_full_screenshot_hotkey_var.get() if hasattr(self, 'stop_full_screenshot_hotkey_var') else "f10"
            
            # Update event settings
            if hasattr(self, 'event_vars'):
                for event_key, var in self.event_vars.items():
                    self.config["events"][event_key] = var.get()
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def run(self):
        # Save config on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        if self.detection_running:
            self.stop_detection()
        if self.full_screenshot_running:
            self.stop_full_screenshot()
        self.unbind_hotkeys() # Unbind hotkeys on closing
        self.save_config()
        self.root.destroy()

    def bind_hotkeys(self):
        self.unbind_hotkeys() # Unbind existing hotkeys first
        
        start_key = self.config.get("start_hotkey", "f7")
        stop_key = self.config.get("stop_hotkey", "f8")
        start_full_screenshot_key = self.config.get("start_full_screenshot_hotkey", "f9")
        stop_full_screenshot_key = self.config.get("stop_full_screenshot_hotkey", "f10")

        try:
            if start_key and not self.start_hotkey_bound:
                keyboard.add_hotkey(start_key, self.start_detection)
                self.start_hotkey_bound = True
                self.log_status(f"Bound start hotkey: {start_key}")
        except Exception as e:
            self.log_status(f"Error binding start hotkey '{start_key}': {e}")

        try:
            if stop_key and not self.stop_hotkey_bound:
                keyboard.add_hotkey(stop_key, self.stop_detection)
                self.stop_hotkey_bound = True
                self.log_status(f"Bound stop hotkey: {stop_key}")
        except Exception as e:
            self.log_status(f"Error binding stop hotkey '{stop_key}': {e}")

        try:
            if start_full_screenshot_key and not self.start_full_screenshot_hotkey_bound:
                keyboard.add_hotkey(start_full_screenshot_key, self.start_full_screenshot)
                self.start_full_screenshot_hotkey_bound = True
                self.log_status(f"Bound start full screenshot hotkey: {start_full_screenshot_key}")
        except Exception as e:
            self.log_status(f"Error binding start full screenshot hotkey '{start_full_screenshot_key}': {e}")

        try:
            if stop_full_screenshot_key and not self.stop_full_screenshot_hotkey_bound:
                keyboard.add_hotkey(stop_full_screenshot_key, self.stop_full_screenshot)
                self.stop_full_screenshot_hotkey_bound = True
                self.log_status(f"Bound stop full screenshot hotkey: {stop_full_screenshot_key}")
        except Exception as e:
            self.log_status(f"Error binding stop full screenshot hotkey '{stop_full_screenshot_key}': {e}")

    def unbind_hotkeys(self):
        if self.start_hotkey_bound:
            start_key = self.config.get("start_hotkey", "f7")
            try:
                keyboard.remove_hotkey(start_key)
                self.start_hotkey_bound = False
                self.log_status(f"Unbound start hotkey: {start_key}")
            except KeyError:
                pass # Hotkey might not have been bound
            except Exception as e:
                self.log_status(f"Error unbinding start hotkey '{start_key}': {e}")

        if self.stop_hotkey_bound:
            stop_key = self.config.get("stop_hotkey", "f8")
            try:
                keyboard.remove_hotkey(stop_key)
                self.stop_hotkey_bound = False
                self.log_status(f"Unbound stop hotkey: {stop_key}")
            except KeyError:
                pass # Hotkey might not have been bound
            except Exception as e:
                self.log_status(f"Error unbinding stop hotkey '{stop_key}': {e}")

        if self.start_full_screenshot_hotkey_bound:
            start_full_screenshot_key = self.config.get("start_full_screenshot_hotkey", "f9")
            try:
                keyboard.remove_hotkey(start_full_screenshot_key)
                self.start_full_screenshot_hotkey_bound = False
                self.log_status(f"Unbound start full screenshot hotkey: {start_full_screenshot_key}")
            except KeyError:
                pass
            except Exception as e:
                self.log_status(f"Error unbinding start full screenshot hotkey '{start_full_screenshot_key}': {e}")

        if self.stop_full_screenshot_hotkey_bound:
            stop_full_screenshot_key = self.config.get("stop_full_screenshot_hotkey", "f10")
            try:
                keyboard.remove_hotkey(stop_full_screenshot_key)
                self.stop_full_screenshot_hotkey_bound = False
                self.log_status(f"Unbound stop full screenshot hotkey: {stop_full_screenshot_key}")
            except KeyError:
                pass
            except Exception as e:
                self.log_status(f"Error unbinding stop full screenshot hotkey '{stop_full_screenshot_key}': {e}")

    def start_full_screenshot(self):
        if self.full_screenshot_running:
            return

        webhook_url = self.screenshot_webhook_var.get().strip()
        if not webhook_url:
            messagebox.showwarning("Warning", "Please configure a screenshot webhook URL before starting full screenshots.")
            return

        self.full_screenshot_running = True
        self.start_full_screenshot_button.configure(state="disabled")
        self.stop_full_screenshot_button.configure(state="normal")
        self.log_status("Full screenshot capture started.")
        self._update_screenshot_status("Running", "green")
        
        self.full_screenshot_thread = threading.Thread(target=self.full_screenshot_loop, daemon=True)
        self.full_screenshot_thread.start()

    def stop_full_screenshot(self):
        self.full_screenshot_running = False
        self.start_full_screenshot_button.configure(state="normal")
        self.stop_full_screenshot_button.configure(state="disabled")
        self.log_status("Full screenshot capture stopped.")
        self._update_screenshot_status("Stopped", "red")

    def full_screenshot_loop(self):
        try:
            interval = float(self.full_screenshot_interval_var.get())
        except ValueError:
            interval = 3.0

        while self.full_screenshot_running:
            try:
                screenshot = ImageGrab.grab()
                self.send_full_screenshot(screenshot)
                time.sleep(interval)
            except Exception as e:
                self.log_status(f"Full screenshot error: {str(e)}")
                self._update_screenshot_status(f"Error: {e}", "red")
                time.sleep(interval)

    def send_full_screenshot(self, screenshot):
        webhook_url = self.screenshot_webhook_var.get().strip()
        if not webhook_url:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_file = f"full_screenshot_{timestamp}.png"
        
        try:
            screenshot.save(temp_file)

            with open(temp_file, 'rb') as f:
                files = {'file': (temp_file, f, 'image/png')}
                payload = {"content": f"📸 **Full Screenshot** ({timestamp})"}
                response = requests.post(webhook_url, data=payload, files=files)

            if response.status_code == 204:
                self.log_status(f"Full screenshot sent at {timestamp}")
                self._update_screenshot_status("Last sent: " + timestamp, "green")
            else:
                self.log_status(f"Failed to send full screenshot: {response.status_code} - {response.text}")
                self._update_screenshot_status("Send failed: " + str(response.status_code), "red")
        except Exception as e:
            self.log_status(f"Error saving or sending full screenshot: {str(e)}")
            self._update_screenshot_status("Error sending: " + str(e), "red")
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def _update_screenshot_status(self, message, color):
        self.root.after(0, self.__update_screenshot_status_text, message, color)

    def __update_screenshot_status_text(self, message, color):
        self.screenshot_status_text.configure(state="normal")
        self.screenshot_status_text.delete(1.0, tk.END)
        self.screenshot_status_text.insert("end", message)
        self.screenshot_status_text.configure(foreground=color)
        self.screenshot_status_text.configure(state="disabled")

if __name__ == "__main__":
    # Note: This application requires the following dependencies:
    # pip install pillow pytesseract requests
    # You'll also need to install Tesseract OCR on your system
    
    try:
        app = BeeSwarmNotifier()
        app.run()
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install pillow pytesseract requests keyboard")
        print("Also install Tesseract OCR from: https://github.com/tesseract-ocr/tesseract")
    except Exception as e:
        print(f"Application error: {e}")
        input("Press Enter to exit...")
