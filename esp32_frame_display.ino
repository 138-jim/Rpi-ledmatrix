#include <FastLED.h>

// LED Matrix Configuration
#define LED_PIN     26        // GPIO pin connected to the LED data line
#define MATRIX_WIDTH  16      // Number of LEDs horizontally
#define MATRIX_HEIGHT 16      // Number of LEDs vertically
#define NUM_LEDS (MATRIX_WIDTH * MATRIX_HEIGHT)
#define BRIGHTNESS  50        // LED brightness (0-255)

// Display orientation settings
#define FLIP_HORIZONTAL true  // Set to true if text appears mirror-flipped
#define FLIP_VERTICAL   false // Set to true if text appears upside-down
#define SERPENTINE_LAYOUT true // Set to false if your LEDs go row-by-row instead of zigzag

CRGB leds[NUM_LEDS];

// Frame buffer for incoming data
uint8_t frameBuffer[NUM_LEDS * 3]; // RGB data for each LED
bool newFrameReady = false;

// Convert XY coordinates to LED index
int XY(int x, int y) {
  // Apply horizontal flip if needed
  if (FLIP_HORIZONTAL) {
    x = MATRIX_WIDTH - 1 - x;
  }
  
  // Apply vertical flip if needed
  if (FLIP_VERTICAL) {
    y = MATRIX_HEIGHT - 1 - y;
  }
  
  if (SERPENTINE_LAYOUT) {
    // Serpentine layout (zigzag)
    if (y & 0x01) {
      // Odd rows run backwards
      return (y + 1) * MATRIX_WIDTH - 1 - x;
    } else {
      // Even rows run forwards
      return y * MATRIX_WIDTH + x;
    }
  } else {
    // Simple row-by-row layout
    return y * MATRIX_WIDTH + x;
  }
}

// Protocol: FRAME:<768 bytes of RGB data>:END
void parseSerialData() {
  static String inputBuffer = "";
  
  while (Serial.available()) {
    char c = Serial.read();
    inputBuffer += c;
    
    // Check for complete frame command
    if (inputBuffer.startsWith("FRAME:") && inputBuffer.endsWith(":END")) {
      // Extract frame data
      int startPos = 6; // After "FRAME:"
      int endPos = inputBuffer.length() - 4; // Before ":END"
      
      if (endPos - startPos == NUM_LEDS * 3) {
        // Copy RGB data to frame buffer
        for (int i = 0; i < NUM_LEDS * 3; i++) {
          frameBuffer[i] = inputBuffer[startPos + i];
        }
        newFrameReady = true;
        Serial.println("FRAME_OK");
      } else {
        Serial.println("FRAME_ERROR: Invalid size");
      }
      
      inputBuffer = "";
    }
    // Handle brightness command
    else if (inputBuffer.startsWith("BRIGHTNESS:") && c == '\n') {
      int brightness = inputBuffer.substring(11).toInt();
      if (brightness >= 0 && brightness <= 255) {
        FastLED.setBrightness(brightness);
        FastLED.show();
        Serial.println("BRIGHTNESS_OK");
      } else {
        Serial.println("BRIGHTNESS_ERROR");
      }
      inputBuffer = "";
    }
    // Handle clear command
    else if (inputBuffer.startsWith("CLEAR") && c == '\n') {
      FastLED.clear();
      FastLED.show();
      Serial.println("CLEAR_OK");
      inputBuffer = "";
    }
    // Reset buffer if it gets too long (prevents memory issues)
    else if (inputBuffer.length() > NUM_LEDS * 3 + 20) {
      inputBuffer = "";
    }
  }
}

void displayFrame() {
  if (newFrameReady) {
    // Convert frame buffer to LED array
    for (int i = 0; i < NUM_LEDS; i++) {
      leds[i] = CRGB(
        frameBuffer[i * 3],     // R
        frameBuffer[i * 3 + 1], // G
        frameBuffer[i * 3 + 2]  // B
      );
    }
    
    FastLED.show();
    newFrameReady = false;
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 Frame Display Ready");
  
  // Initialize FastLED
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.clear();
  FastLED.show();
  
  // Initialize frame buffer to black
  memset(frameBuffer, 0, sizeof(frameBuffer));
  
  Serial.println("Ready for frames");
}

void loop() {
  parseSerialData();
  displayFrame();
  
  // Small delay to prevent overwhelming the serial buffer
  delayMicroseconds(100);
}