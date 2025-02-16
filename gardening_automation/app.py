from flask import Flask, jsonify, render_template, url_for
import pandas as pd
import serial
import time
import threading
import matplotlib.pyplot as plt
import os
from datetime import datetime

app = Flask(__name__, template_folder="templates")

# File paths
CSV_FILE = "/home/andrei/shared/GardenStation_log.csv"
STATIC_FOLDER = "static"
SOIL_GRAPH_PATH = os.path.join(STATIC_FOLDER, "soil_moisture_graph.png")
TEMP_HUMIDITY_GRAPH_PATH = os.path.join(STATIC_FOLDER, "temp_humidity_graph.png")

def generate_graphs():
    try:
        # Read the CSV file
        df = pd.read_csv(CSV_FILE)
        print(f"🔍 Original CSV Columns: {df.columns}")

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        print(f"🔄 Normalized Columns: {df.columns}")

        # Rename columns to a consistent format
        df.rename(columns={
            "soil_moisture": "Soil Moisture",
            "temp": "Temperature",
            "humid": "Humidity",
            "date": "Date",
            "time": "Time"
        }, inplace=True)

        print(f"✅ Final Columns: {df.columns}")

        # Ensure required columns exist
        required_columns = {"Soil Moisture", "Temperature", "Humidity", "Date", "Time"}
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            raise ValueError(f"⚠️ Missing required columns: {missing_columns}")

        # Convert sensor data to numeric values
        df["Soil Moisture"] = pd.to_numeric(df["Soil Moisture"], errors="coerce")
        df["Temperature"] = pd.to_numeric(df["Temperature"], errors="coerce")
        df["Humidity"] = pd.to_numeric(df["Humidity"], errors="coerce")
        df.dropna(subset=["Soil Moisture", "Temperature", "Humidity"], inplace=True)

        # Convert Date & Time into full timestamp
        df["Timestamp"] = pd.to_datetime(df["Date"] + " " + df["Time"], errors="coerce")
        df.dropna(subset=["Timestamp"], inplace=True)

        # Group data by day (daily averages)
        df["Date"] = df["Timestamp"].dt.date
        daily_avg = df.groupby("Date")[["Soil Moisture", "Temperature", "Humidity"]].mean()

        # Debugging step: Print processed data
        print(f"✅ Daily averages:\n{daily_avg}")

        if daily_avg.empty:
            print("⚠️ No data to plot.")
            return  # Stop if no data

        # Create "static" folder if it doesn't exist
        os.makedirs(STATIC_FOLDER, exist_ok=True)

        # **Graph 1: Soil Moisture**
        plt.figure(figsize=(10, 5))
        plt.plot(daily_avg.index, daily_avg["Soil Moisture"], label="Soil Moisture", marker="o", linestyle="-", color="blue")
        plt.xlabel("Date")
        plt.ylabel("Soil Moisture")
        plt.title("Daily Average Soil Moisture")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(SOIL_GRAPH_PATH)
        plt.close()

        # **Graph 2: Temperature & Humidity**
        plt.figure(figsize=(10, 5))
        plt.plot(daily_avg.index, daily_avg["Temperature"], label="Temperature (°C)", marker="s", linestyle="--", color="red")
        plt.plot(daily_avg.index, daily_avg["Humidity"], label="Humidity (%)", marker="^", linestyle="-.", color="green")
        plt.xlabel("Date")
        plt.ylabel("Values")
        plt.title("Daily Average Temperature & Humidity")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(TEMP_HUMIDITY_GRAPH_PATH)
        plt.close()

        print("✅ Graphs successfully generated!")

    except Exception as e:
        print(f"⚠️ Error generating graphs: {e}")


# Ensure the CSV file exists
try:
    df = pd.read_csv(CSV_FILE)
    print("📂 Loaded existing data.")
except FileNotFoundError:
    df = pd.DataFrame(columns=["Timestamp", "Soil Moisture", "Temperature", "Humidity"])
    df.to_csv(CSV_FILE, index=False)
    print("🆕 No existing data found. Created a new CSV file.")


try:
    arduino = serial.Serial(port="/dev/ttyACM0", baudrate=9600, timeout=1)
    time.sleep(2)  # Allow time for Arduino to initialize
except Exception as e:
    print("⚠️ Error connecting to Arduino:", e)
    arduino = None

latest_data = {"soil_moisture": 0, "temperature": 0, "humidity": 0}


@app.route('/')
def index():
    """ Renders the main page with both graphs. """
    generate_graphs()
    return render_template(
        "index.html",
        soil_graph_url=url_for('static', filename='soil_moisture_graph.png'),
        temp_humidity_graph_url=url_for('static', filename='temp_humidity_graph.png')
    )


@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(latest_data)


# Function to read data from Arduino in a background thread
serial_lock = threading.Lock()


# Global variable to store the last time data was logged
last_logged_time = None

def read_arduino():
    global latest_data, arduino, last_logged_time
    while True:
        try:
            with serial_lock:  # Prevent multiple accesses
                if arduino is None or not arduino.is_open:
                    print("⚠️ Reconnecting to Arduino...")
                    arduino = serial.Serial(port="/dev/ttyACM0", baudrate=9600, timeout=1)
                    time.sleep(2)  # Give time to reconnect

                if arduino.in_waiting > 0:
                    line = arduino.readline().decode("utf-8").strip()
                    print("📥 Received:", line)

                    if line.startswith("Soil Moisture:"):
                        latest_data["soil_moisture"] = int(line.split(":")[1])
                    elif line.startswith("Temp:"):
                        latest_data["temperature"] = float(line.split(":")[1])
                    elif line.startswith("Hum:"):
                        latest_data["humidity"] = float(line.split(":")[1])

                    # Get the current time
                    now = datetime.now()

                    # Only log if at least 1 hour has passed since last logged time
                    if last_logged_time is None or (now - last_logged_time).total_seconds() >= 3600:
                        last_logged_time = now  # Update last logged time

                        # Save data to CSV
                        with open(CSV_FILE, "a") as f:
                            timestamp_time = now.strftime("%H:%M:%S")
                            timestamp_date = now.strftime("%-m/%-d/%Y")
                            f.write(f"{latest_data['soil_moisture']},{latest_data['temperature']},{latest_data['humidity']},{timestamp_time},{timestamp_date}")

                        print("✅ Data logged to CSV")

                        # Generate new graphs
                        generate_graphs()

        except serial.SerialException as e:
            print("⚠️ Serial error:", e)
            arduino = None  # Reset Arduino object to attempt reconnection
            time.sleep(5)  # Wait before retrying



# Start Arduino thread
if arduino:
    threading.Thread(target=read_arduino, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)