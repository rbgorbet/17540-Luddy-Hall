/*
* NodeSerial.cpp - Library for Communication Protocol between Raspberry Pi and Node
* created By Adam Francey March 13, 2018
* Modified from usb_serial_comm.cpp created By Adam Francey, Kevin Lam, July 5, 2017
* Released for Luddy Hall 2018
* Philip Beesley Architect Inc. / Living Architecture Systems Group
*
* Message Format (see related doc [WIP] for details)
* where <value> is the value represented as a byte:
* <SOM1><SOM2><TeensyId1><TeensyId2><TeensyId3><total number of bytes in message><code><data1>...<dataN><EOM1><EOM2>
*/

#include <Arduino.h>
#include <stdint.h>
#include "NodeSerial.h"

NodeSerial::NodeSerial(){
  Serial.begin(57600);
}

NodeSerial::NodeSerial(int baud_rate){
  Serial.begin(baud_rate);
}

NodeSerial::~NodeSerial(){}

void NodeSerial::SendMessage(uint8_t code){
  // Send SOM
  for (int i = 0; i < NUM_SOM; i++){
    Serial.write(SOM[i]);
  }

  // Send TeensyID
  for (int i = 0; i < NUM_ID; i++){
    Serial.write(ID[i]);
  }

  // Send message length
  //                 SOM       ID       length   code  EOM
  uint8_t message_length = NUM_SOM + NUM_ID + 1      + 1   + NUM_EOM;
  Serial.write(message_length);

  // Send code
  Serial.write(code);

  // Send EOM
  for (int i = 0; i < NUM_EOM; i++){
    Serial.write(EOM[i]);
  }

}

void NodeSerial::Register(uint8_t my_id_bytes[]){

  while (initialized == false){

    // send password
    for (int i = 0; i < password_length; i++){
      Serial.write(password[i]);
    }

    // delay okay to use here
    // it is fine to use before the sculpture initializes
    delay(100);

    // check serial port for password sequence
    // this means the Raspberry Pi has recognized the Teensy
    bool eligible = true;
    bool password_received = false;
    if (Serial.available() > password_length - 1){
      for (int i = 0; i < password_length; i++){
        if (Serial.read() != password[i]){
          eligible = false;
        }
      }
    
    } else {
      eligible = false;
    }
  
    if (eligible){
      password_received = true;
    }
    initialized = password_received;
  }

  // wait for Raspberry Pi to flush its buffer
  delay(500);

  //send Teensy ID bytes
  Serial.write(my_id_bytes[0]);
  Serial.write(my_id_bytes[1]);
  Serial.write(my_id_bytes[2]);

  // let NodeSerial know what the id is
  ID[0] = my_id_bytes[0];
  ID[1] = my_id_bytes[1];
  ID[2] = my_id_bytes[2];
}


void NodeSerial::SendMessage(uint8_t code, uint8_t data[], uint8_t data_length){

    // Send SOM
    for (int i = 0; i < NUM_SOM; i++){
        Serial.write(SOM[i]);
    }

    // Send TeensyID
    for (int i = 0; i < NUM_ID; i++){
        Serial.write(ID[i]);
    }

    // Send data length
    Serial.write(data_length);

    // Send code
    Serial.write(code);
    
    // Send data
    for (uint8_t i = 0; i < data_length; i++){
        Serial.write(data[i]);
    }

    // Send EOM
    for (int i = 0; i < NUM_EOM; i++){
        Serial.write(EOM[i]);
    }

}


// CheckMessage
// Reads the serial port for an incoming sequence of bytes
// if sequence follows requirements of a message defined in docs, returns 1 and
// updates the following NodeSerial members:
// last_data_length, last_code_received, last_data_received, message_waiting
// if requirements fail, returns 0
bool NodeSerial::CheckMessage(){

  message_waiting_ = 0;

  //if (Serial.available()>=MESSAGE_LENGTH){
  if (Serial.available()>NUM_SOM + 4){ // at least 7 bytes for SOM, ID, length, code

    // Teensy ID
    uint8_t t1;
    uint8_t t2;
    uint8_t t3;

    // modifiers
    uint8_t data_length;
    uint8_t code;

    // check for SOM (bytes 0-1)
    // we are expecting SOM bytes in sequence (currently: {0xff,0xff})
    for (int s = 0; s < NUM_SOM; s++){
      if (Serial.read() != SOM[s]){
        // Fail: SOM byte missing
        // So CheckMessage fails (no message found) and we stop reading serial port
        return 0;
      }
    }
    // if we make it here, we have found all SOM bytes

    // Teensy ID (bytes 2-4)
    t1 = Serial.read();
    t2 = Serial.read();
    t3 = Serial.read();

    // data_length (byte 5)
    data_length = Serial.read();

    // command/code (byte 6)
    code = Serial.read();

    // SOM (2 bytes), Teensy ID (3 bytes), message length (1 byte), code (1 byte) should take up 7 bytes
    // we are now expecting num_bytes_to_receive more bytes (including EOM)
    uint8_t data[data_length];

    if (Serial.available()>data_length+1){ // at least enough bytes for data and EOM

      for (uint8_t i = 0; i < data_length; i++){
        // read in data bytes
        data[i] = Serial.read();
      }
  
      // check for EOM
      for (int e = 0; e < NUM_EOM; e++){
        if (Serial.read() != EOM[e]){
          // Fail: EOM byte missing
          // something went wrong: num_bytes_in_message tells us to expect EOM here but we didn't find it
          // CheckMessage fails, stop reading serial port
          // bytes read up until this point will be discarded
          return 0;
        }
      }
      // If we make it here, we have found all EOM bytes
      
      // Success: Full message found
      // update class members
      // note: this will be overwritten on the next message successfully recieved
      last_data_length_ = data_length;
      last_code_received_ = code;
      for (int i = 0; i < data_length; i++){
        last_data_received_[i] = data[i];
      }
      message_waiting_ = 1;
      return 1;
    } else {
      //Fail: not enough bytes
      return 0;
    }



  } else {
    // Fail: not enough bytes
    return 0;
  }
}
