/*
 * WS2812B LED Panel Controller for ESP32
 * Single-pin daisy-chained panel configuration
 * Compatible with FastLED library
 */

#include <FastLED.h>

// Configuration
#define MAX_PANELS 64          // Maximum number of panels (4x16 = 64 for large display)
#define MAX_LEDS_PER_PANEL 256 // Maximum LEDs per panel (16x16)
#define MAX_TOTAL_LEDS 16384   // Maximum total LEDs (64 * 256)

// Pin definition - Single data pin for daisy-chained panels
#define LED_DATA_PIN 13        // Data pin for WS2812B strip
#define LED_BACKUP_PIN 14      // Optional backup pin for redundancy

// Serial communication settings
#define SERIAL_BAUDRATE 115200  // Reduced from 921600 for reliability
#define BUFFER_SIZE 2048

// Protocol definitions
#define START_BYTE_1 0xAA
#define START_BYTE_2 0x55

enum Commands {
    CMD_SET_PIXELS = 0x01,
    CMD_CLEAR = 0x02,
    CMD_BRIGHTNESS = 0x03,
    CMD_SHOW = 0x04,
    CMD_CONFIG = 0x05
};

// Panel configuration
struct PanelConfig {
    uint16_t numPanels;
    uint16_t ledsPerPanel;
    uint16_t totalLeds;
    uint8_t brightness;
};

// LED panel class
class LEDPanelController {
private:
    CRGB* leds;  // Single array for all LEDs (daisy-chained)
    PanelConfig config;
    uint8_t receiveBuffer[BUFFER_SIZE];
    uint16_t bufferIndex;
    uint16_t dataOffset;
    bool receivingData;
    uint8_t currentCommand;
    uint16_t expectedDataLength;
    uint16_t receivedDataLength;
    
    // Panel mapping for physical layout
    uint16_t* panelMap;  // Maps logical panel position to physical position
    
public:
    LEDPanelController() {
        config.numPanels = 4;    // Default 2x2 grid for 32x32 display
        config.ledsPerPanel = 256;  // Default 16x16 panels
        config.totalLeds = config.numPanels * config.ledsPerPanel;
        config.brightness = 128;  // Default 50% brightness
        
        bufferIndex = 0;
        dataOffset = 0;
        receivingData = false;
        currentCommand = 0;
        expectedDataLength = 0;
        receivedDataLength = 0;
        
        leds = nullptr;
        panelMap = nullptr;
    }
    
    void begin() {
        // Allocate memory for LED array
        leds = new CRGB[config.totalLeds];
        memset(leds, 0, sizeof(CRGB) * config.totalLeds);
        
        // Initialize panel mapping (default sequential)
        panelMap = new uint16_t[config.numPanels];
        for (int i = 0; i < config.numPanels; i++) {
            panelMap[i] = i;  // Default: logical = physical
        }
        
        // Initialize FastLED with single pin for daisy-chained panels
        FastLED.addLeds<WS2812B, LED_DATA_PIN, GRB>(leds, config.totalLeds);
        
        // Optional: Add backup pin for redundancy
        // FastLED.addLeds<WS2812B, LED_BACKUP_PIN, GRB>(leds, config.totalLeds);
        
        FastLED.setBrightness(config.brightness);
        FastLED.clear();
        FastLED.show();
        
        // Set FastLED parameters for better performance
        FastLED.setMaxRefreshRate(0);  // No refresh rate limit
        FastLED.setDither(0);           // Disable dithering for consistency
        
        // Start serial communication
        Serial.begin(SERIAL_BAUDRATE);
        Serial.setTimeout(10);
        
        // Wait for serial to be ready
        delay(1000);
        
        // Send ready signal
        Serial.println("ESP32 LED Controller Ready - Binary Protocol Mode");
        Serial.print("Total LEDs: ");
        Serial.println(config.totalLeds);
        Serial.print("Baud Rate: ");
        Serial.println(SERIAL_BAUDRATE);
        Serial.println("Waiting for commands...");
    }
    
    void processSerial() {
        while (Serial.available() > 0) {
            uint8_t byte = Serial.read();
            
            // Debug output for first few bytes
            if (bufferIndex < 5) {
                Serial.print("Byte ");
                Serial.print(bufferIndex);
                Serial.print(": 0x");
                Serial.println(byte, HEX);
            }
            
            if (!receivingData) {
                // Look for start bytes
                if (bufferIndex == 0 && byte == START_BYTE_1) {
                    receiveBuffer[bufferIndex++] = byte;
                } else if (bufferIndex == 1 && byte == START_BYTE_2) {
                    receiveBuffer[bufferIndex++] = byte;
                } else if (bufferIndex == 2) {
                    // Command byte
                    currentCommand = byte;
                    receiveBuffer[bufferIndex++] = byte;
                    Serial.print("Command received: 0x");
                    Serial.println(currentCommand, HEX);
                } else if (bufferIndex == 3) {
                    // Data length low byte
                    receiveBuffer[bufferIndex++] = byte;
                } else if (bufferIndex == 4) {
                    // Data length high byte
                    receiveBuffer[bufferIndex++] = byte;
                    // Little-endian: low byte (index 3) | high byte (index 4) << 8
                    expectedDataLength = receiveBuffer[3] | (receiveBuffer[4] << 8);
                    receivedDataLength = 0;
                    receivingData = true;
                    
                    Serial.print("Expected data length: ");
                    Serial.println(expectedDataLength);
                    
                    if (expectedDataLength == 0) {
                        // No data expected, process command immediately
                        processCommand();
                        resetBuffer();
                    }
                } else {
                    // Invalid state, reset
                    Serial.println("Invalid packet, resetting buffer");
                    resetBuffer();
                }
            } else {
                // Receiving data bytes
                if (receivedDataLength < expectedDataLength) {
                    receiveBuffer[bufferIndex++] = byte;
                    receivedDataLength++;
                    
                    // Check buffer overflow
                    if (bufferIndex >= BUFFER_SIZE) {
                        Serial.println("Buffer overflow!");
                        resetBuffer();
                        return;
                    }
                } else {
                    // This should be the checksum byte
                    uint8_t calculatedChecksum = calculateChecksum();
                    if (byte == calculatedChecksum) {
                        Serial.println("Checksum OK, processing command");
                        processCommand();
                    } else {
                        Serial.print("Checksum error! Expected: ");
                        Serial.print(calculatedChecksum, HEX);
                        Serial.print(" Got: ");
                        Serial.println(byte, HEX);
                    }
                    resetBuffer();
                }
            }
        }
    }
    
    uint8_t calculateChecksum() {
        uint16_t sum = 0;
        for (int i = 2; i < bufferIndex; i++) {
            sum += receiveBuffer[i];
        }
        return sum & 0xFF;
    }
    
    void processCommand() {
        Serial.print("Processing command: 0x");
        Serial.println(currentCommand, HEX);
        
        switch (currentCommand) {
            case CMD_SET_PIXELS:
                handleSetPixels();
                Serial.println("Pixels updated");
                break;
            case CMD_CLEAR:
                handleClear();
                Serial.println("Display cleared");
                break;
            case CMD_BRIGHTNESS:
                handleBrightness();
                Serial.println("Brightness updated");
                break;
            case CMD_SHOW:
                handleShow();
                Serial.println("Display refreshed");
                break;
            case CMD_CONFIG:
                handleConfig();
                break;
            default:
                Serial.print("Unknown command: 0x");
                Serial.println(currentCommand, HEX);
                break;
        }
    }
    
    void handleSetPixels() {
        // Extract offset from first 2 bytes of data (little-endian)
        uint16_t offset = receiveBuffer[5] | (receiveBuffer[6] << 8);
        
        // Copy pixel data directly to LED array
        uint16_t dataStart = 7;
        uint16_t pixelDataLength = expectedDataLength - 2;
        uint16_t pixelCount = pixelDataLength / 3;
        
        Serial.print("Setting ");
        Serial.print(pixelCount);
        Serial.print(" pixels starting at offset ");
        Serial.println(offset);
        
        for (uint16_t i = 0; i < pixelDataLength; i += 3) {
            uint16_t ledIndex = offset + i/3;
            if (ledIndex < config.totalLeds) {
                leds[ledIndex].r = receiveBuffer[dataStart + i];
                leds[ledIndex].g = receiveBuffer[dataStart + i + 1];
                leds[ledIndex].b = receiveBuffer[dataStart + i + 2];
            }
        }
    }
    
    void handleClear() {
        memset(leds, 0, sizeof(CRGB) * config.totalLeds);
        FastLED.show();
    }
    
    void handleBrightness() {
        if (expectedDataLength >= 1) {
            config.brightness = receiveBuffer[5];
            FastLED.setBrightness(config.brightness);
            FastLED.show();
        }
    }
    
    void handleShow() {
        FastLED.show();
    }
    
    void handleConfig() {
        if (expectedDataLength >= 4) {
            // Read configuration (little-endian)
            uint16_t newNumPanels = receiveBuffer[5] | (receiveBuffer[6] << 8);
            uint16_t newLedsPerPanel = receiveBuffer[7] | (receiveBuffer[8] << 8);
            
            // Optional: Panel mapping data (for snake patterns, etc.)
            bool hasPanelMapping = (expectedDataLength >= 4 + newNumPanels * 2);
            
            // Validate configuration
            if (newNumPanels <= MAX_PANELS && 
                newLedsPerPanel <= MAX_LEDS_PER_PANEL &&
                newNumPanels * newLedsPerPanel <= MAX_TOTAL_LEDS) {
                
                // Update configuration
                config.numPanels = newNumPanels;
                config.ledsPerPanel = newLedsPerPanel;
                config.totalLeds = config.numPanels * config.ledsPerPanel;
                
                Serial.print("Config: ");
                Serial.print(config.numPanels);
                Serial.print(" panels, ");
                Serial.print(config.ledsPerPanel);
                Serial.print(" LEDs each, total: ");
                Serial.println(config.totalLeds);
                
                // Update panel mapping if provided
                if (hasPanelMapping) {
                    for (int i = 0; i < newNumPanels; i++) {
                        uint16_t mapIndex = 9 + (i * 2);
                        panelMap[i] = receiveBuffer[mapIndex] | (receiveBuffer[mapIndex + 1] << 8);
                    }
                }
                
                // Reinitialize LED array
                reinitializeLEDs();
                
                Serial.println("Configuration updated");
            } else {
                Serial.println("Invalid configuration");
            }
        }
    }
    
    void reinitializeLEDs() {
        // Clear existing LEDs
        FastLED.clear();
        FastLED.show();
        
        // Free existing memory
        if (leds != nullptr) {
            delete[] leds;
            leds = nullptr;
        }
        if (panelMap != nullptr) {
            delete[] panelMap;
        }
        
        // Reallocate based on new configuration
        leds = new CRGB[config.totalLeds];
        memset(leds, 0, sizeof(CRGB) * config.totalLeds);
        
        panelMap = new uint16_t[config.numPanels];
        for (int i = 0; i < config.numPanels; i++) {
            panelMap[i] = i;  // Reset to default mapping
        }
        
        // Reinitialize FastLED
        FastLED.addLeds<WS2812B, LED_DATA_PIN, GRB>(leds, config.totalLeds);
        FastLED.setBrightness(config.brightness);
    }
    
    void resetBuffer() {
        bufferIndex = 0;
        receivingData = false;
        currentCommand = 0;
        expectedDataLength = 0;
        receivedDataLength = 0;
    }
    
    void runTestPattern() {
        // Test pattern: Light up each panel sequentially
        static uint16_t currentPanel = 0;
        static uint8_t hue = 0;
        
        // Clear all
        memset(leds, 0, sizeof(CRGB) * config.totalLeds);
        
        // Light up current panel
        uint16_t startLed = currentPanel * config.ledsPerPanel;
        uint16_t endLed = startLed + config.ledsPerPanel;
        
        for (uint16_t i = startLed; i < endLed && i < config.totalLeds; i++) {
            leds[i] = CHSV(hue, 255, 255);
        }
        
        FastLED.show();
        
        // Move to next panel
        currentPanel = (currentPanel + 1) % config.numPanels;
        hue += 10;
    }
    
    void setPixelXY(uint16_t x, uint16_t y, CRGB color) {
        // Helper function to set pixel by X,Y coordinates
        // Assumes panels are arranged in a grid
        uint16_t panelsPerRow = 2;  // Adjust based on your layout (2x2 default)
        uint16_t pixelsPerPanelRow = 16;  // For 16x16 panels
        
        uint16_t panelX = x / pixelsPerPanelRow;
        uint16_t panelY = y / pixelsPerPanelRow;
        uint16_t pixelX = x % pixelsPerPanelRow;
        uint16_t pixelY = y % pixelsPerPanelRow;
        
        uint16_t panelIndex = panelY * panelsPerRow + panelX;
        uint16_t pixelIndex = panelIndex * config.ledsPerPanel + 
                              pixelY * pixelsPerPanelRow + pixelX;
        
        if (pixelIndex < config.totalLeds) {
            leds[pixelIndex] = color;
        }
    }
};

// Global controller instance
LEDPanelController controller;

// Performance monitoring
unsigned long lastFrameTime = 0;
unsigned long frameCount = 0;
unsigned long lastFPSReport = 0;

void setup() {
    // Small delay for stable startup
    delay(500);
    
    // Initialize controller
    controller.begin();
    
    // Set up performance monitoring
    lastFrameTime = millis();
    lastFPSReport = millis();
    
    // Optional: Show startup pattern
    showStartupPattern();
    
    Serial.println("System ready for commands");
}

void loop() {
    // Process serial commands
    controller.processSerial();
    
    // Performance monitoring (optional)
    frameCount++;
    if (millis() - lastFPSReport >= 1000) {
        // Uncomment to see FPS in serial monitor
        // Serial.print("FPS: ");
        // Serial.println(frameCount);
        frameCount = 0;
        lastFPSReport = millis();
    }
    
    // Small delay to prevent watchdog issues
    delay(1);
}

void showStartupPattern() {
    // Show a brief startup pattern to indicate the system is ready
    Serial.println("Showing startup pattern...");
    for (int i = 0; i < 50; i++) {
        controller.runTestPattern();
        delay(20);
    }
    
    // Clear display
    FastLED.clear();
    FastLED.show();
    Serial.println("Startup pattern complete");
}

// Optional: WiFi control addition
#ifdef USE_WIFI
#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

WebServer server(80);

void setupWiFi() {
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("");
    Serial.print("Connected to WiFi. IP: ");
    Serial.println(WiFi.localIP());
    
    // Set up web server endpoints
    server.on("/clear", HTTP_GET, []() {
        FastLED.clear();
        FastLED.show();
        server.send(200, "text/plain", "Display cleared");
    });
    
    server.on("/brightness", HTTP_GET, []() {
        if (server.hasArg("value")) {
            int brightness = server.arg("value").toInt();
            if (brightness >= 0 && brightness <= 255) {
                FastLED.setBrightness(brightness);
                FastLED.show();
                server.send(200, "text/plain", "Brightness set");
            } else {
                server.send(400, "text/plain", "Invalid brightness value");
            }
        } else {
            server.send(400, "text/plain", "Missing brightness value");
        }
    });
    
    server.begin();
}
#endif