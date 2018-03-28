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
    const static uint8_t num_behaviours = 1;
    const uint8_t _behaviour_TEST_LED_PIN = 0; // modifier: num_blinks, function: blinks led pin with 100 ms between on and off

    // behaviour state variables
    bool _behaviour_on[num_behaviours]; // whether on not the behaviour is currently running
    int _framecount[num_behaviours]; // tracks current frame of eah behaviour
    int _behaviour_max_frames[num_behaviours]; // maximum number of frames for each behaviour (may depend on modifiers)
    uint8_t _modifiers[num_behaviours]; // modifiers for each behaviour
    

    // TEST_LED_PIN
    void start_TEST_LED_PIN(uint8_t num_blinks);
    void _do_behaviour_TEST_LED_PIN();

    void loop();


};

#endif //BEHAVIOURS_H_
