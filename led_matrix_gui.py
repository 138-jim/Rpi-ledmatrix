#!/usr/bin/env python3
"""
LED Matrix GUI - Simple interface using the clean PanelController

This provides a user-friendly GUI for controlling LED matrices using the
standardized PanelController interface.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import time
import threading
import math
import colorsys
from panel_controller import PanelController, create_default_2x2_layout, create_test_frame


class LEDMatrixGUI:
    """Simple GUI for LED matrix control using PanelController"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LED Matrix Controller")
        self.root.geometry("800x600")
        
        # Panel controller
        self.controller = create_default_2x2_layout()
        
        # Animation state
        self.animation_running = False
        self.animation_thread = None
        self.current_mode = "text"
        self.current_text = "HELLO WORLD!"
        self.text_color = (255, 0, 0)
        self.scroll_offset = 0
        self.pattern_offset = 0.0
        self.brightness = 128
        
        self.setup_gui()
    
    def setup_gui(self):
        """Setup the GUI interface"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Controls
        control_frame = ttk.LabelFrame(main_frame, text="Controls", width=300)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)
        
        # Right panel - Status and config
        status_frame = ttk.LabelFrame(main_frame, text="Status & Configuration")
        status_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_controls(control_frame)
        self.setup_status(status_frame)
    
    def setup_controls(self, parent):
        """Setup control panel"""
        # Connection
        conn_frame = ttk.LabelFrame(parent, text="Connection")
        conn_frame.pack(fill=tk.X, pady=5)
        
        self.port_var = tk.StringVar(value="COM3")
        ttk.Label(conn_frame, text="Port:").pack()
        ttk.Entry(conn_frame, textvariable=self.port_var).pack(fill=tk.X, padx=5)
        
        ttk.Button(conn_frame, text="Connect", command=self.connect).pack(pady=2)
        ttk.Button(conn_frame, text="Disconnect", command=self.disconnect).pack(pady=2)
        
        # Display mode
        mode_frame = ttk.LabelFrame(parent, text="Display Mode")
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.mode_var = tk.StringVar(value="text")
        ttk.Radiobutton(mode_frame, text="Scrolling Text", variable=self.mode_var,
                       value="text", command=self.change_mode).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Test Patterns", variable=self.mode_var,
                       value="pattern", command=self.change_mode).pack(anchor=tk.W)
        
        # Text controls
        text_frame = ttk.LabelFrame(parent, text="Text Settings")
        text_frame.pack(fill=tk.X, pady=5)
        
        self.text_var = tk.StringVar(value=self.current_text)
        ttk.Label(text_frame, text="Text:").pack()
        ttk.Entry(text_frame, textvariable=self.text_var).pack(fill=tk.X, padx=5)
        ttk.Button(text_frame, text="Update", command=self.update_text).pack(pady=2)
        
        # Color controls
        color_frame = ttk.Frame(text_frame)
        color_frame.pack(fill=tk.X, pady=5)
        
        self.r_var = tk.IntVar(value=255)
        self.g_var = tk.IntVar(value=0)
        self.b_var = tk.IntVar(value=0)
        
        ttk.Label(color_frame, text="Color (RGB):").pack()
        
        rgb_frame = ttk.Frame(color_frame)
        rgb_frame.pack(fill=tk.X)
        
        ttk.Label(rgb_frame, text="R:").grid(row=0, column=0, sticky=tk.W)
        ttk.Scale(rgb_frame, from_=0, to=255, variable=self.r_var, orient=tk.HORIZONTAL,
                 command=self.update_color).grid(row=0, column=1, sticky=tk.EW)
        
        ttk.Label(rgb_frame, text="G:").grid(row=1, column=0, sticky=tk.W)
        ttk.Scale(rgb_frame, from_=0, to=255, variable=self.g_var, orient=tk.HORIZONTAL,
                 command=self.update_color).grid(row=1, column=1, sticky=tk.EW)
        
        ttk.Label(rgb_frame, text="B:").grid(row=2, column=0, sticky=tk.W)
        ttk.Scale(rgb_frame, from_=0, to=255, variable=self.b_var, orient=tk.HORIZONTAL,
                 command=self.update_color).grid(row=2, column=1, sticky=tk.EW)
        
        rgb_frame.columnconfigure(1, weight=1)
        
        # Pattern controls
        pattern_frame = ttk.LabelFrame(parent, text="Test Patterns")
        pattern_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(pattern_frame, text="Corner Test", command=lambda: self.show_pattern("corners")).pack(pady=2)
        ttk.Button(pattern_frame, text="Cross Test", command=lambda: self.show_pattern("cross")).pack(pady=2)
        ttk.Button(pattern_frame, text="Gradient Test", command=lambda: self.show_pattern("gradient")).pack(pady=2)
        ttk.Button(pattern_frame, text="Rainbow", command=lambda: self.show_pattern("rainbow")).pack(pady=2)
        
        # Brightness
        bright_frame = ttk.LabelFrame(parent, text="Brightness")
        bright_frame.pack(fill=tk.X, pady=5)
        
        self.brightness_var = tk.IntVar(value=128)
        ttk.Scale(bright_frame, from_=0, to=255, variable=self.brightness_var, orient=tk.HORIZONTAL,
                 command=self.update_brightness).pack(fill=tk.X, padx=5)
        
        # Quick actions
        action_frame = ttk.LabelFrame(parent, text="Actions")
        action_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(action_frame, text="Clear Display", command=self.clear_display).pack(pady=2)
        ttk.Button(action_frame, text="Start Animation", command=self.start_animation).pack(pady=2)
        ttk.Button(action_frame, text="Stop Animation", command=self.stop_animation).pack(pady=2)
    
    def setup_status(self, parent):
        """Setup status and configuration panel"""
        # Connection status
        status_info = ttk.LabelFrame(parent, text="Connection Status")
        status_info.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(status_info, text="Not connected")
        self.status_label.pack(padx=10, pady=5)
        
        # Panel configuration
        config_frame = ttk.LabelFrame(parent, text="Panel Configuration")
        config_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Display current config
        config_text = f"""Current Configuration:
Panels: {len(self.controller.panels)}
Total Display: {self.controller.total_width}x{self.controller.total_height}

Panel Layout:"""
        
        for i, panel in enumerate(self.controller.panels):
            config_text += f"\\n  Panel {i+1}: {panel.width}x{panel.height} at ({panel.x},{panel.y}) rot={panel.rotation}°"
        
        self.config_label = ttk.Label(config_frame, text=config_text, justify=tk.LEFT)
        self.config_label.pack(padx=10, pady=5, anchor=tk.NW)
        
        # Config buttons
        config_buttons = ttk.Frame(config_frame)
        config_buttons.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(config_buttons, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(config_buttons, text="Load Config", command=self.load_config).pack(side=tk.LEFT, padx=2)
        
        # Status log
        log_frame = ttk.LabelFrame(parent, text="Log")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def log(self, message: str):
        """Add message to log"""
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\\n")
        self.log_text.see(tk.END)
    
    def connect(self):
        """Connect to ESP32"""
        port = self.port_var.get()
        self.controller.port = port
        
        self.log(f"Connecting to {port}...")
        
        if self.controller.connect():
            self.status_label.config(text=f"Connected to {port}", foreground="green")
            self.log("✓ Connected successfully")
        else:
            self.status_label.config(text="Connection failed", foreground="red")
            self.log("✗ Connection failed")
    
    def disconnect(self):
        """Disconnect from ESP32"""
        self.stop_animation()
        self.controller.disconnect()
        self.status_label.config(text="Not connected", foreground="black")
        self.log("Disconnected")
    
    def change_mode(self):
        """Change display mode"""
        self.current_mode = self.mode_var.get()
        self.log(f"Mode changed to: {self.current_mode}")
    
    def update_text(self):
        """Update text"""
        self.current_text = self.text_var.get()
        self.scroll_offset = 32  # Reset scroll position
        self.log(f"Text updated: '{self.current_text}'")
    
    def update_color(self, *args):
        """Update text color"""
        self.text_color = (self.r_var.get(), self.g_var.get(), self.b_var.get())
    
    def update_brightness(self, *args):
        """Update brightness"""
        self.brightness = self.brightness_var.get()
        if self.controller.connected:
            self.controller.set_brightness(self.brightness)
    
    def show_pattern(self, pattern_name: str):
        """Show a test pattern"""
        self.log(f"Showing pattern: {pattern_name}")
        
        if pattern_name == "rainbow":
            # Animated rainbow - start animation mode
            self.current_mode = "rainbow"
            if not self.animation_running:
                self.start_animation()
        else:
            # Static test pattern
            frame = create_test_frame(32, 32, pattern_name)
            if self.controller.connected:
                success = self.controller.display_frame(frame)
                if success:
                    self.log(f"✓ Pattern '{pattern_name}' displayed")
                else:
                    self.log(f"✗ Failed to display pattern '{pattern_name}'")
    
    def clear_display(self):
        """Clear the display"""
        if self.controller.connected:
            success = self.controller.clear_display()
            if success:
                self.log("✓ Display cleared")
            else:
                self.log("✗ Failed to clear display")
    
    def start_animation(self):
        """Start animation thread"""
        if not self.animation_running:
            self.animation_running = True
            self.animation_thread = threading.Thread(target=self.animation_loop, daemon=True)
            self.animation_thread.start()
            self.log("Animation started")
    
    def stop_animation(self):
        """Stop animation"""
        self.animation_running = False
        if self.animation_thread:
            self.animation_thread.join(timeout=1.0)
        self.log("Animation stopped")
    
    def animation_loop(self):
        """Main animation loop"""
        frame_rate = 1/10  # 10 FPS
        last_time = time.time()
        
        while self.animation_running:
            current_time = time.time()
            
            if current_time - last_time >= frame_rate:
                try:
                    if self.current_mode == "text":
                        self.update_text_frame()
                    elif self.current_mode == "rainbow":
                        self.update_rainbow_frame()
                    
                    last_time = current_time
                except Exception as e:
                    self.log(f"Animation error: {e}")
            
            time.sleep(0.01)
    
    def update_text_frame(self):
        """Update scrolling text frame"""
        if not self.controller.connected:
            return
        
        # Create frame with text
        frame = self.create_text_frame(self.current_text, self.text_color, self.scroll_offset)
        
        # Send to display
        self.controller.display_frame(frame)
        
        # Update scroll position
        self.scroll_offset -= 1
        text_width = len(self.current_text) * 6  # Approximate text width
        if self.scroll_offset < -text_width:
            self.scroll_offset = 32
    
    def update_rainbow_frame(self):
        """Update rainbow pattern frame"""
        if not self.controller.connected:
            return
        
        frame = self.create_rainbow_frame(self.pattern_offset)
        self.controller.display_frame(frame)
        
        self.pattern_offset += 0.1
    
    def create_text_frame(self, text: str, color: tuple, x_offset: int) -> np.ndarray:
        """Create a frame with text (simplified bitmap font)"""
        frame = np.zeros((32, 32, 3), dtype=np.uint8)
        
        # Simple 5x7 character rendering (just basic shapes for demo)
        char_width = 6
        y_pos = 12  # Center vertically
        
        for i, char in enumerate(text):
            x_pos = x_offset + i * char_width
            
            # Draw simple character shapes
            if 0 <= x_pos < 32 and 0 <= x_pos + 4 < 32:
                if char == 'H':
                    for y in range(7):
                        if y_pos + y < 32:
                            frame[y_pos + y, x_pos] = color  # Left line
                            frame[y_pos + y, x_pos + 4] = color  # Right line
                            if y == 3:  # Middle line
                                for x in range(5):
                                    if x_pos + x < 32:
                                        frame[y_pos + y, x_pos + x] = color
                elif char == 'E':
                    for y in range(7):
                        if y_pos + y < 32:
                            frame[y_pos + y, x_pos] = color  # Left line
                            if y in [0, 3, 6]:  # Horizontal lines
                                for x in range(4):
                                    if x_pos + x < 32:
                                        frame[y_pos + y, x_pos + x] = color
                elif char == 'L':
                    for y in range(7):
                        if y_pos + y < 32:
                            frame[y_pos + y, x_pos] = color  # Left line
                            if y == 6:  # Bottom line
                                for x in range(4):
                                    if x_pos + x < 32:
                                        frame[y_pos + y, x_pos + x] = color
                elif char == 'O':
                    for y in range(7):
                        if y_pos + y < 32:
                            if y in [0, 6]:  # Top and bottom
                                for x in range(1, 4):
                                    if x_pos + x < 32:
                                        frame[y_pos + y, x_pos + x] = color
                            else:  # Sides
                                frame[y_pos + y, x_pos] = color
                                frame[y_pos + y, x_pos + 4] = color
                else:
                    # Default: simple rectangle for unknown chars
                    for y in range(5):
                        for x in range(3):
                            if (y_pos + y + 1 < 32 and x_pos + x + 1 < 32 and
                                x_pos + x + 1 >= 0):
                                frame[y_pos + y + 1, x_pos + x + 1] = color
        
        return frame
    
    def create_rainbow_frame(self, offset: float) -> np.ndarray:
        """Create rainbow pattern frame"""
        frame = np.zeros((32, 32, 3), dtype=np.uint8)
        
        for y in range(32):
            for x in range(32):
                hue = (x + y + offset) / (32 + 32)
                r, g, b = colorsys.hsv_to_rgb(hue % 1.0, 1.0, 1.0)
                frame[y, x] = [int(r * 255), int(g * 255), int(b * 255)]
        
        return frame
    
    def save_config(self):
        """Save panel configuration"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                self.controller.save_config(filename)
                self.log(f"✓ Configuration saved: {filename}")
            except Exception as e:
                self.log(f"✗ Save failed: {e}")
                messagebox.showerror("Error", f"Failed to save: {e}")
    
    def load_config(self):
        """Load panel configuration"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                self.controller.load_config(filename)
                self.log(f"✓ Configuration loaded: {filename}")
                # Update display
                self.update_config_display()
            except Exception as e:
                self.log(f"✗ Load failed: {e}")
                messagebox.showerror("Error", f"Failed to load: {e}")
    
    def update_config_display(self):
        """Update the configuration display"""
        config_text = f"""Current Configuration:
Panels: {len(self.controller.panels)}
Total Display: {self.controller.total_width}x{self.controller.total_height}

Panel Layout:"""
        
        for i, panel in enumerate(self.controller.panels):
            config_text += f"\\n  Panel {i+1}: {panel.width}x{panel.height} at ({panel.x},{panel.y}) rot={panel.rotation}°"
        
        self.config_label.config(text=config_text)
    
    def run(self):
        """Run the GUI application"""
        self.log("LED Matrix Controller started")
        self.log(f"Default configuration: {len(self.controller.panels)} panels, {self.controller.total_width}x{self.controller.total_height} display")
        
        try:
            self.root.mainloop()
        finally:
            self.stop_animation()
            if self.controller.connected:
                self.controller.disconnect()


def main():
    """Main entry point"""
    app = LEDMatrixGUI()
    app.run()


if __name__ == "__main__":
    main()