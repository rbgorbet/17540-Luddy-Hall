// example code for sending password to Pi
// for auto-registration

bool initialized = false;
byte password[8] = {0xff,0xff,0x04,0x00,0x00,0x01,0xfe,0xfe};
int password_length = 8;

void setup() {
  Serial.begin(57600);

  // after booting, send password until told otherwise by Pi
  while (initialized == false){
    sendPassword();
    delay(100);
    initialized = readPassword();
  }
  

}

void loop() {

}

void sendPassword(){
  for (int i = 0; i < password_length; i++){
    Serial.write(password[i]);
  }
}

bool readPassword(){

  // checks serial port for password sequence
  // this means the Raspberry Pi has recognized the Teensy

  bool eligible = true;
  bool password_received = false;
  if (Serial.available() > 7){
    for (int i = 0; i < 8; i++){
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

  return password_received;
}

