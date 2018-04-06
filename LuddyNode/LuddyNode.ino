// example code for sending password to Pi
// for auto-registration

#include "NodeSerial.h"
#include "Behaviours.h"

// Message codes
#define TEST_LED_PIN_AND_RESPOND 0x00
#define AUDIO_START_RECORDING 0x02
#define AUDIO_STOP_RECORDING 0x03
#define AUDIO_START_PLAYING 0x04
#define AUDIO_STOP_PLAYING 0x05
#define FADE_ACTUATOR_GROUP 0x06
#define IR_TRIGGER 0x07

int frame_duration = 10; //milliseconds

int led_pin = 13;

static uint8_t teensyID[8];
uint8_t my_id_bytes[3] = {0x00,0x00,0x00};
long int my_id;

NodeSerial serial_comm;
Behaviours behaviours(frame_duration);

void setup() {


  read_teensyID();

  pinMode(led_pin, OUTPUT);
  serial_comm.Register(my_id_bytes);

  behaviours.start_IR_SENSING();
  
}

void loop() {


  // this loops starts running after the node registers
  
  //digitalWrite(led_pin, HIGH);

  // check for IR triggers, send message back to Pi when triggered
  for (uint8_t ir = 0; ir < behaviours.IR_num_sensors; ir++){
    if (behaviours.IR_triggered[ir]){
      uint8_t ir_num[1] = {ir}; 
      serial_comm.SendMessage(IR_TRIGGER, ir_num, 1);
      behaviours.IR_triggered[ir] = false;
    }
  }

  // check for incoming serial messages and act upon them
  if (serial_comm.CheckMessage()){ // returns 1 if message found, 0 otherwise
    if (serial_comm.last_code_received_ == TEST_LED_PIN_AND_RESPOND){
      uint8_t num_blinks = serial_comm.last_data_received_[0];
      uint8_t test_data[4] = {4,0,0,1};
      behaviours.start_TEST_LED_PIN(num_blinks);
      serial_comm.SendMessage(TEST_LED_PIN_AND_RESPOND, test_data, 4);
    }

    if (serial_comm.last_code_received_ == FADE_ACTUATOR_GROUP){
      // each actuator takes 5 bytes to control
      // <pin><start><end><time_hi><time_lo>
      uint8_t num_actuators = serial_comm.last_data_length_/5;
      uint8_t pins[num_actuators]; 
      uint8_t start_values[num_actuators]; 
      uint8_t end_values[num_actuators]; 
      int fade_times[num_actuators];
      for (int a = 0; a < serial_comm.last_data_length_ ; a = a + 5){
        pins[a] = serial_comm.last_data_received_[a]; // first byte is pin
        start_values[a] = serial_comm.last_data_received_[a+1]; // second byte is starting value
        end_values[a] = serial_comm.last_data_received_[a+2]; // third byte is starting value
        fade_times[a] = (serial_comm.last_data_received_[a+3] << 8) + serial_comm.last_data_received_[a+4]; 
        // fourth byte is time hi, fifth byte is time lo
        // fade time in milliseconds = (hi << 8) + lo
      }
      behaviours.start_FADE_ACTUATOR_GROUP(pins, start_values, end_values, fade_times, num_actuators);
    }
  }
  
  
  behaviours.loop();

}


// Code to read the Teensy ID
void read_EE(uint8_t word, uint8_t *buf, uint8_t offset) {
  noInterrupts();
  FTFL_FCCOB0 = 0x41;             // Selects the READONCE command
  FTFL_FCCOB1 = word;             // read the given word of read once area

  // launch command and wait until complete
  FTFL_FSTAT = FTFL_FSTAT_CCIF;
  while (!(FTFL_FSTAT & FTFL_FSTAT_CCIF));
  *(buf + offset + 0) = FTFL_FCCOB4;
  *(buf + offset + 1) = FTFL_FCCOB5;
  *(buf + offset + 2) = FTFL_FCCOB6;
  *(buf + offset + 3) = FTFL_FCCOB7;
  interrupts();
}

long int read_teensyID() {
  read_EE(0xe, teensyID, 0); // should be 04 E9 E5 xx, this being PJRC's registered OUI
  read_EE(0xf, teensyID, 4); // xx xx xx xx
  my_id = (teensyID[5] << 16) | (teensyID[6] << 8) | (teensyID[7]);
  my_id_bytes[0] = teensyID[5];
  my_id_bytes[1] = teensyID[6];
  my_id_bytes[2] = teensyID[7];
  return my_id;
}
