
int nums[16] = {7,22,24,26,28,30,32,36,38,40,42,44,46,48,50,52};
int counter;
int inputPins[16] = {7,22,24,26,28,30,32,36,38,40,42,44,46,48,50,52};
int outputPins[16];
unsigned int cur;
int len=6;

void setup(){
    Serial.begin(9600);
    while (!Serial) {
         ; // wait for serial port to connect. Needed for native USB port only
    }
    for (int i=0; i < 16; i++){
        pinMode(inputPins[i],INPUT);
        outputPins[i] = inputPins[i] + 1;
        pinMode(outputPins[i],OUTPUT);
    } 
}


void loop(){
    cur = 0;
    for (int i=0; i < 16; i++){
        digitalWrite(outputPins[i], 1 & (nums[i] >> counter));
        int val = digitalRead(inputPins[i]);
        cur += (val << i);
    }
    delay(1);
    counter = (counter + 1) % len;
    Serial.println(cur);
}