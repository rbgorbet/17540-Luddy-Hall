/*
* usb_serial_comm.cpp - Library for Communication Protocol between Raspberry Pi and Node
* Created By Adam Francey, Kevin Lam, July 5, 2017
* Released for Desktop Kit
* Philip Beesley Architect Inc. / Living Architecture Systems Group
*/

#ifndef NODE_SERIAL_H_
#define NODE_SERIAL_H_

// Delimiters
#define SOM1 0xff
#define SOM2 0xff
#define EOM1 0xfe
#define EOM2 0xfe
#define NUM_SOM 2
#define NUM_EOM 2
#define NUM_ID 3
#define PADDING_BYTE 0xfd

#define MAX_DATA_LENGTH 255

// Message codes
#define TEST_LED_PIN_AND_RESPOND 0x00

class NodeSerial{

  public:
    NodeSerial();
    NodeSerial(int baud_rate);
    ~NodeSerial();

    bool initialized = false;
    byte password[8] = {0xff,0xff,0x04,0x00,0x00,0x01,0xfe,0xfe};
    int password_length = 8;
    void Register(uint8_t my_id_bytes[]);

    void SendMessage(uint8_t code);
    void SendMessage(uint8_t msg, uint8_t data[], uint8_t data_length);
    bool CheckMessage();

    uint8_t last_data_received_[MAX_DATA_LENGTH] = { 0 };
    int last_data_length_;
    uint8_t last_code_received_;
    bool message_waiting_ = 0; // whether or not a received message needs to be processed

    uint8_t SOM[2] = {SOM1,SOM2};
    uint8_t EOM[2] = {EOM1,EOM2};
    uint8_t ID[3] = {0x00,0x00,0x00}; //placeholder

};

#endif //NODE_SERIAL_H_
