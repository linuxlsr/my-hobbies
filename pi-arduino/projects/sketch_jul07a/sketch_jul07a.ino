
const int LED = 9;

int val = 0;


void setup() {
  // put your setup code here, to run once:
  pinMode(LED, OUTPUT);

}

void loop() {
  // put your main code here, to run repeatedly:
  val = analogRead(0);

  analogWrite(LED, val/4);

  delay(10);

}
