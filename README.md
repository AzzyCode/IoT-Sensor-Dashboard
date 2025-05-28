# IoT Real-Time Sensor Dashboard

IoT monitoring system that collects environmental data from sensor and displays it through a web-based dashboard with real-time visualization. This project demonstrates full-stack IoT development, from embedded hardware programming to web application deployment.

## 🌟 Project Overview

This system monitors environmental conditions (temperature and humidity) using ESP8266 microcontrollers with DHT11 sensors, transmitting data wirelessly via MQTT protocol to a Raspberry Pi 4 server. The data is stored in a MariaDB database and displayed through a responsive Flask web application with real-time charts and user authentication.


## ✨ Key Features

- **Real-time sensor data collection** from multiple ESP8266 nodes
- **Wireless communication** using secure MQTT over TLS
- **Live data visualization** with interactive Chart.js graphs
- **User authentication system** with secure login/logout
- **Responsive web interface** optimized for desktop and mobile
- **Automatic data logging** to database with error handling
- **Network-accessible dashboard** for remote monitoring
- **SSL/TLS encryption** for secure web communications

## 🛠️ Technologies Used

### Hardware
- **ESP8266 WiFi microcontrollers** - Sensor nodes
- **DHT11 sensors** - Temperature and humidity measurement
- **Raspberry Pi 4** - Server and database host


## 🏃‍♂️ Running the Project

1. **Start the MQTT listener:**
   ```bash
   python3 MQTT_server.py
   ```

2. **Launch the web application:**
   ```bash
   python3 app.py
   ```

3. **Access the dashboard:**
   - Open browser to `https://[raspberry-pi-ip]:5001`
   - Create user account or login
   - View real-time sensor data and graphs

4. **Power on ESP8266 sensors:**
   - Sensors will automatically connect and start transmitting data
   - Data updates every 10 seconds

## 📊 System Architecture

```
[ESP8266 + DHT11] --WiFi--> [MQTT Broker] ---> [Python MQTT Client]
                                                       |
[Web Dashboard] <--HTTP/HTTPS-- [Flask App] <-- [MariaDB Database]
```

## 🎯 Challenges & Learning Outcomes

**Technical Challenges Solved:**
- Implemented secure MQTT communication with TLS certificates
- Handled real-time data synchronization between system components
- Designed UI with live chart updates without page refresh
- Managed network configuration for cross-device communication

**Key Learning:**
- IoT system architecture and communication protocols
- Full-stack web development with real-time features
- Database design for time-series sensor data
- Network security implementation in IoT environments
- Embedded programming and sensor integration


## 🤝 Project Context

This project was developed as part of an international university collaboration, demonstrating cross-cultural teamwork and technical knowledge sharing in IoT system development.

## 📝 License

This project is available under the MIT License. See LICENSE file for details.

---
