#define RED_PIN 5
#define GREEN_PIN 6
#define BLUE_PIN 7
#define BUTTON_PIN 2
#define RELAY_PIN A0
#define SOIL_SENSOR_PIN A1

int buttonStatus = HIGH; // Store the current button status
int pinValue;            // Store the read value from the button
unsigned long lastSoilReading = 0; // Last soil read
const unsigned long soilInterval = 3000; // Read soil delay

void setup() {
    pinMode(SOIL_SENSOR_PIN, INPUT);
    pinMode(RELAY_PIN, OUTPUT);
    pinMode(RED_PIN, OUTPUT);
    pinMode(GREEN_PIN, OUTPUT);
    pinMode(BLUE_PIN, OUTPUT);
    pinMode(BUTTON_PIN, INPUT_PULLUP);  // Use internal pull-up resistor
    Serial.begin(9600);

    // Turn off everything initially
    digitalWrite(RELAY_PIN, LOW);
    digitalWrite(RED_PIN, HIGH);
    digitalWrite(GREEN_PIN, LOW);
    digitalWrite(BLUE_PIN, LOW);
}

void loop() {
    unsigned long currentMillis = millis();
    if (currentMillis - lastSoilReading >= soilInterval) {
        lastSoilReading = currentMillis; // Update time last read
        int soilMoisture = analogRead(SOIL_SENSOR_PIN);
        Serial.print("Soil moisture: ");
        Serial.println(soilMoisture);
    }
    pinValue = digitalRead(BUTTON_PIN);
    delay(10); // Debounce delay

    if (buttonStatus != pinValue) { // Button state has changed
        buttonStatus = pinValue;

        if (buttonStatus == LOW) { // Button was pressed
            Serial.println("Button pressed!");
            digitalWrite(RED_PIN, LOW);
            digitalWrite(GREEN_PIN, HIGH);
            digitalWrite(RELAY_PIN, HIGH);
        } else { // Button was released
            Serial.println("Button released!");
            digitalWrite(GREEN_PIN, LOW);
            digitalWrite(RED_PIN, HIGH);
            digitalWrite(RELAY_PIN, LOW);
        }
    }
}