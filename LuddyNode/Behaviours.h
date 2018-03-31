/*
* Behaviours.h - Library for Behaviour (actuation and sensing)
* Created By Adam Francey March 27, 2018
* Philip Beesley Architect Inc. / Living Architecture Systems Group
*/

#ifndef BEHAVIOURS_H_
#define BEHAVIOURS_H_

class Behaviours{

  public:
    Behaviours(int input_frame_duration);
    ~Behaviours();

    int frame_duration;
    long current_millis;
    long elapsed_millis;

    // behaviours
    // when possible, matches #defined message codes
    const static uint8_t num_behaviours = 2;
    const uint8_t _behaviour_TEST_LED_PIN = 0; // modifier: num_blinks, function: blinks led pin with 100 ms between on and off
    const uint8_t _behaviour_FADE_ACTUATOR_GROUP = 1;

    // behaviour state variables
    bool _behaviour_on[num_behaviours]; // whether on not the behaviour is currently running
    int _framecount[num_behaviours]; // tracks current frame of eah behaviour
    int _behaviour_max_frames[num_behaviours]; // maximum number of frames for each behaviour (may depend on modifiers)
    uint8_t _modifiers[num_behaviours]; // modifiers for each behaviour NOTE: changing to separate state variables for each behaviour
    

    // Behaviour 0: TEST_LED_PIN
    void start_TEST_LED_PIN(uint8_t num_blinks);
    void _resume_TEST_LED_PIN();

    // Behaviour 1: FADE_ACTUATOR_GROUP
    const static int _max_actuators_FADE_ACTUATOR_GROUP = 50; // max data length = 255, 5 bytes per actuator (pin, start, end, time1,time2)
    uint8_t _pins_FADE_ACTUATOR_GROUP[_max_actuators_FADE_ACTUATOR_GROUP];
    uint8_t _start_values_FADE_ACTUATOR_GROUP[_max_actuators_FADE_ACTUATOR_GROUP];
    uint8_t _end_values_FADE_ACTUATOR_GROUP[_max_actuators_FADE_ACTUATOR_GROUP];
    uint8_t _fade_times_FADE_ACTUATOR_GROUP[_max_actuators_FADE_ACTUATOR_GROUP];
    uint8_t _num_frames_to_skip_FADE_ACTUATOR_GROUP[_max_actuators_FADE_ACTUATOR_GROUP];
    uint8_t _num_actuators_FADE_ACTUATOR_GROUP;
    void start_FADE_ACTUATOR_GROUP(uint8_t pins[], uint8_t start_values[], uint8_t end_values[], int fade_times[], uint8_t num_actuators);
    void _resume_FADE_ACTUATOR_GROUP();
    

    void loop();


};

#endif //BEHAVIOURS_H_
