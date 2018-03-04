/* 
 * Living Architecture Systems
 * Testing code for system behaviour and "Frame"
 * test code March 02 Amber Ma 
 * 
 * There will be two system behaviours right now
 * LED sequence local and neighbour 
 * Moth vibration local 
*/

// Macro for serial communication message 
#define SOM 0xff
#define ACTIVEIR 0x02

// Macro for behaviour name 
#define LEDSEQUENCE 0x10

const long FRAMELENGHT = 6;
unsigned long previousTime = 0;

int LED_sequence_frame_count = 0;
bool LED_sequence_triggered = false;
int LED_sequence_frame_max = 6; // the frame lenght of the behaviour 

int NC_with_sensor = {245689,123546};
int NC_no_sensor = {1419710,236467}; 
long int myID; 
//int ncType = {2,1}; // 1 = NC with IR 
                      // 2 = NC no IR 
//int behaviour_frame_count = {0,0}; // [0] = LED Sequence; [1] = moth 
//bool behaviuor_on = {0,0};
int LED_frame_count = 0;
bool LED_behaviour_on = false;

int ledPin = {25,32,6,21,26,31}; // P1
int mothPin = {9,10,22,23,29,30}; //P2
int irPin = {A0,A17,A13}; 

// Teensy ID
// filled with read_EE(), read_teensyID()
static uint8_t teensyID[8];
long int myID;
int myType; 

// Sets for IR 
int ir_threashold = 300;
bool ir_activated = {0,0,0};
unsigned long ir_activated_time = {0,0,0};
int ir_value = {0,0,0}; 

// Message from Pi 
byte incomingByte;
byte incomingMsg;

// Message to Pi 
bool ir_triggering_sendMesg = false;

/**************************************************************/
// Code to read the Teensy ID 
void read_EE(uint8_t word, uint8_t* mac, uint8_t offset) {
  noInterrupts();
  
  // To understand what's going on here, see. 
  // "Kinetis Peripheral Module Quick Reference" page 85 and. 
  // "K20 Sub-Family Reference Manual" page 548. 
  
  FTFL_FCCOB0 = 0x41;             // Selects the READONCE command
  FTFL_FCCOB1 = word;             // read the given word of read once area

  // launch command and wait until complete
  FTFL_FSTAT = FTFL_FSTAT_CCIF;

  while(!(FTFL_FSTAT & FTFL_FSTAT_CCIF))
   *(mac+offset) = FTFL_FCCOB4;         // FTFL_FCC0B4 is always 0, 
   *(mac+offset+1) = FTFL_FCCOB5;       // but still collect only the top four bytes in the right orientation (big endian)
   *(mac+offset+2) = FTFL_FCCOB6;       
   *(mac+offset+3) = FTFL_FCCOB7;      
   interrupts();
}
/**************************************************************/
long int read_teensyID(){
  read_EE(0xe, teensyID, 0); // should be 04 E9 E5 xx, this being PJRC's registered OUI
  read_EE(0xf, teensyID, 4); // xx xx xx xx

  myID = (teensyID[5] << 16) | (teensyID[6] << 8) | (teensyID[7]); // Use bit shifting to get the Teensy ID in decimal number 
  return myID;  
}
/**************************************************************/
int get_teensyType(long int myID){
// first check centre spars
  for (uint8_t unit = 0x00; unit < 2; unit+= 0x01){ 
    if (NC_with_sensor[unit] == myID){
      myType = 1;
    }
    else if (NC_no_sensor[unit] == myID){
      myType = 2;
    }
  }
  return myType;
}
/**************************************************************/
void checkIncomingMessageFromPi(){  
  // see if we are receiving a message from Pi  
  if (Serial.available() > 1){ // Asumme only 2 bytes message 
    incomingByte = Serial.read();  
    if (incomingByte == SOM){
      incomingMsg = Serial.read();     
    }
  }
}
/**************************************************************/
void readIRsensors(){
  // check if any of the IR sensor is triggered 
  for (int i=0; i<3; i++){
    ir_value = analogRead(irPin[i]);
    ir_activated[i] = ir_value[i] > ir_threshold;
  }  
}
/**************************************************************/
void doCalculations(byte action){ 
  /*Sensor Message calculation for type 1 NC with IR sensor*/
  if(ir_activated[0]||ir_activated[1]||activated[2]){ // If any IR is triggered 
    // 1. Do LED Sequence local behaviour
    LED_sequence_triggered = true;
     
    // 2. Send Data to Pi-Pi to do neighbour behaviour 
    ir_triggering_sendMsg = true;
  }
  
  /*Incoming Message from Pi calculation for type 2 NC no IR sensor*/
  if (incomingMsg == LEDSEQUENCE){
    LED_sequence_triggered = true;
  }
}
/**************************************************************/
void sendMessageToPi(){
  if (ir_triggering_sendMsg){
     Serial.write(SOM); // send the byte 0xff to signify a command is about to be sent
     Serial.write(ACTIVEIR); // send ACTIVE message to tell Pi the LED is supposed to be turned on now
  }
}
/**************************************************************/
void setup() {
  /*Determing Teensy type*/
  // Code to read the Teensy ID
  myID = read_teensyID();
  myType = get_teeynsyType(myID);

  /*Set pinMode*/
  for (int i = 0; i<6;i++){
    pinMode(ledPin[i],OUTPUT);
    pinMode(mothPin[i],OUTPUT);
  }
  if (myType == 1){
    for (int i = 0; i<3;i++){
    pinMode(irPin[i],OUTPUT);
    }
  }
  /*Start serial USB*/
  Serial.begin(9600);
  /*Star serial XBee*/
  /*Star Teensy Audio*/
}
/**************************************************************/
void loop() {
 /*Read message to pi via Serial*/
 // Might contain trigger information got from the other Node 
 checkIncomingMessageFromPi();

 /*Read Sensors*/
 readIRsensors(); // Depends on the type of the node 

 /*doCalculations*/ // check the incoming message from Pi and new input sensor data to see if there is new state of triggering information 
 doCalculations();
 
 /*Check frame duration*/
 if (abs(millis()- previousTime) >= FRAMELENGTH){
  /*LED sequence*/
  if (LED_sequence_triggered){ // Time to start the LED sequence behaviour once any IR is triggered 
    LED_sequence_frame_count = 0;
    LED_sequence_triggered = false; // so in the next frame this behaivour will not be restart
    LED_sequence_on = true; // This is always true until reaches the last frame of this behaviour i.e == LED_sequence_frame_max
  }

  if (LED_sequence_on){
    digitalWrite(ledPin[LED_sequence_frame_count],HIGH); // Frame 1: {1,0,0,0,0,0}
                                                         // Frame 2: {0,1,0,0,0,0}...
    LED_sequence_frame_count++;
  }

  if (LED_sequence_frame_count == LED_sequence_max){ // If it is the last frame
    for (int i = 0; i<6;i++){
      digitalWrite(ledPin[i],LOW); // Reset actuators
    }
  }
  
  LED_sequence_on = false;
 }

 /*Send message to Pi via Serial*/
 sendMessageToPi();
 
 previousTime = millis();
}
