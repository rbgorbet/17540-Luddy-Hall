#include <Arduino.h>
#include <stdint.h>

/*
#include <Audio.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <SerialFlash.h>
*/
#include "AudioController.h"

AudioController::AudioController(){
  
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
  

  
 //Serial.begin(115200);

  // note: setting this too high causes a
  AudioMemory(60);
  
  sgtl5000_1.enable();
  sgtl5000_1.inputSelect(myInput);
  sgtl5000_1.volume(0.7);

  mixer1.gain(0,0.2);
  mixer1.gain(1,0.2);  

  filter1.frequency(1000);
  reverb1.reverbTime(20);

  mixer2.gain(0,0.5);
  mixer2.gain(1,0.5);

  SPI.setMOSI(SDCARD_MOSI_PIN);
  SPI.setSCK(SDCARD_SCK_PIN);
  if (!(SD.begin(SDCARD_CS_PIN))) {
    // stop here, but print a message repetitively
    while (1) {
      Serial.println("Unable to access the SD card");
      delay(500);
    }
  }
}

AudioController::~AudioController(){}


void AudioController::loop(){
  if(Serial.available() > 0) {
     int incomingInt = Serial.read();
     
     //REC
     if(incomingInt == 1){
        if(mode == 2) stopPlaying();
        if(mode == 0) startRecording();
     }
     //STOP
     if(incomingInt == 2){
        if(mode == 1) stopRecording();
        if(mode == 2) stopPlaying();        
     }
     //PLAY
     if(incomingInt == 3) {
      if(mode == 1) stopRecording();
      if(mode == 0) startPlaying();
     }
  }
  if (mode == 1) {
    continueRecording();
  }  
}

void AudioController::startRecording() {

  if(SD.exists("RECORD.WAV")){
    SD.remove("RECORD.WAV");
  }
  frec = SD.open("RECORD.WAV",FILE_WRITE);
  if(frec) {
    queue1.begin();
    mode = 1;
    recByteSaved = 0L;
  }
}

void AudioController::continueRecording() {
  if(queue1.available() >= 2){
    byte buffer[512];
    
    memcpy(buffer, queue1.readBuffer(), 256);
    queue1.freeBuffer();
    memcpy(buffer + 256, queue1.readBuffer(),256);
    queue1.freeBuffer();
   
    frec.write(buffer, 512);
    recByteSaved += 512;

   
  }
}

void AudioController::stopRecording(){
  queue1.end();
  if(mode == 1){
    while(queue1.available() > 0){
      
      frec.write((byte*)queue1.readBuffer(), 256);
      queue1.freeBuffer();
      recByteSaved += 256;
    }
    writeOutHeader();
    frec.close();

  }
  mode = 0;
}

void AudioController::startPlaying(){  
  playSdWav1.play("RECORD.WAV");
  mode = 2;
}

void AudioController::stopPlaying(){
  if (mode == 2) playSdWav1.stop();
  mode = 0;
}

void AudioController::writeOutHeader() { // update WAV header with final filesize/datasize

//  NumSamples = (recByteSaved*8)/bitsPerSample/numChannels;
//  Subchunk2Size = NumSamples*numChannels*bitsPerSample/8; // number of samples x number of channels x number of bytes per sample
  Subchunk2Size = recByteSaved;
  ChunkSize = Subchunk2Size + 36;
  frec.seek(0);
  frec.write("RIFF");
  byte1 = ChunkSize & 0xff;
  byte2 = (ChunkSize >> 8) & 0xff;
  byte3 = (ChunkSize >> 16) & 0xff;
  byte4 = (ChunkSize >> 24) & 0xff;  
  frec.write(byte1);  frec.write(byte2);  frec.write(byte3);  frec.write(byte4);
  frec.write("WAVE");
  frec.write("fmt ");
  byte1 = Subchunk1Size & 0xff;
  byte2 = (Subchunk1Size >> 8) & 0xff;
  byte3 = (Subchunk1Size >> 16) & 0xff;
  byte4 = (Subchunk1Size >> 24) & 0xff;  
  frec.write(byte1);  frec.write(byte2);  frec.write(byte3);  frec.write(byte4);
  byte1 = AudioFormat & 0xff;
  byte2 = (AudioFormat >> 8) & 0xff;
  frec.write(byte1);  frec.write(byte2); 
  byte1 = numChannels & 0xff;
  byte2 = (numChannels >> 8) & 0xff;
  frec.write(byte1);  frec.write(byte2); 
  byte1 = sampleRate & 0xff;
  byte2 = (sampleRate >> 8) & 0xff;
  byte3 = (sampleRate >> 16) & 0xff;
  byte4 = (sampleRate >> 24) & 0xff;  
  frec.write(byte1);  frec.write(byte2);  frec.write(byte3);  frec.write(byte4);
  byte1 = byteRate & 0xff;
  byte2 = (byteRate >> 8) & 0xff;
  byte3 = (byteRate >> 16) & 0xff;
  byte4 = (byteRate >> 24) & 0xff;  
  frec.write(byte1);  frec.write(byte2);  frec.write(byte3);  frec.write(byte4);
  byte1 = blockAlign & 0xff;
  byte2 = (blockAlign >> 8) & 0xff;
  frec.write(byte1);  frec.write(byte2); 
  byte1 = bitsPerSample & 0xff;
  byte2 = (bitsPerSample >> 8) & 0xff;
  frec.write(byte1);  frec.write(byte2); 
  frec.write("data");
  byte1 = Subchunk2Size & 0xff;
  byte2 = (Subchunk2Size >> 8) & 0xff;
  byte3 = (Subchunk2Size >> 16) & 0xff;
  byte4 = (Subchunk2Size >> 24) & 0xff;  
  frec.write(byte1);  frec.write(byte2);  frec.write(byte3);  frec.write(byte4);
  frec.close();

}
