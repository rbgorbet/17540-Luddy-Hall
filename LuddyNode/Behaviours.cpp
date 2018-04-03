/*
* Behaviours.cpp - Library for Behaviours
* created By Adam Francey March 27, 2018
* Released for Luddy Hall 2018
* Philip Beesley Architect Inc. / Living Architecture Systems Group
*/

#include <Arduino.h>
#include <stdint.h>
#include "Behaviours.h"
#include <SoftPWM.h>

Behaviours::Behaviours(int input_frame_duration){
  // set frame duration
  frame_duration = input_frame_duration;

  // get current time for first frame
  current_millis = millis();

  // initial state of behaviour
  for (int i = 0; i < num_behaviours; i++){
    _behaviour_on[i] = false;
    _framecount[i] = 0;
  }

  // begin software PWM
  SoftPWMBegin(SOFTPWM_NORMAL);
}

Behaviours::~Behaviours(){}


// Behaviour 0: TEST_LED_PIN
// Blinks the on board LED

void Behaviours::start_TEST_LED_PIN(uint8_t num_blinks){

  // initialize this behaviour
  _behaviour_on[_behaviour_TEST_LED_PIN] = true;
  _framecount[_behaviour_TEST_LED_PIN] = 0;

  // off for 100ms, on for 100ms = 200ms per blink
  // 200ms/frame_duration = number of frames per blink
  _behaviour_max_frames[_behaviour_TEST_LED_PIN] = num_blinks*200/frame_duration;

  _modifiers[_behaviour_TEST_LED_PIN] = num_blinks;

}

void Behaviours::_resume_TEST_LED_PIN(){
  uint8_t num_blinks = _modifiers[_behaviour_TEST_LED_PIN];
  int framecount = _framecount[_behaviour_TEST_LED_PIN];

  int milliseconds_since_behaviour_started = framecount*frame_duration;
  
  // oscillates between true and false, changes every 100 ms
  // starts true for first 100ms
  bool on = ((milliseconds_since_behaviour_started % 1000) % 200) < 100;

  // the actual behaviour
  if (on){
    SoftPWMSet(13, 50);
  } else {
    SoftPWMSet(13, 0);  
  }

  // check to see if the behaviour is complete,
  // otherwise
  if (framecount >= _behaviour_max_frames[_behaviour_TEST_LED_PIN]){
    _behaviour_on[_behaviour_TEST_LED_PIN] = false;
    _framecount[_behaviour_TEST_LED_PIN] = 0;
    SoftPWMSet(13, 0); // turn off light (on stays true, assuming because of timing)
  } else {
    _framecount[_behaviour_TEST_LED_PIN]++;
    
  }
  
}

// Behaviour 1: FADE_ACTUATOR_GROUP
// Fades a group of actuators (could be only one)
// to delay, give negative numbers as start values?

void Behaviours::start_FADE_ACTUATOR_GROUP(uint8_t pins[], uint8_t start_values[], uint8_t end_values[], int fade_times[], uint8_t num_actuators){
  _behaviour_on[_behaviour_FADE_ACTUATOR_GROUP] = true;
  _framecount[_behaviour_FADE_ACTUATOR_GROUP] = 0;

  // get modifiers for behaviour
  int max_fade_time = 0;
  for (uint8_t actuator = 0; actuator < num_actuators; actuator++){

    // set each behaviour modifier to the given input
    _pins_FADE_ACTUATOR_GROUP[actuator] = pins[actuator];
    _start_values_FADE_ACTUATOR_GROUP[actuator] = start_values[actuator];
    _end_values_FADE_ACTUATOR_GROUP[actuator] = end_values[actuator];
    _fade_times_FADE_ACTUATOR_GROUP[actuator] = fade_times[actuator];
    _num_actuators_FADE_ACTUATOR_GROUP = num_actuators;

    // determine number of fames to skip for each actuator
    // that is, only update each actuator every num_frame_to_skip[actuator] frames;

    // end - start = num values to go through (state changes)
    // fade time = time
    // fadetime/frame_duration = number of frames that will pass during the frame time
    // example:
    // end - start = 19 - 0 = 20 state changes
    // fadetime/frameduration = 1000ms/10ms = 100 frames
    // num_frames_to_skip = 100/20 = 5
    // fade will end after 100 frames, changing every fifth frame

    //-------------------
    // end - start + 1 = 20 - 0 + 1 = 21 state changes
    // fadetime/fadeduration = 1000ms/10ms = 100 frames
    // num_frames_to_skip = 100 frames/21 state changes = 100/21 = 4.8 = 4 = update state every fourth frame
    // 21*4 = 84 frames to go from 0 to 20
    // 84 * 10ms = 840 ms to go from 0 to 20
    //-------------

    // example2:
    // end - start = 20-0 = 20 state changes
    //fadetime/frameduration = 250ms/10ms = 25 frames
    // num_frames_to_skip = 25/20 = 1.25 = 1 (integer division rounds down)
    // so fade will end after 20 frames, changing every frame, with 5 frames left over

    // example3:
    // end - start = 20 - 0
    // fadetime/frameduration = 100ms/10ms = 10 frames
    // num_frames_to_skip = 10/20 = 0
    // fade will not start since # % 0 = undefined

    // ISSUE example 4: (rolling over and looping when I send these values?)
    // end - start = 100 - 0 = 101 state changes
    // fadetime/frameduration = 60000/50 = 1200 frames
    // num_frames_to_skip = 1200 frames / 101 state changes = 11.8 = 11
    // fixed: change num_frames_in_fade_time from uint8_t to int

    // ISSUE example 5: (immediately jumping to end values)
    // end - start = 100 - 0 = 101 state changes
    // fadetime/frameduration = 2000/50 = 40 frames
    // num_frames_to_skip = 40 frames / 101 state changes = 0
    // hack/fix: lower frame duration
    // real solution: skip values (rather than frames) when num_frames_to_skip = 0
    uint8_t num_state_changes = abs(end_values[actuator] - start_values[actuator]);
    int num_frames_in_fade_time = fade_times[actuator]/frame_duration;
    _num_frames_to_skip_FADE_ACTUATOR_GROUP[actuator] = num_frames_in_fade_time/num_state_changes;

    // determine maximum fade time
    if (fade_times[actuator] > max_fade_time){
      max_fade_time = fade_times[actuator];
    }
  }

  // maximum frames depends on maximum fade time
  _behaviour_max_frames[_behaviour_FADE_ACTUATOR_GROUP] = max_fade_time/frame_duration;
}

void Behaviours::_resume_FADE_ACTUATOR_GROUP(){
  int framecount = _framecount[_behaviour_FADE_ACTUATOR_GROUP];
  for (uint8_t actuator = 0; actuator < _num_actuators_FADE_ACTUATOR_GROUP; actuator++){
    uint8_t start_value = _start_values_FADE_ACTUATOR_GROUP[actuator];
    uint8_t end_value = _end_values_FADE_ACTUATOR_GROUP[actuator];
    uint8_t num_frames_to_skip = _num_frames_to_skip_FADE_ACTUATOR_GROUP[actuator];
    uint8_t pin = _pins_FADE_ACTUATOR_GROUP[actuator];
    uint8_t PWM_value;

    // NEED TO FIX
    // PWM_values is rolling over?
    if (start_value <= end_value){
      // fading up
      PWM_value = start_value + framecount/num_frames_to_skip;
      if (framecount % num_frames_to_skip == 0 && PWM_value <= end_value){
        safe_write(pin, PWM_value);
      }
    } else {
      // fading down
      PWM_value = start_value - framecount/num_frames_to_skip;
      if (framecount % num_frames_to_skip == 0 && PWM_value >= end_value){
        safe_write(pin, PWM_value);
      }
    }
  }

  if (framecount >= _behaviour_max_frames[_behaviour_FADE_ACTUATOR_GROUP]){
    _behaviour_on[_behaviour_FADE_ACTUATOR_GROUP] = false;
    _framecount[_behaviour_FADE_ACTUATOR_GROUP] = 0;
    // set each actuator to its ending value
    for (uint8_t a = 0; a < _num_actuators_FADE_ACTUATOR_GROUP; a++){
      safe_write(_pins_FADE_ACTUATOR_GROUP[a],_end_values_FADE_ACTUATOR_GROUP[a]);
    }
  } else {
    _framecount[_behaviour_FADE_ACTUATOR_GROUP]++;
    
  }
  
  
}

void Behaviours::loop(){
  elapsed_millis = millis() - current_millis;
  if (elapsed_millis >= frame_duration){
    if (_behaviour_on[_behaviour_TEST_LED_PIN]){
      _resume_TEST_LED_PIN();
    }
    if (_behaviour_on[_behaviour_FADE_ACTUATOR_GROUP]){
      _resume_FADE_ACTUATOR_GROUP();
    }
    current_millis = millis(); //I forgot this line, and forgot to set frame duration... worked as intended??
  }
}

void Behaviours::safe_write(uint8_t pin, uint8_t val){
  if (val < 76){
    SoftPWMSet(pin,val);
  }
}





