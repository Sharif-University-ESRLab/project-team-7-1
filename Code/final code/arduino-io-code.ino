
int inputPins[16] = {0, 1, 2, 3, 4, 5, 6, 7, 14, 15, 16, 17, 18, 19, 20, 21};
int singal_out_pins[2] = {12, 13};
int incoming_byte;
unsigned int cur;

void setup(){
    // start serial connection with baud rate 9600
    Serial.begin(9600);
    while (!Serial) {
         ; // wait for serial port to connect. Needed for native USB port only
    }
    // declare input pins
    for (int i=0; i < 16; i++){
        pinMode(inputPins[i],INPUT);
    }
    // decalre output pins
    pinMode(singal_out_pins[0], OUTPUT);
    pinMode(singal_out_pins[1], OUTPUT);
}


void loop(){
    // read input signals and encode them to a 16 bit value
    cur = 0;
    for (int i=0; i < 16; i++){
        int val = digitalRead(inputPins[i]);
        cur += (val << i);
    }
    // send encoded input signals using serial port
    Serial.println(cur);
    delay(1000);
    if (Serial.available()){
      // receive outputs from serial port and decode them 
      incoming_byte = Serial.read();
      incoming_byte  = incoming_byte - 48;
      // write output values to output pins
      for (int i=0; i< 2; i++){
        digitalWrite(singal_out_pins[i], 1 & (incoming_byte >> i));
      }
      
    }
    delay(1000);    
}