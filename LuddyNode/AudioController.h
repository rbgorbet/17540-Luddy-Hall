#include <Audio.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <SerialFlash.h>


#ifndef AUDIOCONTROLLER_H_
#define AUDIOCONTROLLER_H_

class AudioController{

  public:
    AudioController();
    ~AudioController();

    //write wav
    unsigned long ChunkSize = 0L;
    unsigned long Subchunk1Size = 16;
    unsigned int AudioFormat = 1;
    unsigned int numChannels = 1;
    unsigned long sampleRate = 44100;
    unsigned int bitsPerSample = 16;
    unsigned long byteRate = sampleRate*numChannels*(bitsPerSample/8);// samplerate x channels x (bitspersample / 8)
    unsigned int blockAlign = numChannels*bitsPerSample/8;
    unsigned long Subchunk2Size = 0L;
    unsigned long recByteSaved = 0L;
    unsigned long NumSamples = 0L;
    byte byte1, byte2, byte3, byte4;
    //uint8_t byte1, byte2, byte3, byte4;
    
    const int myInput = AUDIO_INPUT_LINEIN;

        // GUItool: begin automatically generated code
    AudioPlaySdWav           playSdWav1;     //xy=69,280.5
    AudioInputI2S            i2s1;           //xy=119.3055419921875,219.4722137451172
    AudioMixer4              mixer1;         //xy=211.49999321831598,294.24998643663196
    AudioFilterStateVariable filter1;        //xy=338.999993218316,293.99998643663196
    AudioEffectReverb        reverb1;        //xy=457.9999932183159,281.99998643663196
    AudioRecordQueue         queue1;         //xy=487.61114501953125,136.80555725097656
    AudioMixer4              mixer2;         //xy=623,240
    AudioOutputI2S           i2s2;           //xy=752.3611450195312,235.66665649414062
    /*
    AudioConnection          patchCord1(playSdWav1, 0, mixer1, 0);
    AudioConnection          patchCord2(playSdWav1, 1, mixer1, 1);
    AudioConnection          patchCord3(i2s1, 0, queue1, 0);
    AudioConnection          patchCord4(i2s1, 1, mixer2, 0);
    AudioConnection          patchCord5(mixer1, 0, filter1, 0);
    AudioConnection          patchCord6(mixer1, 0, filter1, 1);
    AudioConnection          patchCord7(filter1, 0, reverb1, 0);
    AudioConnection          patchCord8(reverb1, 0, mixer2, 1);
    AudioConnection          patchCord9(mixer2, 0, i2s2, 0);
    AudioConnection          patchCord10(mixer2, 0, i2s2, 1);
    */
    AudioControlSGTL5000     sgtl5000_1;     //xy=379.77777099609375,429.5555419921875
    // GUItool: end automatically generated code


    int mode = 0; // 0=stopped, 1=recording, 2=playing
    File frec;
    
    // Use these with the Teensy 3.6 & Audio Shield
    #define SDCARD_CS_PIN    BUILTIN_SDCARD
    #define SDCARD_MOSI_PIN  11  // not actually used
    #define SDCARD_SCK_PIN   13  // not actually used
    
    
    // Use these with the Teensy Audio Shield
    //#define SDCARD_CS_PIN    10
    //#define SDCARD_MOSI_PIN  7
    //#define SDCARD_SCK_PIN   14

    void loop();
    void startRecording();
    void stopRecording();
    void startPlaying();
    void stopPlaying();
    void continueRecording();
    void writeOutHeader();



};

#endif //AUDIOCONTROLLER_H_
