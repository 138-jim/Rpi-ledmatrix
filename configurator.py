#!/usr/bin/env python3
"""
Configuration generator for WS2812B 16x16 LED panel arrays
Helps create proper configuration files for different panel arrangements
"""

import json
from typing import List, Tuple


def generate_panel_config(grid_width: int, grid_height: int, 
                         wiring_pattern: str = "snake",
                         auto_rotate: bool = True) -> dict:
    """
    Generate panel configuration for 16x16 LED panels
    
    Args:
        grid_width: Number of panels horizontally
        grid_height: Number of panels vertically
        wiring_pattern: "sequential", "snake", or "vertical_snake"
        auto_rotate: Automatically rotate panels in alternating rows/columns
    
    Returns:
        Configuration dictionary
    """
    
    panels = []
    panel_id = 0
    
    if wiring_pattern == "snake":
        # Snake/zigzag pattern (common for daisy-chained panels)
        for gy in range(grid_height):
            if gy % 2 == 0:  # Even rows: left to right
                for gx in range(grid_width):
                    rotation = 0
                    if auto_rotate and gy % 2 == 1:
                        rotation = 180
                    panels.append({
                        "id": panel_id,
                        "rotation": rotation,
                        "position": [gx, gy]
                    })
                    panel_id += 1
            else:  # Odd rows: right to left
                for gx in range(grid_width - 1, -1, -1):
                    rotation = 0
                    if auto_rotate:
                        rotation = 180  # Panels going backwards often need rotation
                    panels.append({
                        "id": panel_id,
                        "rotation": rotation,
                        "position": [gx, gy]
                    })
                    panel_id += 1
                    
    elif wiring_pattern == "vertical_snake":
        # Vertical snake pattern
        for gx in range(grid_width):
            if gx % 2 == 0:  # Even columns: top to bottom
                for gy in range(grid_height):
                    rotation = 0
                    if auto_rotate and gx % 2 == 1:
                        rotation = 180
                    panels.append({
                        "id": panel_id,
                        "rotation": rotation,
                        "position": [gx, gy]
                    })
                    panel_id += 1
            else:  # Odd columns: bottom to top
                for gy in range(grid_height - 1, -1, -1):
                    rotation = 0
                    if auto_rotate:
                        rotation = 180
                    panels.append({
                        "id": panel_id,
                        "rotation": rotation,
                        "position": [gx, gy]
                    })
                    panel_id += 1
                    
    else:  # sequential
        # Sequential pattern: left to right, top to bottom
        for gy in range(grid_height):
            for gx in range(grid_width):
                panels.append({
                    "id": panel_id,
                    "rotation": 0,
                    "position": [gx, gy]
                })
                panel_id += 1
    
    # Create configuration
    config = {
        "grid": {
            "grid_width": grid_width,
            "grid_height": grid_height,
            "panel_width": 16,
            "panel_height": 16,
            "wiring_pattern": wiring_pattern
        },
        "brightness": 128,
        "frame_rate": 30,
        "panels": panels
    }
    
    return config


def calculate_display_specs(grid_width: int, grid_height: int) -> dict:
    """Calculate specifications for a given panel configuration"""
    
    panel_pixels = 16 * 16  # 256 pixels per panel
    total_panels = grid_width * grid_height
    total_pixels = total_panels * panel_pixels
    display_width = grid_width * 16
    display_height = grid_height * 16
    
    # Power calculations
    max_current_per_led = 0.06  # 60mA per LED at full white
    max_total_current = total_pixels * max_current_per_led
    typical_current = max_total_current * 0.3  # 30% typical usage
    
    # Data rate calculations
    bytes_per_frame = total_pixels * 3  # RGB
    max_fps_serial = 921600 / (bytes_per_frame * 10)  # With overhead
    
    # Memory calculations
    esp32_memory = bytes_per_frame / 1024  # KB
    python_memory = bytes_per_frame * 2 / 1024  # KB (double buffered)
    
    return {
        "display_resolution": f"{display_width}x{display_height}",
        "total_panels": total_panels,
        "total_pixels": total_pixels,
        "max_current_draw": f"{max_total_current:.1f}A",
        "typical_current_draw": f"{typical_current:.1f}A",
        "recommended_power_supplies": max(1, int(typical_current / 20)),  # 20A supplies
        "max_fps_serial": f"{max_fps_serial:.1f}",
        "esp32_memory_usage": f"{esp32_memory:.1f}KB",
        "python_memory_usage": f"{python_memory:.1f}KB",
        "data_per_frame": f"{bytes_per_frame / 1024:.1f}KB"
    }


def print_wiring_diagram(grid_width: int, grid_height: int, wiring_pattern: str):
    """Print ASCII art wiring diagram"""
    
    print("\nWiring Diagram:")
    print("=" * 50)
    
    if wiring_pattern == "snake":
        print("ESP32 GPIO 13")
        print("     │")
        for row in range(grid_height):
            if row % 2 == 0:
                # Left to right
                line = "     └─> "
                for col in range(grid_width):
                    panel_num = row * grid_width + col
                    line += f"[{panel_num:2d}]"
                    if col < grid_width - 1:
                        line += "──>"
                print(line)
                if row < grid_height - 1:
                    print(" " * (len(line) - 3) + "│")
                    print(" " * (len(line) - 3) + "↓")
            else:
                # Right to left
                line = "         "
                for col in range(grid_width - 1, -1, -1):
                    panel_num = row * grid_width + (grid_width - 1 - col)
                    if col == grid_width - 1:
                        line = f"         [{panel_num:2d}]"
                    else:
                        line += f"<──[{panel_num:2d}]"
                print(line)
                if row < grid_height - 1:
                    print("          │")
                    print("          ↓")
                    
    elif wiring_pattern == "sequential":
        print("ESP32 GPIO 13")
        print("     │")
        for row in range(grid_height):
            line = "     └─> " if row == 0 else "         "
            for col in range(grid_width):
                panel_num = row * grid_width + col
                line += f"[{panel_num:2d}]"
                if col < grid_width - 1:
                    line += "──>"
                elif row < grid_height - 1:
                    line += "─┐"
            print(line)
            if row < grid_height - 1:
                print(" " * (len(line) - 1) + "│")
                print(" " * (len(line) - 1) + "↓")


def main():
    print("WS2812B 16x16 LED Panel Configuration Generator")
    print("=" * 50)
    
    # Common configurations
    configs = {
        "1": ("2x2 (32x32) - Desktop Display", 2, 2),
        "2": ("2x4 (32x64) - Small Wall Display", 2, 4),
        "3": ("4x4 (64x64) - Medium Wall Display", 4, 4),
        "4": ("4x8 (64x128) - Large Wall Display", 4, 8),
        "5": ("4x16 (64x256) - Massive Installation", 4, 16),
        "6": ("8x8 (128x128) - Square Display", 8, 8),
        "7": ("Custom", None, None)
    }
    
    print("\nSelect configuration:")
    for key, (desc, _, _) in configs.items():
        print(f"{key}. {desc}")
    
    choice = input("\nEnter choice (1-7): ").strip()
    
    if choice == "7":
        grid_width = int(input("Enter grid width (panels): "))
        grid_height = int(input("Enter grid height (panels): "))
    elif choice in configs:
        _, grid_width, grid_height = configs[choice]
    else:
        print("Invalid choice")
        return
    
    print("\nSelect wiring pattern:")
    print("1. Snake (zigzag) - Most common")
    print("2. Sequential (row by row)")
    print("3. Vertical Snake")
    
    pattern_choice = input("Enter choice (1-3): ").strip()
    patterns = {"1": "snake", "2": "sequential", "3": "vertical_snake"}
    wiring_pattern = patterns.get(pattern_choice, "snake")
    
    auto_rotate = input("\nAuto-rotate panels in alternating rows? (y/n): ").lower() == 'y'
    
    # Generate configuration
    config = generate_panel_config(grid_width, grid_height, wiring_pattern, auto_rotate)
    
    # Calculate specifications
    specs = calculate_display_specs(grid_width, grid_height)
    
    # Print results
    print("\n" + "=" * 50)
    print("DISPLAY SPECIFICATIONS")
    print("=" * 50)
    for key, value in specs.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Print wiring diagram
    print_wiring_diagram(grid_width, grid_height, wiring_pattern)
    
    # Save configuration
    filename = f"panel_config_{grid_width}x{grid_height}.json"
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\nConfiguration saved to: {filename}")
    
    # Print power recommendations
    print("\n" + "=" * 50)
    print("POWER RECOMMENDATIONS")
    print("=" * 50)
    print(f"Minimum: {specs['typical_current_draw']} at 30% brightness")
    print(f"Maximum: {specs['max_current_draw']} at full white")
    print(f"Suggested: {specs['recommended_power_supplies']} x 5V 20A supplies")
    print("\nPower injection points:")
    if total_panels := grid_width * grid_height:
        if total_panels <= 4:
            print("- Single injection at start of chain")
        elif total_panels <= 16:
            print("- Inject power every 4 panels")
            print("- Use 18AWG wire for power distribution")
        else:
            print("- Inject power every 2-3 panels")
            print("- Use 14-16AWG wire for main power bus")
            print("- Consider multiple ESP32s for sections")
    
    print("\n" + "=" * 50)
    print("WIRING CHECKLIST")
    print("=" * 50)
    print("□ 330-470Ω resistor on data line")
    print("□ Common ground between ESP32 and power supplies")
    print("□ 1000µF capacitor at each power injection point")
    print("□ Level shifter (3.3V to 5V) for reliability")
    print("□ Short data wire from ESP32 to first panel")
    print("□ Proper gauge wire for current draw")
    

if __name__ == "__main__":
    main()