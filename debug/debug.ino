/*
 * WS2812B LED Panel Controller for ESP32 - DEBUG VERSION
 * Simplified protocol for troubleshooting
 */

#include <FastLED.h>

// Configuration - adjust these for your setup
#define LED_DATA_PIN 26        // Data pin for WS2812B strip
#define NUM_PANELS 4           // Number of 16x16 panels (2x2 = 4)
#define LEDS_PER_PANEL 256     // 16x16 = 256 LEDs per panel
#define NUM_LEDS (NUM_PANELS * LEDS_PER_PANEL)  // Total LEDs
#define SERIAL_BAUDRATE 115200 // Lower baud rate for debugging

// LED array
CRGB leds[NUM_LEDS];

// Simple test modes
int testMode = 0;
unsigned long lastUpdate = 0;
uint8_t testHue = 0;

void setup() {
    // Initialize Serial first for debugging
    Serial.begin(SERIAL_BAUDRATE);
    delay(1000);  // Give serial time to initialize
    
    Serial.println("ESP32 LED Controller Starting...");
    Serial.print("Total LEDs configured: ");
    Serial.println(NUM_LEDS);
    Serial.print("Panels: ");
    Serial.println(NUM_PANELS);
    
    // Initialize FastLED
    FastLED.addLeds<WS2812B, LED_DATA_PIN, GRB>(leds, NUM_LEDS);
    FastLED.setBrightness(64);  // Start at 25% brightness for safety
    
    // Clear all LEDs
    FastLED.clear();
    FastLED.show();
    
    // Show startup pattern
    Serial.println("Showing startup pattern...");
    showStartupPattern();
    
    // Clear again
    FastLED.clear();
    FastLED.show();
    
    Serial.println("Ready for commands!");
    Serial.println("Commands:");
    Serial.println("  R - Red test");
    Serial.println("  G - Green test");
    Serial.println("  B - Blue test");
    Serial.println("  W - White test");
    Serial.println("  C - Clear");
    Serial.println("  T - Test pattern");
    Serial.println("  S - Snake test (shows panel order)");
    Serial.println("  P<rrr,ggg,bbb> - Set all pixels to RGB");
    Serial.println("  I<index>,<r>,<g>,<b> - Set specific LED");
}

void loop() {
    // Check for serial commands
    if (Serial.available() > 0) {
        char cmd = Serial.read();
        processCommand(cmd);
    }
    
    // If in test mode, update test pattern
    if (testMode > 0 && millis() - lastUpdate > 50) {
        updateTestPattern();
        lastUpdate = millis();
    }
}

void processCommand(char cmd) {
    Serial.print("Received command: ");
    Serial.println(cmd);
    
    switch(cmd) {
        case 'R':
        case 'r':
            // Red test
            Serial.println("Setting all LEDs to RED");
            fill_solid(leds, NUM_LEDS, CRGB::Red);
            FastLED.show();
            testMode = 0;
            break;
            
        case 'G':
        case 'g':
            // Green test
            Serial.println("Setting all LEDs to GREEN");
            fill_solid(leds, NUM_LEDS, CRGB::Green);
            FastLED.show();
            testMode = 0;
            break;
            
        case 'B':
        case 'b':
            // Blue test
            Serial.println("Setting all LEDs to BLUE");
            fill_solid(leds, NUM_LEDS, CRGB::Blue);
            FastLED.show();
            testMode = 0;
            break;
            
        case 'W':
        case 'w':
            // White test (careful with power!)
            Serial.println("Setting all LEDs to WHITE (25% brightness)");
            fill_solid(leds, NUM_LEDS, CRGB::White);
            FastLED.setBrightness(64);  // Limit brightness
            FastLED.show();
            testMode = 0;
            break;
            
        case 'C':
        case 'c':
            // Clear
            Serial.println("Clearing all LEDs");
            FastLED.clear();
            FastLED.show();
            testMode = 0;
            break;
            
        case 'T':
        case 't':
            // Test pattern
            Serial.println("Starting rainbow test pattern");
            testMode = 1;
            break;
            
        case 'S':
        case 's':
            // Snake test - shows panel order
            Serial.println("Starting snake test (panel order)");
            testMode = 2;
            break;
            
        case 'P':
        case 'p':
            // Set all pixels to specific color
            // Format: P<rrr,ggg,bbb>
            parseColorCommand();
            break;
            
        case 'I':
        case 'i':
            // Set individual LED
            // Format: I<index>,<r>,<g>,<b>
            parseIndexCommand();
            break;
            
        case 'H':
        case 'h':
            // Set brightness
            parseBrightnessCommand();
            break;
            
        case '\n':
        case '\r':
            // Ignore newlines
            break;
            
        default:
            Serial.print("Unknown command: ");
            Serial.println(cmd);
            break;
    }
}

void parseColorCommand() {
    // Read RGB values in format: rrr,ggg,bbb
    String colorStr = Serial.readStringUntil('\n');
    
    int commaIndex1 = colorStr.indexOf(',');
    int commaIndex2 = colorStr.lastIndexOf(',');
    
    if (commaIndex1 > 0 && commaIndex2 > commaIndex1) {
        int r = colorStr.substring(0, commaIndex1).toInt();
        int g = colorStr.substring(commaIndex1 + 1, commaIndex2).toInt();
        int b = colorStr.substring(commaIndex2 + 1).toInt();
        
        r = constrain(r, 0, 255);
        g = constrain(g, 0, 255);
        b = constrain(b, 0, 255);
        
        Serial.print("Setting all LEDs to RGB(");
        Serial.print(r); Serial.print(",");
        Serial.print(g); Serial.print(",");
        Serial.print(b); Serial.println(")");
        
        fill_solid(leds, NUM_LEDS, CRGB(r, g, b));
        FastLED.show();
        testMode = 0;
    } else {
        Serial.println("Invalid color format. Use: P<rrr,ggg,bbb>");
    }
}

void parseIndexCommand() {
    // Read index and RGB values
    String indexStr = Serial.readStringUntil('\n');
    
    int comma1 = indexStr.indexOf(',');
    int comma2 = indexStr.indexOf(',', comma1 + 1);
    int comma3 = indexStr.lastIndexOf(',');
    
    if (comma1 > 0 && comma2 > comma1 && comma3 > comma2) {
        int index = indexStr.substring(0, comma1).toInt();
        int r = indexStr.substring(comma1 + 1, comma2).toInt();
        int g = indexStr.substring(comma2 + 1, comma3).toInt();
        int b = indexStr.substring(comma3 + 1).toInt();
        
        if (index >= 0 && index < NUM_LEDS) {
            leds[index] = CRGB(r, g, b);
            FastLED.show();
            
            Serial.print("Set LED ");
            Serial.print(index);
            Serial.print(" to RGB(");
            Serial.print(r); Serial.print(",");
            Serial.print(g); Serial.print(",");
            Serial.print(b); Serial.println(")");
        } else {
            Serial.print("Invalid index: ");
            Serial.println(index);
        }
    } else {
        Serial.println("Invalid format. Use: I<index>,<r>,<g>,<b>");
    }
}

void parseBrightnessCommand() {
    String brightStr = Serial.readStringUntil('\n');
    int brightness = brightStr.toInt();
    brightness = constrain(brightness, 0, 255);
    
    FastLED.setBrightness(brightness);
    FastLED.show();
    
    Serial.print("Brightness set to: ");
    Serial.println(brightness);
}

void updateTestPattern() {
    if (testMode == 1) {
        // Rainbow pattern
        fill_rainbow(leds, NUM_LEDS, testHue, 7);
        FastLED.show();
        testHue += 2;
    } else if (testMode == 2) {
        // Snake test - light up one panel at a time
        static int currentPanel = 0;
        static unsigned long lastPanelChange = 0;
        
        if (millis() - lastPanelChange > 500) {
            // Clear all
            FastLED.clear();
            
            // Light up current panel
            int startLed = currentPanel * LEDS_PER_PANEL;
            int endLed = startLed + LEDS_PER_PANEL;
            
            for (int i = startLed; i < endLed && i < NUM_LEDS; i++) {
                leds[i] = CHSV(currentPanel * 60, 255, 255);
            }
            
            FastLED.show();
            
            Serial.print("Panel ");
            Serial.print(currentPanel);
            Serial.print(" (LEDs ");
            Serial.print(startLed);
            Serial.print("-");
            Serial.print(endLed - 1);
            Serial.println(")");
            
            currentPanel = (currentPanel + 1) % NUM_PANELS;
            lastPanelChange = millis();
        }
    }
}

void showStartupPattern() {
    // Quick rainbow sweep to indicate system is working
    for (int i = 0; i < 256; i++) {
        fill_rainbow(leds, NUM_LEDS, i, 7);
        FastLED.show();
        delay(5);
    }
}

// Function to process binary data (for future use)
void processBinaryData() {
    // This will be implemented once basic serial works
    // For now, using simple text commands for debugging
}