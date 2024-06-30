
const int LED = 9;
const int BUTTON = 7;

int val = 0;

int old_val = 0;
int state = 0;

int brightness = 128;
unsigned long startTime = 0;
        
        
void setup() {
  // put your setup code here, to run once:
  pinMode(LED, OUTPUT);   // tell arduino tLED is an output
  pinMode(BUTTON, INPUT); // when did we begin pressing?
  
}

void loop() {
  // put your main code here, to run repeatedly:

  val = digitalRead(BUTTON);

  if ((val == HIGH) && (old_val == LOW)) {
    state = 1 - state;
    startTime = millis();

    delay(10);
  }

  if ((val == HIGH) && (old_val == HIGH)) {
    if (state == 1 && (millis() - startTime) > 500) {
      brightness++;
      delay(10);

      if (brightness > 255) {
        brightness = 0;
      }
    }
  }

  old_val = val;
  
  if (state == 1){
    analogWrite(LED, brightness);
  } else {
    analogWrite(LED, 0);
  }
}
