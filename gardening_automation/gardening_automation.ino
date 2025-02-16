#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <DHT_U.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define RED_PIN 5
#define GREEN_PIN 6
#define BLUE_PIN 7
#define BUTTON_PIN 2
#define RELAY_PIN A0
#define SOIL_SENSOR_PIN A1
#define DHTPIN 3
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);


Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

int buttonStatus = HIGH;
int pinValue;
unsigned long lastSoilReading = 0;
unsigned long lastPumpRun = 0;
const unsigned long soilInterval = 1500;
const unsigned long pumpRunTime = 10000;
const unsigned long pumpCooldown = 15000;
bool isPumping = false;

void setup()
{
    dht.begin();
    pinMode(SOIL_SENSOR_PIN, INPUT);
    pinMode(RELAY_PIN, OUTPUT);
    pinMode(RED_PIN, OUTPUT);
    pinMode(GREEN_PIN, OUTPUT);
    pinMode(BLUE_PIN, OUTPUT);
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    Serial.begin(9600);

    digitalWrite(RELAY_PIN, LOW);
    digitalWrite(RED_PIN, HIGH);
    digitalWrite(GREEN_PIN, LOW);
    digitalWrite(BLUE_PIN, LOW);

    // OLED Initialization
    if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C))
    {
        Serial.println(F("SSD1306 allocation failed"));
        for (;;)
            ;
    }

    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(10, 10);
    display.println("Soil Sensor Ready!");
    display.display();
    delay(2000);
}

void loop()
{
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();
    unsigned long currentMillis = millis();
    static int soilMoisture = 0;

    // Read soil moisture every interval
    if (currentMillis - lastSoilReading >= soilInterval)
    {
        lastSoilReading = currentMillis;
        soilMoisture = analogRead(SOIL_SENSOR_PIN);
        Serial.print("Soil Moisture:");
        Serial.println(soilMoisture);
        Serial.print("Temp:");
        Serial.println(temperature);
        Serial.print("Hum:");
        Serial.println(humidity);

        // Update OLED Display
        display.clearDisplay();

        // Display soil moisture
        display.setTextSize(2);
        display.setCursor(10, 10);
        display.println("Soil:");
        display.setCursor(80, 10);
        display.println(soilMoisture);

        // Display temperature
        display.setCursor(10, 35);
        display.setTextSize(1);
        display.println("Temp:");
        display.setCursor(80, 35);
        display.println(temperature);

        // Display humidity
        display.setCursor(10, 55);
        display.println("Hum:");
        display.setCursor(80, 55);
        display.println(humidity);

        display.display();
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
        Serial.println("PUMP:TRIGGERED");
        Serial.println("PUMP:START");
        digitalWrite(RELAY_PIN, HIGH);
        lastPumpRun = currentMillis;
        isPumping = true;
    }

    // Stop pump after pumpRunTime
    if (isPumping && (currentMillis - lastPumpRun >= pumpRunTime))
    {
        Serial.println("PUMP:STOP");
        digitalWrite(RELAY_PIN, LOW);
        isPumping = false;
    }
}