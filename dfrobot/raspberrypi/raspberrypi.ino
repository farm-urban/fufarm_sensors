#include <ArduinoJson.h>
// Sensors
#include "DHTesp.h"
#include <OneWire.h>
#include "DFRobot_EC.h"
#include "DFRobot_PH.h"

// Time in milliseconds - 5 minutes = 1000 * 60 * 5 = 300000
#define SAMPLE_WINDOW 300000
#define SAMPLE_WINDOW 5000

// Analog Inputs
int lightPin = A0;
int co2Pin = A1;
int ecPin = A2;
int phPin = A3;

// Digital Inputs
int dhtPin = 2; // Temp and Humidity
int DS18S20_Pin = 3; // Wet temperature
int SEN0217_Pin = 4; // Flow sensor

// Data collecting strucutures
DHTesp dht; // Temperature and Humidity
OneWire ds(DS18S20_Pin); // Wet temperature chip i/o
DFRobot_EC ecProbe; // EC probe
DFRobot_PH phProbe; // pH probe
volatile int pulseCount; // Flow Sensor

#define JSON_DOC_SIZE 200;
const int jsize=JSON_DOC_SIZE;
StaticJsonDocument<jsize> doc;

float getEC(int ecPin, float temperature){
   float voltage = analogRead(ecPin)/1024.0*5000;
   return ecProbe.readEC(voltage,temperature);
}

int getLight(int lightPin){
  int light = analogRead(lightPin);
  return light;
}

float getPH(int phPin, float temperature){
   float voltage = analogRead(phPin)/1024.0*5000;
   return phProbe.readPH(voltage,temperature);
}

int getCO2(int analogPin){
    // Calculate CO2 concentration in ppm
    int sensorValue = analogRead(analogPin);
    float voltage = sensorValue*(5000/1024.0);
    if(voltage == 0)
    {
      // Error
      return -1.0;
    }
    else if(voltage < 400)
    {
      // Preheating
      return -2.0;
    }
    else
    {
      int voltage_diference=voltage-400;
      return (int) (voltage_diference*50.0/16.0);
    }
}

float getTempWet(){
  //returns the temperature from one DS18S20 in DEG Celsius
  byte data[12];
  byte addr[8];

  if ( !ds.search(addr)) {
      //no more sensors on chain, reset search
      ds.reset_search();
      return -1000;
  }

  if ( OneWire::crc8( addr, 7) != addr[7]) {
      //Serial.println("CRC is not valid!");
      return -1001;
  }

  if ( addr[0] != 0x10 && addr[0] != 0x28) {
      //Serial.print("Device is not recognized");
      return -1002;
  }

  ds.reset();
  ds.select(addr);
  ds.write(0x44,1); // start conversion, with parasite power on at the end

  byte present = ds.reset();
  ds.select(addr);    
  ds.write(0xBE); // Read Scratchpad
  
  for (int i = 0; i < 9; i++) { // we need 9 bytes
    data[i] = ds.read();
  }
  
  ds.reset_search();
  
  byte MSB = data[1];
  byte LSB = data[0];

  float tempRead = ((MSB << 8) | LSB); //using two's compliment
  float TemperatureSum = tempRead / 16;
  
  return TemperatureSum;
}

void flowPulse()
{
  pulseCount += 1;
}


float getFlow()
/* From YF-S201 manual:
    Pluse Characteristic:F=7Q(L/MIN).
    2L/MIN=16HZ 4L/MIN=32.5HZ 6L/MIN=49.3HZ 8L/MIN=65.5HZ 10L/MIN=82HZ
    sample_window is in seconds, so hz is pulseCount / SAMPLE_WINDOW
 */
{
  float hertz = (float) (pulseCount * 1000.0 ) / SAMPLE_WINDOW;
  Serial.print("Pulse Count: ");
  Serial.println(pulseCount);
  pulseCount = 0; // reset flow counter
  return hertz / 7.0;
}

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    Serial.begin(9600);
    dht.setup(dhtPin, DHTesp::DHT22);
    analogReference(DEFAULT); // Set the default voltage of the reference voltage
    attachInterrupt(digitalPinToInterrupt(SEN0217_Pin), flowPulse, RISING);
    pulseCount = 0;
    ecProbe.begin();
    phProbe.begin();
}


void loop() {
    //Serial.println("Starting main loop");
    //digitalWrite(LED_BUILTIN, HIGH);
    TempAndHumidity th = dht.getTempAndHumidity();
    float t = th.temperature;
    float h = th.humidity;
    int co2 = getCO2(co2Pin);
    float twet = getTempWet();
    float ec = getEC(ecPin, twet);
    float ph = getPH(phPin, twet);
    float flow = getFlow();
    int light = getLight(lightPin);

    // json
    doc["tempair"] = t;
    doc["humidity"] = h;
    doc["tempwet"] = twet;
    doc["co2"] = co2;
    doc["cond"] = ec; // For unfathomable reasons influxdb won't accept ec as a name. WTF?!?!?!@@
    doc["ph"] = ph;
    doc["flow"] = flow;
    doc["light"] = light;
    serializeJson(doc, Serial);

    delay(SAMPLE_WINDOW);
}
