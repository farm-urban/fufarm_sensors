#include "DHTesp.h"
#include <OneWire.h>
#include <ArduinoJson.h>

#define JSON_DOC_SIZE 200;

int dhtPin = 2;
int co2Pin = A0;
int DS18S20_Pin = 3;

//Temperature and Humidity
DHTesp dht;
//Temperature chip i/o
OneWire ds(DS18S20_Pin);  // on digital pin 2

//StaticJsonDocument<JSON_DOC_SIZE> doc;
StaticJsonDocument<200> doc;

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
}


void loop() {
    String out;
    digitalWrite(LED_BUILTIN, HIGH);
    delay(1000);

    TempAndHumidity m = dht.getTempAndHumidity();
    float t = m.temperature;
    float h = m.humidity;
    int co2 = getCO2(co2Pin);
    float twet = getTempWet();
    out += "T: " + String(t);
    out += " | H: " + String(h);
    out += " | CO2: " + String(co2);
    out += " | T_wet: " + String(twet);
    Serial.println(out);

    //json
    doc["temperature"] = t;
    doc["humidity"] = h;
    doc["temperature_wet"] = twet;
    doc["co2"] = co2;
    serializeJson(doc, Serial);

    digitalWrite(LED_BUILTIN, LOW);
    delay(1000);
}


