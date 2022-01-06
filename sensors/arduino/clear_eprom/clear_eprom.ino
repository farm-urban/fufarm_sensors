#include <EEPROM.h>
#define KVALUEADDR 0x00
void setup(){
    for(byte i = 0;i< 8; i++   ){
      EEPROM.write(KVALUEADDR+i, 0xFF);
    }
}
void loop(){
}
