#define RED_PIN 5
#define GREEN_PIN 6
#define BLUE_PIN 7
#define BUTTON_PIN 2
#define RELAY_PIN A0
#define SOIL_SENSOR_PIN A1

int buttonStatus = HIGH; // Button status
int pinValue;
unsigned long lastSoilReading = 0;
unsigned long lastPumpRun = 0;
const unsigned long soilInterval = 1500; // Read soil delay
const unsigned long pumpRunTime = 10000;  // Pump runs for 10 sec
const unsigned long pumpCooldown = 15000; // Wait 15 sec before next pump // cooldown safety
bool isPumping = false;

void setup()
{
    pinMode(SOIL_SENSOR_PIN, INPUT);
    pinMode(RELAY_PIN, OUTPUT);
    pinMode(RED_PIN, OUTPUT);
    pinMode(GREEN_PIN, OUTPUT);
    pinMode(BLUE_PIN, OUTPUT);
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    Serial.begin(9600);

    // Turn off everything initially
    digitalWrite(RELAY_PIN, LOW);
    digitalWrite(RED_PIN, HIGH);
    digitalWrite(GREEN_PIN, LOW);
    digitalWrite(BLUE_PIN, LOW);
}

void loop()
{
    unsigned long currentMillis = millis();

    // Read soil moisture per soilInterval
    static int soilMoisture = 0;
    if (currentMillis - lastSoilReading >= soilInterval)
    {
        lastSoilReading = currentMillis;
        soilMoisture = analogRead(SOIL_SENSOR_PIN);
        Serial.print("Soil moisture: ");
        Serial.println(soilMoisture);
    }

    // Button handling
    pinValue = digitalRead(BUTTON_PIN);
    delay(10); // Debounce

    if (buttonStatus != pinValue)
    {
        buttonStatus = pinValue;

        if (buttonStatus == LOW)
        {
            Serial.println("Button pressed!");
            digitalWrite(RED_PIN, LOW);
            digitalWrite(GREEN_PIN, HIGH);
            digitalWrite(RELAY_PIN, HIGH);
        }
        else
        {
            Serial.println("Button released!");
            digitalWrite(GREEN_PIN, LOW);
            digitalWrite(RED_PIN, HIGH);
            digitalWrite(RELAY_PIN, LOW);
        }
    }

    // Automatic watering logic
    if (soilMoisture >= 600 && !isPumping && (currentMillis - lastPumpRun >= pumpCooldown))
    {
        Serial.println("Soil is dry! Turning on pump.");
        digitalWrite(RELAY_PIN, HIGH);
        lastPumpRun = currentMillis;
        isPumping = true;
    }

    // Stop the pump after / per pumpRunTime
    if (isPumping && (currentMillis - lastPumpRun >= pumpRunTime))
    {
        Serial.println("Turning off pump.");
        digitalWrite(RELAY_PIN, LOW);
        isPumping = false;
    }
}