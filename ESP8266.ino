#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include <time.h>
#include "credentials.h"

const char *ssid = WIFI_SSID;
const char *password = WIFI_PASSWORD;

// MQTT Broker
const char *mqtt_broker = MQTT_BROKER;
const char *mqtt_topic = MQTT_TOPIC;
const char *mqtt_pub_topic = MQTT_PUB_TOPIC;
const char *mqtt_username = MQTT_USER;
const char *mqtt_password = MQTT_PASSWORD;
const int mqtt_port = MQTT_PORT;

const char *mqtt_fingerprint = MQTT_FINGERPRINT;

#define DHTPIN D5
#define DHTYPE DHT11
DHT dht(DHTPIN, DHTYPE);

WiFiClientSecure espClientSecure;
PubSubClient mqtt_client(espClientSecure);

char client_id_cstr[40];

void printHeapInfo() {
  Serial.printf("Free Heap: %u bytes\n", ESP.getFreeHeap());
}

void connectToWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  String mac = WiFi.macAddress();
  snprintf(client_id_cstr, sizeof(client_id_cstr), "esp8266-client-%s", mac.c_str());
}

void connectToMQTTBroker() {
  Serial.printf("Setting SHA1 fingerprint: %s\n", mqtt_fingerprint);
  espClientSecure.setFingerprint(mqtt_fingerprint);
  espClientSecure.setTimeout(5000);

  while (!mqtt_client.connected()) {
    Serial.printf("Connecting to MQTT broker %s:%d as %s...\n", mqtt_broker, mqtt_port, client_id_cstr);
    if (mqtt_client.connect(client_id_cstr, mqtt_username, mqtt_password)) {
      Serial.println("Connected to MQTT broker (TLS - Fingerprint Verified)");
      mqtt_client.subscribe(mqtt_topic);
    } else {
      Serial.print("MQTT connection failed, rc=");
      Serial.print(mqtt_client.state());
      Serial.println(" Retrying in 5s...");
      delay(5000);
    }
  }
}

void mqttCallback(char *topic, byte *payload, unsigned int length) {
  Serial.print("Message received [");
  Serial.print(topic);
  Serial.print("]: ");
  for (unsigned int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  Serial.println("\nBooting...");
  dht.begin();
  connectToWiFi();

  mqtt_client.setServer(mqtt_broker, mqtt_port);
  mqtt_client.setCallback(mqttCallback);
  mqtt_client.setBufferSize(128);
}

unsigned long lastPublishTime = 0;
const long publishInterval = 10000;

void loop() {
  if (!mqtt_client.connected()) {
    connectToMQTTBroker();
  }
  mqtt_client.loop();

  unsigned long currentMillis = millis();
  if (currentMillis - lastPublishTime >= publishInterval) {
    lastPublishTime = currentMillis;

    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    if (!isnan(temperature) && !isnan(humidity)) {
      StaticJsonDocument<96> doc;
      doc["temperature"] = temperature;
      doc["humidity"] = humidity;
      char payload[96];
      size_t n = serializeJson(doc, payload);

      Serial.print("Publishing: ");
      Serial.println(payload);
      if (!mqtt_client.publish(mqtt_pub_topic, payload, n)) {
        Serial.println("!!! Failed to publish message!");
      }
    } else {
      Serial.println("Failed to read from DHT sensor");
    }
  }
  delay(10);
}
