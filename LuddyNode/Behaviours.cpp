/*
* Behaviours.cpp - Library for Behaviours
* created By Adam Francey March 27, 2018
* Released for Luddy Hall 2018
* Philip Beesley Architect Inc. / Living Architecture Systems Group
*/

#include <Arduino.h>
#include <stdint.h>
#include "Behaviours.h"

Behaviours::Behaviours(int input_frame_duration){
  frame_duration = input_frame_duration;
  current_millis = millis();
  for (int i = 0; i < num_behaviours; i++){
    _behaviour_on[i] = false;
    _framecount[i] = 0;
  }
}

Behaviours::~Behaviours(){}

void Behaviours::start_TEST_LED_PIN(uint8_t num_blinks){

  // initialize this behaviour
  _behaviour_on[_behaviour_TEST_LED_PIN] = true;
  _framecount[_behaviour_TEST_LED_PIN] = 0;

  // off for 100ms, on for 100ms = 200ms per blink
  // 200ms/frame_duration = number of frames per blink
  _behaviour_max_frames[_behaviour_TEST_LED_PIN] = num_blinks*200/frame_duration;

  _modifiers[_behaviour_TEST_LED_PIN] = num_blinks;

}

void Behaviours::_do_behaviour_TEST_LED_PIN(){
  uint8_t num_blinks = _modifiers[_behaviour_TEST_LED_PIN];
  int framecount = _framecount[_behaviour_TEST_LED_PIN];

  int milliseconds_since_behaviour_started = framecount*frame_duration;
  
  // oscillates between true and false, changes every 100 ms
  // starts true for first 100ms
  bool on = ((milliseconds_since_behaviour_started % 1000) % 200) < 100;

  // the actual behaviour
  if (on){
    digitalWrite(13, HIGH);
  } else {
    digitalWrite(13, LOW);  
  }

  // check to see if the behaviour is complete,
  // otherwise
  if (framecount >= _behaviour_max_frames[_behaviour_TEST_LED_PIN]){
    _behaviour_on[_behaviour_TEST_LED_PIN] = false;
    _framecount[_behaviour_TEST_LED_PIN] = 0;
    digitalWrite(13,LOW); // turn off light (on stays true, assuming because of timing)
  } else {
    _framecount[_behaviour_TEST_LED_PIN]++;
    
  }
  
}

void Behaviours::loop(){
  elapsed_millis = millis() - current_millis;
  if (elapsed_millis >= frame_duration){
    if (_behaviour_on[_behaviour_TEST_LED_PIN]){
      _do_behaviour_TEST_LED_PIN();
    }
    current_millis = millis(); //I forgot this line, and forgot to set frame duration... worked as intended??
  }
}





