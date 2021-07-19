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


// Define Variables
WiFiClient wifiClient;
PubSubClient client(wifiClient);
IPAddress mqttServer(192, 168, 0, 102);
Adafruit_ADS1015 ads;     /* Use this for the 12-bit version */  
int16_t adc0;
float Current = 0;

// Define Functions
void ADC()
{
    adc0 = ads.readADC_SingleEnded(0);
    int average = 0;
    for (int i=0; i < 1000; i++) {
      average = average + adc0;
    }
    average = average/1000;
    Current = (average - 1659) * 0.0866;
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
  ads.setGain(GAIN_TWO);
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
  if (Current < 0) Current = 0;
  char charCurrent[] = "0.00" ; // convert Current float to string
  dtostrf(Current, 6, 1, charCurrent);
  // Once connected, publish an announcement...
  Serial.print("Publishing on " MQTT_PUBLISH_CHANNEL ": ");
  Serial.println(charCurrent);
  client.publish(MQTT_PUBLISH_CHANNEL, charCurrent);
  delay(SAMPLE_WINDOW);
} // END loop
