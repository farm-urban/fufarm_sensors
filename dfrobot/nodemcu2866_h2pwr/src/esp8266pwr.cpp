// https://github.com/esp8266/Arduino
// https://github.com/knolleary/pubsubclient/blob/master/examples/mqtt_basic/mqtt_basic.ino
#include <SPI.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_ADS1X15.h>
#include <Wire.h>

// Time in milliseconds - 5 minutes = 1000 * 60 * 5 = 300000
#define SAMPLE_WINDOW 5000 // 5 seconds for testing
#define SSID "Vertical Farm Pilot_EXT"
#define WIFI_PASSWORD "1106FaRm1028"
#define MQTT_CLIENT_NAME "h2Pwr"
#define MQTT_USER "mosquitto"
#define MQTT_PASSWORD "mosquitto"
#define MQTT_PUBLISH_CHANNEL "h2Pwr/STATUS"
#define BAUD_SPEED 9600
#define R1 9800 //for voltage divider
#define R2 1180 //for voltage divider

// Define Variables
WiFiClient wifiClient;
PubSubClient client(wifiClient);
IPAddress mqttServer(192, 168, 0, 102);
Adafruit_ADS1115 ads;     /* Use this for the 16-bit version */  
int16_t adc0;
int16_t adc1;
float current = 0;
float voltage = 0;
float adc0vout = 0;
float adc1vout = 0;
String mqttJson = "";

// Define Functions
void ADC()
{
    adc0 = ads.readADC_SingleEnded(0);  //adc0 is the current sensor
    adc1 = ads.readADC_SingleEnded(1);  //adc1 is the voltage divider to get fuel cell voltage
    int avgCurrent = 0;
    int avgVoltage = 0;
    for (int i=0; i < 1000; i++) {
      avgCurrent = avgCurrent + adc0;
      avgVoltage = avgVoltage + adc1;
    }
    avgCurrent = avgCurrent/1000;
    avgVoltage = avgVoltage/1000;
  //sorting out the current
    Serial.println(avgCurrent);
    adc0vout = avgCurrent * 0.00012476; //the voltage reading at adc0 (used for calibration with 12476micro volts per bit)
    Serial.print("adc0vout: ");
    Serial.println(adc0vout); 
    current = adc0vout * 85.2 - 144.1; // (-1.66v due to sensor measuring negative values) converting microvolts to amps
    Serial.print("Current: ");
    Serial.println(current);
    

  //sorting out the Voltage
  //  Serial.println(avgVoltage);
    adc1vout = avgVoltage * 0.00012476; //the voltage reading at adc1 used for calibration with 12476micro volts per bit
  //  Serial.print("adc1vout: ");
  //  Serial.println(adc1vout); 
    voltage = adc1vout / 0.1063; //0.1075 is r2/ (r1 + r2)
    Serial.print("Voltage: ");
    Serial.println(voltage);
//    voltage = avgVoltage * 0.00848; //3.3 is the voltage range of the nodeMCU and 65535 as the ADC is 16 bit
} // END ADC


void connectToWiFi()
{
  /* Explicitly set the ESP8266 to be a WiFi-client, otherwise, it by default,
    would try to act as both a client and an access-point and could cause
    network-issues with your other WiFi-devices on your WiFi-network. */
  WiFi.mode(WIFI_STA);

  int i = 0;
  while ( WiFi.status() != WL_CONNECTED )
  {
    WiFi.disconnect(); // https://forum.arduino.cc/t/mqtt-with-esp32-gives-timeout-exceeded-disconnecting/688723/6
    Serial.print("Wifi connecting to: ");
    Serial.println(SSID);
    WiFi.begin(SSID, WIFI_PASSWORD);
    delay(10000);
    i++;
    if ( i == 5 )
    {
      Serial.print("*** Restarting ESP on failed WIFI connect ***");
      ESP.restart();
    }
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
} // END connectToWiFi


void reconnectMQTT() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(MQTT_CLIENT_NAME, MQTT_USER, MQTT_PASSWORD)) {
      Serial.println("MQTT connected");
    } else {
        Serial.print("failed, rc=");
        Serial.print(client.state());
        Serial.println(" try again in 5 seconds");
        // Wait 5 seconds before retrying
        delay(5000);
    }
  }
} // END reconnectMQTT

//void callback(char* topic, byte* payload, unsigned int length) {
//  Serial.print("Message arrived [");
//  Serial.print(topic);
//  Serial.print("] ");
//  for (int i=0;i<length;i++) {
//    Serial.print((char)payload[i]);
//  }
//  Serial.println();
//}

void setup()
{
  Serial.begin(BAUD_SPEED);
  connectToWiFi();
  client.setServer(mqttServer, 1883);
//  client.setCallback(callback);

  // Allow the hardware to sort itself out
  delay(1500);

  Serial.println("Getting single-ended readings from AIN0..3");
  // ads1015.setGain(GAIN_TWOTHIRDS);  // 2/3x gain +/- 6.144V  1 bit = 3mV (default)
  // ads1015.setGain(GAIN_ONE);     // 1x gain   +/- 4.096V  1 bit = 2mV
  // ads1015.setGain(GAIN_TWO);     // 2x gain   +/- 2.048V  1 bit = 1mV
  // ads1015.setGain(GAIN_FOUR);    // 4x gain   +/- 1.024V  1 bit = 0.5mV
  // ads1015.setGain(GAIN_EIGHT);   // 8x gain   +/- 0.512V  1 bit = 0.25mV
  // ads1015.setGain(GAIN_SIXTEEN); // 16x gain  +/- 0.256V  1 bit = 0.125mV
  ads.setGain(GAIN_ONE);
  ads.begin();
} // END setup

void loop()
{
  if ( WiFi.status() != WL_CONNECTED ) {
    connectToWiFi();
  }
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();
  ADC(); //get sensor data
  // prepare data for MQTT
  if (current < 0.09) current = 0;
  if (voltage < 0.09) voltage = 0;
  mqttJson = "{\"current\":";
  mqttJson += String(current, 2);
  mqttJson += ",\"voltage\":";
  mqttJson += String(voltage, 2);
  mqttJson += "}";
  Serial.print("Publishing on " MQTT_PUBLISH_CHANNEL ": ");
  Serial.println(mqttJson); //used for debugging
  client.publish(MQTT_PUBLISH_CHANNEL, mqttJson.c_str()); 
  delay(SAMPLE_WINDOW);
} // END loop
