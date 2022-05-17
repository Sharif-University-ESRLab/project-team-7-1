
int nums[16] = {7,22,24,26,28,30,32,36,38,40,42,44,46,48,50,52};
int counter;
int inputPins[16] = {7,22,24,26,28,30,32,36,38,40,42,44,46,48,50,52};
int singal_out_pins[2] = {10,12};
int outputPins[16];
int incoming_byte;
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
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(singal_out_pins[0], OUTPUT);
    pinMode(singal_out_pins[1], OUTPUT);
}


void loop(){
    cur = 0;
    for (int i=0; i < 16; i++){
        digitalWrite(outputPins[i], 1 & (nums[i] >> counter));
        int val = digitalRead(inputPins[i]);
        cur += (val << i);
    }
    Serial.println(cur);
    delay(1000);
    if (Serial.available()){
      incoming_byte = Serial.read();
      incoming_byte  = incoming_byte - 48;
      for (int i=0; i< 2; i++){
        digitalWrite(singal_out_pins[i], 1 & (incoming_byte >> i));
      }
      
    }
    
    delay(1000);
    counter = (counter + 1) % len;
    
}