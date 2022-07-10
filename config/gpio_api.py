#import the library
import os, sys, getopt, time, os.path, glob
import random
import Logfile
#import mqtt_srv

from pyA20.gpio import gpio
from pyA20.gpio import port
from pyA20.gpio import connector

from time import sleep

VERBOSE = 1

#########################
# gpio_control(pin, updown, sztime)
# pin: numero de pin
# updown: 
#         0->LOW
#         1->HIGH
#         2->HIGH, sleep, LOW
#         3->Read/return State
# sztime: sleep time (if not used must be 0)

# 0 si es activo en alta
# 1 si es activo en baja
       
def pincode(pin):

    d=[1024 for i in range(43)]
    d[3]=port.PA12
    d[5]=port.PA11
    d[7]=port.PA6
    d[8]=port.PA13
    d[10]=port.PA14
    d[11]=port.PA1
    d[12]=port.PD14
    d[13]=port.PA0
    d[15]=port.PA3
    d[16]=port.PC4
    d[18]=port.PC7
    d[19]=port.PC0
    d[21]=port.PC1
    d[22]=port.PA2
    d[23]=port.PC2
    d[24]=port.PC3
    d[26]=port.PA21
    d[27]=port.PA19
    d[28]=port.PA18
    d[29]=port.PA7
    d[31]=port.PA8
    d[32]=port.PG8
    d[33]=port.PA9
    d[35]=port.PA10
    d[36]=port.PG9
    d[37]=port.PA20
    d[38]=port.PG6
    d[40]=port.PG7
    
    d[41]=connector.LEDp1  #Led nada
    d[42]=connector.LEDp2  #Led rojo
    
    pin_code = d[int(pin)]
    
    return pin_code


def pinstate(pin_code, RELETYPE):

    try:
        gpio.init()
    except:
        Logfile.printError ('[GPIO] Algo ha ido mal en init')

    state=gpio.input(pin_code)      # Read button state
    
    
    if RELETYPE == 1:
        if state == 1:
            state = 0
        else:
            state = 1

    return (state)
    
def pinup(pin_code, RELETYPE):
    
    if RELETYPE == 1:
        gpiolevel=gpio.LOW
    else:
        gpiolevel=gpio.HIGH
            
    gpio.init()
    gpio.setcfg(pin_code, gpio.OUTPUT)
    gpio.output(pin_code, gpiolevel)

def pindown(pin_code, RELETYPE):
    
    if RELETYPE == 1:
        gpiolevel=gpio.HIGH
    else:
        gpiolevel=gpio.LOW
        
    gpio.init()
    gpio.setcfg(pin_code, gpio.OUTPUT)    
    gpio.output(pin_code, gpiolevel)

def deletecookies (pin):
    szFileRoot= "/config/Pin_"+str(pin)+"*"
    for filename in glob.glob(szFileRoot):
        os.remove(filename) 
        
def gpio_read (pin, RELETYPE):

    nVerbose = VERBOSE

    if not os.getegid() == 0:
        sys.exit('Hay que ejecutarlo como root')
    
    pin_code = pincode(int(pin))
    
    state=pinstate(pin_code, RELETYPE)

    if nVerbose > 0:
        Logfile.printError ('[GPIO] Leyendo PIN: '+str(pin)+" State: "+str(state))
    return (state)

        
def gpio_control_callback(pin, updown, Obj, mqttc_callback):

    # 29: Calefaccion general
    # 31: Libre
    # 32: Persianas 1 Up
    # 33: Persianas 1 Down
    # 35: Persianas 2 Up
    # 36: Persianas 2 Down
    # 37: Persianas 3 Up
    # 38: Persianas 3 Down
    
    Logfile.printError ('[GPIO] Call with callback')
    nVerbose = VERBOSE
    sztime = str(Obj.getRelayTime())
    RELETYPE = Obj.getInvertRelay()    

    if not os.getegid() == 0:
        sys.exit('Hay que ejecutarlo como root')
    
    pin_code = pincode(int(pin))
    
        
    if int(updown) > 3 or int(updown) < 0:
        Logfile.printError ('[GPIO] Accion fuera de rango')
        return;
        
    if int(updown) == 1:
        if nVerbose > 0:
            Logfile.printError ('[GPIO] Set PIN: '+str(pin)+" HIGH")
        pinup(pin_code, RELETYPE)
        
    if int(updown) == 0:
        if nVerbose > 0:
            Logfile.printError ('[GPIO] Set PIN: '+str(pin)+" LOW")
        pindown(pin_code, RELETYPE)
        deletecookies(pin)                # Borrar cookies para que no se vuelva a parar.
        
    if int(updown) == 2:
        # Primero creamos una cookie indicando que este pin esta HIGH
        hash = random.getrandbits(128)
        szFileName = "/config/Pin_"+str(pin)+"_"+str(hex(hash))
        fd = open(szFileName, 'w')
        fd.close()

        if nVerbose > 0:
            Logfile.printError ('[GPIO] Set PIN: '+str(pin)+" HIGH")
        pinup(pin_code, RELETYPE)
        
        mqttc_callback(Obj)
        
        if nVerbose > 0:
            Logfile.printError ('[GPIO] Sleep: '+sztime)
        time.sleep(float(sztime))
        
        if os.path.isfile(szFileName):      # Si la cookie no existe es que alguien lo ha parado antes. Mejor no tocar
            if nVerbose > 0:
                Logfile.printError ('[GPIO] Set PIN: '+str(pin)+" LOW")
            pindown(pin_code, RELETYPE)
            deletecookies(pin)
            
    if int(updown) == 3:
        state=pinstate(pin_code, RELETYPE)
        if nVerbose > 0:
            Logfile.printError ('[GPIO] Leyendo PIN: '+str(pin)+" State: "+str(state))
        return (state)
        
    mqttc_callback(Obj)
    


if __name__ == "__main__":
    pass
    #gpio_control(sys.argv[1], sys.argv[2], sys.argv[3],0, 1)