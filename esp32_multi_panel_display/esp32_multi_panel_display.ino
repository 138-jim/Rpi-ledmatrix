/*
 * WS2812B LED Panel Controller for ESP32
 * Supports multiple panels with high-speed serial communication
 * Compatible with FastLED library
 */

#include <FastLED.h>
#include <vector>

// Configuration
#define MAX_PANELS 64          // Maximum number of panels (4x16 = 64 for 32x32)
#define MAX_LEDS_PER_PANEL 64  // Maximum LEDs per panel (8x8)
#define MAX_TOTAL_LEDS 4096    // Maximum total LEDs

// Pin definitions - Adjust based on your wiring
// Using multiple pins for better performance with parallel output
#define LED_PIN_1 13  // First set of panels
#define LED_PIN_2 12  // Second set of panels
#define LED_PIN_3 14  // Third set of panels
#define LED_PIN_4 27  // Fourth set of panels

// Serial communication settings
#define SERIAL_BAUDRATE 921600
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
    CRGB* leds[4];  // Array of LED arrays for parallel output
    PanelConfig config;
    uint8_t receiveBuffer[BUFFER_SIZE];
    uint16_t bufferIndex;
    uint16_t dataOffset;
    bool receivingData;
    uint8_t currentCommand;
    uint16_t expectedDataLength;
    uint16_t receivedDataLength;
    
public:
    LEDPanelController() {
        config.numPanels = 16;  // Default 4x4 grid
        config.ledsPerPanel = 64;  // Default 8x8 panels
        config.totalLeds = config.numPanels * config.ledsPerPanel;
        config.brightness = 128;  // Default 50% brightness
        
        bufferIndex = 0;
        dataOffset = 0;
        receivingData = false;
        currentCommand = 0;
        expectedDataLength = 0;
        receivedDataLength = 0;
        
        // Initialize LED arrays
        for (int i = 0; i < 4; i++) {
            leds[i] = nullptr;
        }
    }
    
    void begin() {
        // Calculate LEDs per pin (distribute evenly)
        uint16_t ledsPerPin = config.totalLeds / 4;
        
        // Allocate memory for LED arrays
        for (int i = 0; i < 4; i++) {
            leds[i] = new CRGB[ledsPerPin];
            memset(leds[i], 0, sizeof(CRGB) * ledsPerPin);
        }
        
        // Initialize FastLED for each pin
        // Using parallel output for better performance
        FastLED.addLeds<WS2812B, LED_PIN_1, GRB>(leds[0], ledsPerPin);
        FastLED.addLeds<WS2812B, LED_PIN_2, GRB>(leds[1], ledsPerPin);
        FastLED.addLeds<WS2812B, LED_PIN_3, GRB>(leds[2], ledsPerPin);
        FastLED.addLeds<WS2812B, LED_PIN_4, GRB>(leds[3], ledsPerPin);
        
        FastLED.setBrightness(config.brightness);
        FastLED.clear();
        FastLED.show();
        
        // Start serial communication
        Serial.begin(SERIAL_BAUDRATE);
        Serial.setTimeout(10);
        
        // Send ready signal
        Serial.println("ESP32 LED Controller Ready");
    }
    
    void processSerial() {
        while (Serial.available() > 0) {
            uint8_t byte = Serial.read();
            
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
                } else if (bufferIndex == 3) {
                    // Data length low byte
                    receiveBuffer[bufferIndex++] = byte;
                } else if (bufferIndex == 4) {
                    // Data length high byte
                    receiveBuffer[bufferIndex++] = byte;
                    expectedDataLength = (receiveBuffer[4] << 8) | receiveBuffer[3];
                    receivedDataLength = 0;
                    receivingData = true;
                    
                    if (expectedDataLength == 0) {
                        // No data expected, process command immediately
                        processCommand();
                        resetBuffer();
                    }
                } else {
                    // Invalid state, reset
                    resetBuffer();
                }
            } else {
                // Receiving data bytes
                if (receivedDataLength < expectedDataLength) {
                    receiveBuffer[bufferIndex++] = byte;
                    receivedDataLength++;
                    
                    // Check buffer overflow
                    if (bufferIndex >= BUFFER_SIZE) {
                        resetBuffer();
                        return;
                    }
                } else {
                    // This should be the checksum byte
                    uint8_t calculatedChecksum = calculateChecksum();
                    if (byte == calculatedChecksum) {
                        processCommand();
                    } else {
                        Serial.println("Checksum error");
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
        switch (currentCommand) {
            case CMD_SET_PIXELS:
                handleSetPixels();
                break;
            case CMD_CLEAR:
                handleClear();
                break;
            case CMD_BRIGHTNESS:
                handleBrightness();
                break;
            case CMD_SHOW:
                handleShow();
                break;
            case CMD_CONFIG:
                handleConfig();
                break;
            default:
                Serial.println("Unknown command");
                break;
        }
    }
    
    void handleSetPixels() {
        // Extract offset from first 2 bytes of data
        uint16_t offset = (receiveBuffer[6] << 8) | receiveBuffer[5];
        
        // Copy pixel data
        uint16_t dataStart = 7;
        uint16_t pixelDataLength = expectedDataLength - 2;
        
        // Calculate which LED array and position
        for (uint16_t i = 0; i < pixelDataLength; i += 3) {
            if (offset + i/3 < config.totalLeds) {
                uint16_t ledIndex = offset + i/3;
                uint8_t arrayIndex = ledIndex / (config.totalLeds / 4);
                uint16_t localIndex = ledIndex % (config.totalLeds / 4);
                
                if (arrayIndex < 4 && leds[arrayIndex] != nullptr) {
                    leds[arrayIndex][localIndex].r = receiveBuffer[dataStart + i];
                    leds[arrayIndex][localIndex].g = receiveBuffer[dataStart + i + 1];
                    leds[arrayIndex][localIndex].b = receiveBuffer[dataStart + i + 2];
                }
            }
        }
    }
    
    void handleClear() {
        for (int i = 0; i < 4; i++) {
            if (leds[i] != nullptr) {
                uint16_t ledsPerPin = config.totalLeds / 4;
                memset(leds[i], 0, sizeof(CRGB) * ledsPerPin);
            }
        }
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
            uint16_t newNumPanels = (receiveBuffer[6] << 8) | receiveBuffer[5];
            uint16_t newLedsPerPanel = (receiveBuffer[8] << 8) | receiveBuffer[7];
            
            // Validate configuration
            if (newNumPanels <= MAX_PANELS && 
                newLedsPerPanel <= MAX_LEDS_PER_PANEL &&
                newNumPanels * newLedsPerPanel <= MAX_TOTAL_LEDS) {
                
                // Update configuration
                config.numPanels = newNumPanels;
                config.ledsPerPanel = newLedsPerPanel;
                config.totalLeds = config.numPanels * config.ledsPerPanel;
                
                // Reinitialize LED arrays
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
        for (int i = 0; i < 4; i++) {
            if (leds[i] != nullptr) {
                delete[] leds[i];
                leds[i] = nullptr;
            }
        }
        
        // Reallocate based on new configuration
        uint16_t ledsPerPin = config.totalLeds / 4;
        
        for (int i = 0; i < 4; i++) {
            leds[i] = new CRGB[ledsPerPin];
            memset(leds[i], 0, sizeof(CRGB) * ledsPerPin);
        }
        
        // Reinitialize FastLED
        FastLED.addLeds<WS2812B, LED_PIN_1, GRB>(leds[0], ledsPerPin);
        FastLED.addLeds<WS2812B, LED_PIN_2, GRB>(leds[1], ledsPerPin);
        FastLED.addLeds<WS2812B, LED_PIN_3, GRB>(leds[2], ledsPerPin);
        FastLED.addLeds<WS2812B, LED_PIN_4, GRB>(leds[3], ledsPerPin);
        
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
        // Rainbow test pattern for debugging
        static uint8_t hue = 0;
        
        for (int i = 0; i < 4; i++) {
            if (leds[i] != nullptr) {
                uint16_t ledsPerPin = config.totalLeds / 4;
                for (int j = 0; j < ledsPerPin; j++) {
                    leds[i][j] = CHSV(hue + (j * 2), 255, 255);
                }
            }
        }
        
        FastLED.show();
        hue++;
    }
};

// Global controller instance
LEDPanelController controller;

// Performance monitoring
unsigned long lastFrameTime = 0;
unsigned long frameCount = 0;
unsigned long lastFPSReport = 0;

void setup() {
    // Initialize controller
    controller.begin();
    
    // Set up performance monitoring
    lastFrameTime = millis();
    lastFPSReport = millis();
    
    // Optional: Show startup pattern
    showStartupPattern();
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
    for (int i = 0; i < 50; i++) {
        controller.runTestPattern();
        delay(20);
    }
    
    // Clear display
    FastLED.clear();
    FastLED.show();
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