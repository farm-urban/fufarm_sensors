#include <ArduinoJson.h>
// Sensors
#include "DHTesp.h"
#include <OneWire.h>
#include "DFRobot_EC.h"
#include "DFRobot_PH.h"

// Time in milliseconds
#define SAMPLE_WINDOW 5000

// Analog Inputs
int co2Pin = A0;
int ecPin = A1;
int phPin = A2;
// Digital Inputs
int dhtPin = 2;
int DS18S20_Pin = 3;


// Temperature and Humidity
DHTesp dht;
// Wet temperature chip i/o
OneWire ds(DS18S20_Pin);
// EC probe
DFRobot_EC ec_probe;
// pH probe
DFRobot_PH ph_probe;

#define JSON_DOC_SIZE 200;
const int jsize=JSON_DOC_SIZE;
StaticJsonDocument<jsize> doc;


float getPH(int phPin, float temperature){
   float voltage = analogRead(phPin)/1024.0*5000;
   return ph_probe.readPH(voltage,temperature);
}


float getEC(int ecPin, float temperature){
   float voltage = analogRead(ecPin)/1024.0*5000;
   return ec_probe.readEC(voltage,temperature);
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

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    Serial.begin(9600);
    dht.setup(dhtPin, DHTesp::DHT22);
    // Set the default voltage of the reference voltage
    analogReference(DEFAULT);
    ec_probe.begin();
    ph_probe.begin();
}


void loop() {
    //digitalWrite(LED_BUILTIN, HIGH);
    TempAndHumidity th = dht.getTempAndHumidity();
    float t = th.temperature;
    float h = th.humidity;
    int co2 = getCO2(co2Pin);
    float twet = getTempWet();
    float ec = getEC(ecPin, twet);
    float ph = getPH(phPin, twet);

    // json
    doc["temperature"] = t;
    doc["humidity"] = h;
    doc["temperature_wet"] = twet;
    doc["co2"] = co2;
    doc["ec"] = ec;
    doc["ph"] = ph;
    serializeJson(doc, Serial);

    delay(SAMPLE_WINDOW);
}


