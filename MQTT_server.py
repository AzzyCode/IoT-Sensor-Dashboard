import paho.mqtt.client as paho
from paho import mqtt
import json
from datetime import datetime
import os
import ssl
import pymysql
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Database Configuration ---
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")

# --- MQTT Configuration ---
MQTT_BROKER_HOST = os.environ.get("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.environ.get("MQTT_BROKER_PORT"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC")
MQTT_USERNAME = os.environ.get("MQTT_USERNAME")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")
MQTT_CLIENT_ID = os.environ.get("MQTT_CLIENT_ID")

CA_CERT_PATH = os.environ.get("CA_CERT_PATH")
LOG_FILE = os.environ.get("LOG_FILE")


def get_db_connection():
    try:
        conn = pymysql.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        logger.info("Database connection established.")
        return conn
    except pymysql.MySQLError as e:
        logger.error(f"Database connection error: {e}")
        return None


def on_connect(client, userdata, flags, rc, properties=None):
    """Callback when the client connects to the MQTT broker."""
    if rc == 0:
        logger.info(f"Connected successfully to MQTT Broker {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
        # Subscribe to the topic upon connection
        client.subscribe(MQTT_TOPIC, qos=1)
    else:
        logger.error(f"Failed to connect to MQTT Broker, return code {rc}")
        if rc == 5: logger.error("Authentication failure (check username/password)")
        if rc == -1: logger.error("Connection refused (check host/port, broker rules)")

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    """Callback when the client successfully subscribes."""
    logger.info(f"Subscribed to topic '{MQTT_TOPIC}' with QoS: {granted_qos}")

def on_message(client, userdata, msg):
    topic = msg.topic
    db_conn = None 
    try:
        payload_str = msg.payload.decode("utf-8")
        logger.info(f"Received message on topic '{topic}': {payload_str}")

        data = json.loads(payload_str)
        append_to_json_log(LOG_FILE, data)
        
        temperature = data.get('temperature')
        humidity = data.get('humidity')
        
        if temperature is not None and humidity is not None:
            db_conn = get_db_connection()
            if db_conn:
                try:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    with db_conn.cursor() as cursor:
                        sql = "INSERT INTO sensor_data (datetime, temperature, humidity) VALUES (%s, %s, %s)"
                        cursor.execute(sql, (timestamp, temperature, humidity))
                    logger.info(f"Inserted data into database: T={temperature}, H={humidity}")
                except pymysql.MySQLError as e:
                     logger.error(f"Database error during insert: {e}")
                finally:
                    db_conn.close()
            else:
                logger.error("Could not get database connection. Data not saved to DB.")
        else:
            logger.warning(f"Received message missing temperature or humidity: {payload_str}. Not saved to DB.")

    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON payload from topic '{topic}': {payload_str}")
    except KeyError as e:
         logger.error(f"Missing key in JSON data: {e} - Payload: {payload_str}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in on_message: {e}")


def append_to_json_log(filename, new_data):
    """Appends a new data record to a JSON file containing a list."""
    records = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                content = f.read()
                if content:
                    records = json.loads(content)
                    if not isinstance(records, list):
                        logger.warning(f"Warning: Log file '{filename}' does not contain a valid JSON list. Starting fresh.")
                        records = []
                else:
                     records = [] 
        except json.JSONDecodeError:
            logger.warning(f"Warning: Could not decode JSON from '{filename}'. Starting fresh.")
            records = []
        except Exception as e:
            logger.error(f"Error reading log file '{filename}': {e}. Starting fresh.")
            records = []

    records.append(new_data)

    try:
        with open(filename, 'w') as f:
            json.dump(records, f, indent=4)
        logger.info(f"Successfully appended data to {filename}")
    except Exception as e:
        logger.error(f"Error writing to log file '{filename}': {e}")


def on_disconnect(client, userdata, rc, properties=None):
    """Callback for when the client disconnects."""
    logger.info(f"Disconnected from MQTT Broker with result code: {rc}")
    if rc != 0:
        logger.warning("Unexpected disconnection.")


mqtt_client = paho.Client(client_id=MQTT_CLIENT_ID, protocol=paho.MQTTv311)

mqtt_client.on_connect = on_connect
mqtt_client.on_subscribe = on_subscribe
mqtt_client.on_message = on_message
mqtt_client.on_disconnect = on_disconnect

mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

try:
    logger.info(f"Setting up TLS using CA certificate: {CA_CERT_PATH}")
    mqtt_client.tls_set(
            ca_certs=CA_CERT_PATH,
            certfile=None,
            keyfile=None,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2
    )
except FileNotFoundError:
    logger.error(f"Error: CA certificate file not found at {CA_CERT_PATH}")
    exit()
except Exception as e:
    logger.error(f"Error setting up TLS: {e}")
    exit()
    

logger.info(f"Attempting connection to MQTT Broker {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
try:
    mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
except Exception as e:
    logger.error(f"Error connecting to MQTT Broker: {e}")
    logger.error("Please ensure the MQTT broker is running and accessible.")

logger.info("Starting MQTT listener loop... Press Ctrl+C to exit.")
try:
    mqtt_client.loop_forever()
except KeyboardInterrupt:
    logger.info("Disconnecting from MQTT Broker...")
    mqtt_client.disconnect()
    logger.info("Script finished.")
