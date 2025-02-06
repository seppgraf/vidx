import multiprocessing as mp
import ctypes
import evdev
from evdev import  UInput,InputDevice, categorize, ecodes,AbsInfo
from pyudmx import pyudmx
from time import sleep



class high_res():

    value = 0
    
    def __init__(self,value = 0):
        self.value = value & 0xFFFF


    def increment(self,value):
        if self.value + value > 0xFFFF:
            self.value = 0xFFFF          
        else: 
            self.value += value             
        
    def decrement(self,value):
        if self.value - value < 0:
            self.value = 0
        else :
            self.value -= value 
            
    
    def get_high(self):
        return self.value >> 8 
    
    def get_low(self):
        return self.value & 0x00FF 

    def get(self):
        return self.value
        


def mh_pan_tilt(dmxdev,cv, pan = 127,pan_high = 127,tilt = 127,tilt_high = 127):
     
    cv[0] = pan
    cv[2] = tilt
   
    sent = dmxdev.send_multi_value(1, cv)

def input_process(a):
    print("Input process started")
        
    device_path = '/dev/input/event4'
    device = InputDevice(device_path)    

    print(f"Device name: {device.name}")
    print(f"Device info: {device.info}")

    for event in device.read_loop():
        if event.type == ecodes.EV_ABS:
            absevent = categorize(event)
            if absevent.event.code==1: #ABS_Y:                
                a[0]=   absevent.event.value

            if absevent.event.code==0: #ABS_Z:
                a[1]=   absevent.event.value

            if absevent.event.code==4: #ABS_RY:                
                a[2]=   absevent.event.value

            if absevent.event.code==5: #ABS_RZ:
                a[3]=   absevent.event.value
        
        if event.type == ecodes.EV_KEY:


            absevent = categorize(event)
            print(absevent) 
            if absevent.event.code==304: #BTN_SOUTH:                
                a[4]=   absevent.event.value

            if absevent.event.code==305: #BTN_EAST:
                a[5]=   absevent.event.value

            if absevent.event.code==307: #BTN_NORTH:                
                a[6]=   absevent.event.value

            if absevent.event.code==308: #BTN_WEST:
                a[7]=   absevent.event.value

            if absevent.event.code== 310: #BTN_TL:
                if absevent.event.value == 1:
                    a[8]= 1

            if absevent.event.code==311: #BTN_TR:
                if absevent.event.value > 0:
                    a[9]= 1

def dmx_process(a):
    print("DMX process started")
    dmx_tilt = 127
    dmx_pan = 127
    dmx_zoom = 0

    cv = [0 for v in range(0, 512)]

    light_on = False 

    tilt_value = high_res()
    pan_value = high_res()

    tilt_value.set_high(127)
    pan_value.set_high(127)



    
    # Create an instance of the DMX controller and open it    
    print("Opening DMX controller...")
    dmxdev = pyudmx.uDMXDevice()
    
    # This will automagically find a single Anyma-type USB DMX controller
    dmxdev.open()
    print(dmxdev.Device)


    print("mh_pan_tilt()") 
    mh_pan_tilt(dmxdev = dmxdev,cv=cv,pan = 127,pan_high = 127,tilt = 127,tilt_high = 127)

    while (a[0] == 0 or a[1] == 0):
        sleep(0.1)

    while(True):
        ABS_Y=  a[0]
        ABS_Z=  a[1]
        ABS_RY=  a[2]
        ABS_RZ=  a[3]

        BTN_TL = a[8]
        BTN_TR = a[9]


        if ABS_Y > (127+10):
            if  (dmx_tilt + int((ABS_Y - 137)*0.05))  >  255:
                dmx_tilt=255 
            else:
                dmx_tilt += int((ABS_Y - 137)*0.05)              
           

        if ABS_Y < (127-10):
            if (dmx_tilt - int((117 - ABS_Y)*0.05))  <= 0:
                dmx_tilt=0 
            else: 
                dmx_tilt = dmx_tilt - int((117 - ABS_Y)*0.05)
            

        if ABS_Z > (127+10):
            if  (dmx_pan + int((ABS_Z - 137)*0.05))  >  255:
                dmx_pan=255 
            else:
                dmx_pan += int((ABS_Z - 137)*0.05)              
          

        if ABS_Z < (127-10):
            if (dmx_pan - int((117 - ABS_Z)*0.05))  <= 0:
                dmx_pan=0 
            else: 
                dmx_pan = dmx_pan - int((117 - ABS_Z)*0.05)

        
        if ABS_RY > (127+10):
            dmx_zoom = dmx_zoom + int((ABS_RY - 137)*0.2)              
            dmx_zoom = min(dmx_zoom,255)           

        if ABS_RY < (127-10):
            dmx_zoom = dmx_zoom - int((117 - ABS_RY)*0.2)
            dmx_zoom = max(dmx_zoom,0) 


        if a[8] > 0:
            a[8] = 0
            if light_on == False:
                cv[7] = 100
                cv[12] = 255
                light_on = True
            
            elif light_on == True:
                cv[7] = 0
                cv[12] = 0
                light_on = False

        cv[5] = dmx_zoom
        #cv[6] = dmx_zoom  
        mh_pan_tilt(dmxdev = dmxdev,cv=cv,pan = dmx_pan,pan_high = 127,tilt = dmx_tilt,tilt_high = 127) 
        
        
        sleep(0.2)
 

if __name__ == '__main__':
    
    shared_array = mp.Array(ctypes.c_int, 10)


    input_availible = mp.Barrier(2)

    p_input = mp.Process(target=input_process, args=(shared_array,))
    p_dmx = mp.Process(target=dmx_process, args=(shared_array,))
    
    # 
    p_input.start()
    p_dmx.start()
    
    #  
    p_input.join()
    p_dmx.join()
  
    print(shared_array[:])