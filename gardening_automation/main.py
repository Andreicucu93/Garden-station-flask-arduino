import pandas as pd
import serial
import time
from datetime import datetime

# File paths
CSV_FILE = "/home/andrei/shared/GardenStation_log.csv"
EXCEL_FILE = "/home/andrei/shared/GardenStation_log.xlsx"

# Load existing data or create a new one
try:
    df = pd.read_csv(CSV_FILE)
    print("Loaded existing data.")
except FileNotFoundError:
    df = pd.DataFrame(columns=["Soil moisture", "Temp", "Humid", "Time", "Date", "Event"])
    print("No existing data found. Starting fresh.")

# Connect to Arduino (Change port if needed)
arduino = serial.Serial(port="/dev/ttyACM0", baudrate=9600, timeout=1)
time.sleep(2)  # Allow time for Arduino to initialize


# Function to log data
def log_data(moisture=None, temperature=None, humidity=None, event=""):
    global df
    now = datetime.now()

    # Create new row with default values as empty strings
    new_entry = pd.DataFrame([{
        "Soil moisture": moisture if moisture is not None else "",
        "Temp": temperature if temperature is not None else "",
        "Humid": humidity if humidity is not None else "",
        "Time": now.strftime("%H:%M:%S"),
        "Date": now.strftime("%Y-%m-%d"),
        "Event": event
    }])

    # Append to DataFrame
    df = pd.concat([df, new_entry], ignore_index=True)

    # Save to CSV
    df.to_csv(CSV_FILE, index=False)

    # Save to Excel
    df.to_excel(EXCEL_FILE, index=False)

    print("Entry added successfully!\n", df.tail(5))  # Show last 5 entries


print("Starting soil moisture monitoring... Press CTRL+C to stop.")

# Variables to store last sensor readings
last_moisture = None
last_temp = None
last_humid = None
last_logged_time = time.time()

try:
    while True:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode("utf-8").strip()
            print("Received:", line)

            # Soil moisture data
            if line.startswith("Soil Moisture:"):
                last_moisture = int(line.split(":")[1])

            # Temperature data
            elif line.startswith("Temp:"):
                last_temp = float(line.split(":")[1])

            # Humidity data
            elif line.startswith("Hum:"):
                last_humid = float(line.split(":")[1])

            # Log readings every 30 minutes (1800 sec)
            if last_moisture is not None and last_temp is not None and last_humid is not None:
                if time.time() - last_logged_time >= 1800:
                    log_data(last_moisture, last_temp, last_humid)
                    last_logged_time = time.time()

            # Log pump events
            elif line == "PUMP:TRIGGERED":
                log_data(event="Pump Triggered")

            elif line == "PUMP:START":
                log_data(event="Pump Started")

            elif line == "PUMP:STOP":
                log_data(event="Pump Stopped")

        time.sleep(1)  # Prevent CPU overload

except KeyboardInterrupt:
    print("\nLogging stopped. Data saved.")
    arduino.close()
