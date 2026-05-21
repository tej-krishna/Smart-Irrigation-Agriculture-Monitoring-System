# Smart Irrigation System 🌱

An IoT and AI-powered web application built with Django that allows farmers and government officials to monitor and manage agricultural irrigation in real-time.

## Features
- **Real-Time Dashboards:** Monitor water levels, soil pH, temperature, and humidity directly from IoT sensors.
- **AI Farming Assistant:** A built-in LLM chatbot powered by OpenRouter to answer any agronomy questions.
- **Interactive Visualizations:** Live generated charts powered by Matplotlib.
- **Multi-Role Access:** Beautiful, distinct interfaces for Farmers and Government administrators.
- **Modern UI/UX:** Responsive design powered by CSS Grid, smooth transitions, and glassmorphism.

## Requirements
- Python 3.10+
- Django 5.2+

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd project
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   A `.env` file is required to store your secrets. Create one in the root directory (where `manage.py` is located) with the following content:
   ```env
   SECRET_KEY=your_django_secret_key_here
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

5. **Apply Database Migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create a Superuser (For Government Access):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the Development Server:**
   ```bash
   python manage.py runserver
   ```
   Access the application in your browser at `http://127.0.0.1:8000`.

## Hardware / ESP32 Integration
The application listens for GET requests from microcontrollers (like the ESP32) at the following endpoint:
`http://<server-ip>:8000/esp/<device_id>/<water_level>/<ph>/<ldr>/<humidity>/<temp>/`

A complete starter code for the ESP32 is provided in the `code.txt` file in this repository.

### Hardware Pinout Guide
If using the sample `code.txt`, connect your sensors to the ESP32 as follows:
- **Water Level Sensor (Analog):** GPIO 32
- **pH Sensor (Analog):** GPIO 33
- **LDR / Light Sensor (Analog):** GPIO 34
- **Temperature/Humidity (Analog/DHT):** GPIO 35 & GPIO 36

### Flashing the ESP32
1. Open the Arduino IDE.
2. Install the **ESP32 Board Manager** if you haven't already (`Tools -> Board -> Boards Manager`).
3. Select your ESP32 board (`Tools -> Board -> ESP32 Dev Module`).
4. Copy the code from `code.txt` into the Arduino IDE.
5. Change the `ssid`, `password`, and `serverName` variables at the top of the script to match your WiFi credentials and your computer's local IP address.
6. Connect the ESP32 via USB and click **Upload**.
7. Open the Serial Monitor (115200 baud) to watch the sensor data get pushed to your Django server!
