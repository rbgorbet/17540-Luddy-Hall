/*
 * Living Architecture Systems
 * Testing code for 1 Sound Sensor Scout unit 
 * test code Feb 06 Amber Ma
 * 
 * Will eventually add all necessary functions to become one general code that will be loaded to all NCs
 * and let the NCs check their IDs and decide their types to do the corresponding demands.

 * Hardware 1 Sound Sensor Scout unit
1 Rpi
1 NC
1 Teensy 3.2
1 Teensy Audio Board
2 Device Module B HCDM
3 IR sensor
1 Sound detector sensor
6 Rebel Star LEDs
2 Moths

* Connection
Sound Sensor: NC_P1_HCDM1_A = pin A17
IR Sensor_1: NC_P1_HCDM1_B = pin 13
RBLED1: NC_P1_HCDM1_C = pin 25
RBLED2: NC_P1_HCDM1_D = pin 32
RBLED3: NC_P1_HCDM1_E = pin 6
RBLED4: NC_P1_HCDM1_F = pin 21
RBLED5: NC_P1_HCDM1_G = pin 26
RBLED6: NC_P1_HCDM1_H = pin 31

IR Sensor_2: NC_P2_HCDM2_A = pin A0
IR Sensor_3: NC_P2_HCDM2_B = pin A1
MOTH_1: NC_P2_HCDM_E = pin A8
MOTH_2: NC_P2_HCDM_F = pin A9
*/

#include <SoftPWM.h>

#include <Audio.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <SerialFlash.h>

// Set up for Teensy Audio board
/**************************************************************/
AudioPlaySdWav           playSdWav2;     //xy=106,474
AudioPlaySdWav           playSdWav1;     //xy=118,388
AudioMixer4              mixer2;         //xy=296,468
AudioMixer4              mixer1;         //xy=309,359
AudioOutputI2SQuad       i2s_quad2;      //xy=510,407
AudioConnection          patchCord1(playSdWav2, 0, mixer1, 1);
AudioConnection          patchCord2(playSdWav2, 1, mixer2, 0);
AudioConnection          patchCord3(playSdWav1, 0, mixer1, 0);
AudioConnection          patchCord4(playSdWav1, 1, mixer2, 1);
AudioConnection          patchCord5(mixer2, 0, i2s_quad2, 1);
AudioConnection          patchCord6(mixer2, 0, i2s_quad2, 3);
AudioConnection          patchCord7(mixer1, 0, i2s_quad2, 0);
AudioConnection          patchCord8(mixer1, 0, i2s_quad2, 2);
AudioControlSGTL5000     sgtl5000_2;     //xy=322,662
AudioControlSGTL5000     sgtl5000_1;     //xy=324,626


//#define SDCARD_CS_PIN    10
//#define SDCARD_MOSI_PIN  7
//#define SDCARD_SCK_PIN   14

// Use these with the Teensy 3.5 & 3.6 SD card
#define SDCARD_CS_PIN    BUILTIN_SDCARD
#define SDCARD_MOSI_PIN  11  // not actually used
#define SDCARD_SCK_PIN   13  // not actually used

// Use these for the SD+Wiz820 or other adaptors
//#define SDCARD_CS_PIN    4
//#define SDCARD_MOSI_PIN  11
//#define SDCARD_SCK_PIN   13

/**************************************************************/
// Message struct sent between RPi and Teensy 
//<SOM><incomingDemand>
//Staring of message
#define SOM 0xff

//incomingDemand
#define ACTIVE_TRACK 0x0A //10
#define PLAY_TRACK 0X0B   //11

#define ACTIVE_MOTH 0X14  //20
#define VIB_MOTH 0X15     //21

#define ACTIVE_LED 0x1E   //30
#define ON_LED 0x1F       //31

#define NOTHING 0x64	  //100 

int led_detc = 13;  // Special LED for debugging purpose

/**************************************************************/
// NC_P2
int irR_pin = A0;  // right 1
int irL_pin = A1;  // left 2

int ir_threshold = 300;
int wave_time = 500;
bool left_activated = false;
bool right_activated = false;

unsigned long left_activated_time = 0;
unsigned long right_activated_time = 0;

int irL_value = 0;
int irR_value = 0;
int irL_active = 0;
int irR_active = 0;
int ir_state = 0;

// ir_status signals the aggregate status of the stereo IR pair
// 0 = neither active
// 1 = left-to-right
// 2 = right-to-left
// 3 = left active only
// 4 = right active only
// 5 = both active simultaneously

int ir_status = 0;  // left-to-right, right-to-left, both, left, right, neither

int mothR_pin = A9; // right
int mothL_pin = A8; // left

/**************************************************************/
// NC_P1
int mic_pin = A17;
int ir1_pin = A13;
int pinArray1[6] = {25,32,6,21,26,31}; // All pins are for Rebel Stars LED

int ir1_value = 0;
int ir1_trigger = false;
//bool ignore_irtrigger = false;

int sound_threshold = 200;
bool sound_trigger = false;
//bool ignore_soundtrigger = false;
int sound_value = 0;
/**************************************************************/

const long INTERVAL10 = 10; // To replace delay(10)
const long INTERVAL200 = 200; // To replace dealy(200)

long int NC_identifiers[2] = {258698,258581}; // WATCH OUT THE 0 at the end
long int Sound_teensy_identifiers[2] = {365326,245753}; // WATCH OUT THE 0 at the end

// Teensy ID
// Filled with read_EE(), read_teensyID()
static uint8_t teensyID[8];
long int myID;
int my_type; // 0-Audio 1-NC

int sensor_type;

bool First_LED_ON = 0;

/***************************************************************/
void delayFunc(unsigned long pre, unsigned long curr, const long intervalLength){
   while (curr - pre < intervalLength){ 
    curr = millis();
  }
}
/**************************************************************/
void checkIncomingMessageFromPi(){
  // see if we are receiving a message
  byte incomingByte;
  byte incomingMsg1;
  byte incomingMsg2;
  byte incomingMsg3;

  if (Serial.available() > 1){
    incomingByte = Serial.read();

    if (incomingByte == SOM){
      incomingMsg1 = Serial.read();
	  incomingMsg2 = Serial.read();
	  incomingMsg3 = Serial.read();

      handleIncomingMessage(incomingMsg1,incomingMsg2,incomingMsg3);

     }
  }

}
/**************************************************************/
void handleIncomingMessage(byte action1, byte action2, byte action3) {
	// if incomingMsg indicates that LED should be on
	// digitalWrtie LED to turn it on and off twice
	// <SOM><LED><MOTH/LED><TRACK> 4 Bytes going to be sent to RPi 
	if (action1 == ON_LED || action2 == ACTIVE_LED) {
		// Response in SSS 6 Rebel Stars fade in and out 
		First_LED_ON = 1; // To start the LED chain sequence

		unsigned long previousMillis = 0;
		const long interval = 500;           // sequence interval in milliseconds
		unsigned long currentMillis = millis();

		if (First_LED_ON == HIGH) {
			// loop from the lowest pin to the highest:
			for (int i = 0; i < 7; i++) {
				// turn the pin on:
				delayFunc(previousMillis, currentMillis, 500);

				digitalWrite(pinArray1[i], HIGH);
				currentMillis = millis();
				previousMillis = currentMillis;
			}
			First_LED_ON = 0;
		}

		if (First_LED_ON == 0) {
			// loop from the highest pin to the lowest: 
			for (int i = 6; i >= 0; i--) {
				delayFunc(previousMillis, currentMillis, 500);

				digitalWrite(pinArray1[i], LOW);
				previousMillis = currentMillis;
			}
		}
		while (currentMillis - previousMillis <= interval) {
			currentMillis = millis();
		}
	}
	if (action2 == VIB_MOTH) {
		unsigned long previousMillis = 0;
		const long interval = 500;           // sequence interval in milliseconds
		unsigned long currentMillis = millis();
		switch (ir_status) {
		case 0: // Nothing 
			break;

		case 1: // Moth left-right 
			digitalWrite(mothR_pin, HIGH);
			//delay(200);

			delayFunc(previousMillis, currentMillis, INTERVAL200);

			digitalWrite(mothR_pin, LOW);

			digitalWrite(mothL_pin, HIGH);


			delayFunc(previousMillis, currentMillis, INTERVAL200);

			digitalWrite(mothL_pin, LOW);
			break;

		case 2: // Moth right-left
			digitalWrite(mothL_pin, HIGH);
			//delay(200);

			delayFunc(previousMillis, currentMillis, INTERVAL200);

			digitalWrite(mothL_pin, LOW);

			digitalWrite(mothR_pin, HIGH);

			delayFunc(previousMillis, currentMillis, INTERVAL200);

			digitalWrite(mothR_pin, LOW);

			break;
		case 3:
			break;
		case 4:
			break;
		case 5:
			break;
		}

		if (action3 == PLAY_TRACK) {
			if (playSdWav1.isPlaying() == false) {
				Serial.println("Start playing 1");
				playSdWav1.play("SDTEST1.WAV");
				delay(10); // wait for library to parse WAV info
			}
			if (playSdWav2.isPlaying() == false) {
				Serial.println("Start playing 2");
				playSdWav2.play("SDTEST4.WAV");
				delay(10); // wait for library to parse WAV info
			}
		}


	}
}
/**************************************************************/
void sendMessageToPi(){ // Only Node Controller need to send message to Rpi so far. Teensy Audio and Teensy 3.2 nope 
	// <SOM><LED><MOTH/LED><TRACK> 4 Bytes going to be sent to RPi 
	if (my_type == 1) {
		Serial.write(SOM);
		if (ir1_trigger)
			Serial.write(ACTIVE_LED);
		else
			Serial.write(NOTHING);

		if (ir_status == 1 || ir_status == 2)
			Serial.write(ACTIVE_MOTH);
		else if (ir_status == 3 || ir_status == 4)
			Serial.write(ACTIVE_LED);
		else
			Serial.write(NOTHING);

		if (sound_trigger)
			Serial.write(ACTIVE_TRACK);
		else
			Serial.write(NOTHING);
	}
}
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
// returns unique enumerated Teensy number
// Teensy number is 0 for IR
// and 1 for Sound
//
// int get_my_number(long int myID){..............}
/**************************************************************/
int get_my_type(long int myID){
// first check centre spars
  for (uint8_t unit = 0x00; unit < 2; unit+= 0x01){
    if (NC_identifiers[unit] == myID){
      my_type = 1;
    }
    else if (Sound_teensy_identifiers[unit] == myID){
      my_type = 0;
    }
  }

  return my_type;
}
/**************************************************************/
int check_ir_status(int state_of_ir) {
	switch (state_of_ir) {
	case 00:
		// nothing on
		ir_status = 0;
		break;
	case 01:
		// ir2 activated
		ir_status = 3;
		left_activated = true;
		left_activated_time = millis();
		right_activated = false;
		break;
	case 10:
		// ir1 activated
		ir_status = 4;
		right_activated = true;
		right_activated_time = millis();
		left_activated = false;
		break;
	case 11:
		// both activated
		ir_status = 5;
		break;
	}

	if (right_activated && ((right_activated_time - left_activated_time) < wave_time)) {
		ir_status = 1;
		right_activated = 0;
	}

	if (left_activated && ((left_activated_time - right_activated_time) < wave_time)) {
		ir_status = 2;
		left_activated = 0;
	}

	return ir_status;
}

/*int check_case(int status_of_ir) {
	unsigned long curr = millis();
	unsigned long prev = curr;

	switch (status_of_ir) {
		case 0: // Nothing 
			break;
	
		case 1: // Moth left-right 
			digitalWrite(mothR_pin, HIGH);
			//delay(200);

			delayFunc(prev, curr, INTERVAL200);

			digitalWrite(mothR_pin, LOW);

			digitalWrite(mothL_pin, HIGH);

			curr = millis();
			prev = curr;
			delayFunc(prev, curr, INTERVAL200);

			digitalWrite(mothL_pin, LOW);
			break;

		case 2: // Moth right-left
			digitalWrite(mothL_pin, HIGH);
			//delay(200);

			delayFunc(prev, curr, INTERVAL200);

			digitalWrite(mothL_pin, LOW);

			digitalWrite(mothR_pin, HIGH);

			curr = millis();
			prev = curr;
			delayFunc(prev, curr, INTERVAL200);

			digitalWrite(mothR_pin, LOW);
		
			break;
		case 3: //LED sequence 
			
			break;
		case 4: // LED sequence 
			
			break;
		case 5: // Nothing 
			//digitalWrite(mothL_pin, LOW);
			//digitalWrite(mothR_pin, LOW);
			break;
		}

		curr = millis();
		prev = curr;
		delayFunc(prev, curr, INTERVAL10);
}*/
	
	

/**************************************************************/
void setup() {
  Serial.begin(57600);

  myID = read_teensyID();
  my_type = get_my_type(myID);

  pinMode(led_detc,OUTPUT);

  if (my_type == 1){ // NC
    for (int i=0;i<6;i++) {
    pinMode(pinArray1[i], OUTPUT);
    }
    pinMode(mic_pin,INPUT);
    pinMode(ir1_pin,INPUT);

    pinMode(irL_pin,INPUT);
    pinMode(irR_pin,INPUT);
    pinMode(mothR_pin,OUTPUT);
    pinMode(mothL_pin,OUTPUT);
  }
  else if (my_type == 0){ // Teensy audio board
    AudioMemory(8);
    sgtl5000_1.enable();
    sgtl5000_1.volume(0.5);
    sgtl5000_1.setAddress(LOW);
    sgtl5000_2.setAddress(HIGH);
    SPI.setMOSI(SDCARD_MOSI_PIN);
    SPI.setSCK(SDCARD_SCK_PIN);
    if (!(SD.begin(SDCARD_CS_PIN))) {
      while (1) {
        Serial.println("Unable to access the SD card");
        delay(500);
      }
    }
    mixer1.gain(0, 0.5);
    mixer1.gain(1, 0.5);
    mixer2.gain(0, 0.5);
    mixer2.gain(1, 0.5);
  }
  delay(1000);
}
/**************************************************************/
void loop() {
  unsigned long previousMillis = 0;

  checkIncomingMessageFromPi();

  if (my_type == 1) {// NC  
      unsigned long currentMillis = millis();
      ir1_value = analogRead(ir1_pin);
      sound_value = analogRead(mic_pin);

      
      irL_value = analogRead(irL_pin);
	  delayFunc(previousMillis,currentMillis,INTERVAL10);
      previousMillis = currentMillis;
      
      irR_value = analogRead(irR_pin);
      delayFunc(previousMillis,currentMillis,INTERVAL10);
      
      ir1_trigger = ir1_value > ir_threshold;
      irL_active = irL_value > ir_threshold;
      irR_active = irR_value > ir_threshold;
	  sound_trigger = sound_value > sound_threshold;

	  ir_state = 10 * irR_active + irL_active; // 1-right 2-left 
	  check_ir_status(ir_state);
	  //check_case(ir_status);

	  if (ir1_trigger || (ir_status != (0||5)) || sound_trigger) {
		  sendMessageToPi();
	  }
  }
}
/**************************************************************/

