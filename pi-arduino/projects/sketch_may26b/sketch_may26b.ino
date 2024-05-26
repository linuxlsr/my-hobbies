// Turn on LED while the button is pressed
const int LED = 13;     // the pin for the LED

const int BUTTON = 7;   // the input pin where the
 // pushbutton is connected

int val = 0;             // val will be used to store the state
                         // of the input pin
int state =0;

int old_val = 0;
 
void setup() {
 pinMode(LED, OUTPUT);   // tell Arduino LED is an output
 pinMode(BUTTON, INPUT); // and BUTTON is an input
}

void loop() {

  val = digitalRead(BUTTON); // read input value and store it
 
  // check whether the input is HIGH (button pressed)
  if ((val == HIGH) && (old_val == LOW)) {
    state = 1 - state;
  } 
  
  old_val = val;
  
  if (state == 1) {
    digitalWrite(LED, HIGH);
    
  } else {
    digitalWrite(LED, LOW);
  }
}
