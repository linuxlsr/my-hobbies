
const int LED = 9;
int i = 0;
        
        
void setup() {
  // put your setup code here, to run once:
  pinMode(LED, OUTPUT);   // tell arduino tLED is an output

  
}

void loop() {
  // put your main code here, to run repeatedly:
  for(i = 0; i < 255; i++) {    // fade in light
    analogWrite(LED, i);
    delay(10);
  }

  for (i=255; i > 0; i--) {
    analogWrite(LED, i);        // fade out light
    delay(10);
  }

}
