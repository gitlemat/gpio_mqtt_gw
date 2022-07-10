import paho.mqtt.client as mqtt
import Logfile
import json, time, threading
import gpio_api

# No hace falta subscribirse a las stats de persianas ya que no mantenemos posicion con gpio
# Si nos subscribimos a stat de switch para restaurar en caso de reinicio del proceso


MQTT_TOPIC_GPIO_COVER_CMD = "cmnd/mqtt_gw/gpio/cover"
MQTT_TOPIC_GPIO_COVER_STAT = "stat/mqtt_gw/gpio/cover"

MQTT_TOPIC_GPIO_COVER_CMD_SUBS = MQTT_TOPIC_GPIO_COVER_CMD + "/#"

MQTT_TOPIC_GPIO_SWITCH_CMD = "cmnd/mqtt_gw/gpio/switch"
MQTT_TOPIC_GPIO_SWITCH_STAT = "stat/mqtt_gw/gpio/swtich"

MQTT_TOPIC_GPIO_SWITCH_CMD_SUBS = MQTT_TOPIC_GPIO_SWITCH_CMD + "/#"
MQTT_TOPIC_GPIO_SWITCH_STAT_SUBS = MQTT_TOPIC_GPIO_SWITCH_STAT + "/#"


# "{"PinUp":32,"PinDown":33,"State":1,"Invert":0,"Name":"salon","Time":10}"
MQTT_SERVER = "mqtt.domocasa.com"

class SwitchClass():
    def __init__(self,pin, invertRelay, Name):
        self.pin = pin
        self.invertRelay = invertRelay
        self.name = Name
        self.relayTime = 0
        
        
        
    def getPin(self):
       return(self.pin)
       
    def getInvertRelay(self):
       return(self.invertRelay)
       
    def setInvertRelay(self, invertRelay):
       self.invertRelay = invertRelay
       
    def getRelayTime(self):
       return(self.relayTime)
       
    def getName(self):
       return(self.name)
    

class CoverClass():
    def __init__(self,pinUp, pinDown, relayTime, invertRelay, Name):
        self.pinUp = pinUp
        self.pinDown = pinDown
        self.invertRelay = invertRelay
        self.name = Name
        self.relayTime = relayTime
        
    def getPinDown(self):
       return(self.pinDown)
    
    def getPinUp(self):
       return(self.pinUp)   
       
    def getInvertRelay(self):
       return(self.invertRelay)
    
    def getName(self):
       return(self.name)
    
    def getRelayTime(self):
       return(self.relayTime)
       
    def setInvertRelay(self, invertRelay):
       self.invertRelay = invertRelay
    

class MyMQTTClass(mqtt.Client):
    
    def __init__(self):
        Logfile.printError ('Gateway inicializando.... ')
        super().__init__()
        
        self._typeMatrix = {}
        self._pin1Matrix = {}
        self._pin2Matrix = {}
        self._invertMatrix = {}
        self._relayTime = {}
        
    def load_config (self):
        szFileName='/config/gpio_gw.cfg'
         
        try:
            with open(szFileName, 'r') as fd:
                lines_orig = fd.readlines()
                nLineMax = len(lines_orig)
        except IOError:
            Logfile.printError ('Error leyendo gpio_gw.cfg')
            return
             
        Logfile.printError ('')
        
        
        nLine = 0
        
        
        for nLine in range(nLineMax):
            if (lines_orig[nLine][0] == "\n" or lines_orig[nLine][0] == "#"):
                pass
            else:
                line = lines_orig[nLine].strip().replace(" ", "").split(',')
                nLen = len(line)
                if nLen < 4:
                    break
                    
                szName = line[1]
                szType = line[0]
                szInvert = line[2]
                nPin1 = line[3]
                self._typeMatrix.update ({szName:szType})
                self._invertMatrix.update ({szName:szInvert})
                self._pin1Matrix.update ({szName:nPin1})

                if nLen > 4:
                    nPin2 = line[4]
                    self._pin2Matrix.update ({szName:nPin2})
                else:
                    self._pin2Matrix.update ({szName:""})
                    
                if nLen > 5:
                    nRelayTime = line[5]
                    self._relayTime.update ({szName:nRelayTime})
                else:
                    self._relayTime.update ({szName:""})
                    
                Logfile.printError ('  ++ Name: ' + str(line[1]) + ', Type: ' + str(self._typeMatrix[line[1]]) + ', Invert: ' + str(self._invertMatrix[line[1]]) + ', Pin1: ' + str(self._pin1Matrix[line[1]])  + ', Pin2: ' + str(self._pin2Matrix[line[1]])  + ', RelayTime: ' + str(self._relayTime[line[1]]) )
                
                invert_relay = 0 if szInvert == 'false' else 1
                
                if szType == 'switch':
                    switchObj = SwitchClass (nPin1, invert_relay, szName)
                    self.switch_set(switchObj, 0)  # Pongo a 0 al empezar
                    
                if szType == 'cover':
                    coverObj = CoverClass (nPin1, nPin2, nRelayTime, invert_relay, szName)
                    self.cover_set(coverObj, 0)    # Pongo a 0 al empezar
                    
                
        Logfile.printError ('Gateway inicializado. ')
        
    

    def on_message_gpio_switch_cmd(self, mqttc, obj, msg):
    
        Logfile.printError("Mensaje de switch: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
        # cmnd/mqtt_gw/gpio/switch/salon/set
        msg.payload = msg.payload.decode("utf-8")
        
        topic_list = msg.topic.split('/')
        
        name = topic_list[4]
        try:
            pin_number = self._pin1Matrix[name]
            invert_relay = 0 if self._invertMatrix[name] == 'false' else 1
        except:
            Logfile.printError("Error en el mensaje. No existe el dispositivo " + str(name))
            return
        
        try:
            data = json.loads(msg.payload)
        except:
            Logfile.printError("Error en el mensaje al cargar JSON")
            return
            
        switchObj = SwitchClass (pin_number, invert_relay, name)
            
        if topic_list[5] == "get":
            self.switch_read_and_publish(switchObj)
            return
            
        if topic_list[5] ==  "set": 
            try:
                state = data['State']
            except:
                Logfile.printError("Error en el mensaje. No hay state")
                return
                
            if state < 2 and state > -1:
                self.switch_set(switchObj, state)
                
            return
            
        Logfile.printError("Error. Ningun topic coincide")
        
    def on_message_gpio_switch_stat(self, mqttc, obj, msg):
    
        Logfile.printError("Mensaje de switch (Stat): " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
        # stat/mqtt_gw/gpio/switch/salon
        msg.payload = msg.payload.decode("utf-8")
        
        topic_list = msg.topic.split('/')
        
        name = topic_list[4]
        try:
            pin_number = self._pin1Matrix[name]
            invert_relay = 0 if self._invertMatrix[name] == 'false' else 1
        except:
            Logfile.printError("Error en el mensaje. No existe el dispositivo " + str(name))
            return
        
        try:
            data = json.loads(msg.payload)
        except:
            Logfile.printError("Error en el mensaje al cargar JSON")
            return
            
        switchObj = SwitchClass (pin_number, invert_relay, name)
        
        self.switch_set(switchObj, state)
        
        if 'State' in data:
            state = data['State']
            if state < 2 and state > -1:
                self.switch_set(switchObj, state)
                
            return
            
        Logfile.printError("Error. Ningun topic coincide")
        
        
    def switch_set(self, switchObj, state):
    
        # State:
        #   0: Off
        #   1: On
        
        Logfile.printError("Pedimos tocar swtich")
        
        pin = switchObj.getPin()
        invert_relay = switchObj.getInvertRelay()
                    
        if state == 0:
            gpio_api.gpio_control_callback(pin, 0, switchObj, self.switch_read_and_publish)
            return
            
        if state == 1:
            gpio_api.gpio_control_callback(pin, 1, switchObj, self.switch_read_and_publish)
            return
                  
                
    def switch_read_and_publish(self, switchObj): 
        
        Logfile.printError("Read and Publish Start")
        
        pin = switchObj.getPin()
        invert_relay = switchObj.getInvertRelay()
        name = switchObj.getName()
        
        pin_state = gpio_api.gpio_read (pin, invert_relay)
        
        state = 0
        
        if pin_state == 1:
            state = 1

        payload = {}
        payload.update({"State":state})
        json_payload = json.dumps(payload)
        
        
        szTopic = MQTT_TOPIC_GPIO_SWITCH_STAT + "/" + name + "/state"
        infot = self.publish(szTopic, json_payload, qos=0, retain=True)
        Logfile.printError("Publish: " + json_payload)
        
      
    def on_message_gpio_cover_cmd(self, mqttc, obj, msg):
        # This callback will only be called for messages with topics that match
        # $SYS/broker/messages/#
        
        Logfile.printError("Mensaje de cover: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
        msg.payload = msg.payload.decode("utf-8")
        
        topic_list = msg.topic.split('/')
        
        name = topic_list[4]
        try:
            pinUp_number = self._pin1Matrix[name]
            pinDown_number = self._pin2Matrix[name]
            relay_time = self._relayTime[name]
            invert_relay = 0 if self._invertMatrix[name] == 'false' else 1
        except:
            Logfile.printError("Error en el mensaje. No existe el dispositivo " + str(name))
            return
        
        try:
            data = json.loads(msg.payload)
        except:
            Logfile.printError("Error en el mensaje al cargar JSON")
            return
            
        coverObj = CoverClass (pinUp_number, pinDown_number, relay_time, invert_relay, name)
            
        if topic_list[5] ==  "get":
            self.cover_read_and_publish(coverObj)
            return
            
        if topic_list[5] ==  "set":
        
            valid_state = False
            
            if 'State' in data:
                state = data['State']
                valid_state = True
                
            if 'Position' in data:
                position = data['Position']
                if position < 50:
                    state = 2
                else:
                    state = 1
                valid_state = True
                
            if valid_state == False:
                Logfile.printError("Error en el mensaje. No hay state")
                return
                
            if state < 3 and state > -1:
                self.cover_set(coverObj, state)
                
            return
            
        Logfile.printError("Error. Ningun topic coincide")
    
    def cover_set(self, coverObj, state):
    
        # State:
        #   1: Up
        #   2: DOwn
        #   0: Stop
        
        Logfile.printError("Pedimos mover la persiana")
        
        pin = coverObj.getPinUp()
        pin_contrario = coverObj.getPinDown()
        invert_relay = coverObj.getInvertRelay()
            
        if state == 2:   # Al bajar es alreves
            pin = coverObj.getPinDown()
            pin_contrario = coverObj.getPinUp()
            
        pinState = gpio_api.gpio_read (pin, invert_relay)

        pinContState = gpio_api.gpio_read (pin_contrario, invert_relay)
        
        if state == 0:
            gpio_api.gpio_control_callback(pin, 0, coverObj, self.cover_read_and_publish)
            gpio_api.gpio_control_callback(pin_contrario, 0, coverObj, self.cover_read_and_publish)
            return
        else:
            if pinState == 1:
                self.cover_read_and_publish(coverObj)
                return
            if pinContState == 1:
                gpio_api.gpio_control_callback(pin_contrario, 0, coverObj, self.cover_read_and_publish)
                time.sleep (1)
            
            #gpio_api.gpio_control(pin, 2, str(relay_time), invert_relay, 1)
            t_persianas = threading.Thread(name='gpio_exec', target=self.cover_exec_thread, args=(pin, coverObj,))
            Logfile.printError("Antes Thread Start")
            t_persianas.start()
            
            #self.cover_read_and_publish(coverObj)
            #t_persianas.join()
            #cover_exec_thread(pin, relay_time, invert_relay)
            #self.cover_read_and_publish(pinUp_number, pinDown_number, name, invert_relay)
            
    def cover_exec_thread(self, pin, coverObj):
        Logfile.printError("Thread Start")
        gpio_api.gpio_control_callback(pin, 2, coverObj, self.cover_read_and_publish)
        
    
    def cover_read_and_publish(self, coverObj): 
        
        Logfile.printError("Read and Publish Start")
        
        pinUp_number = coverObj.getPinUp()
        pinDown_number = coverObj.getPinDown()
        invert_relay = coverObj.getInvertRelay()
        name = coverObj.getName()
        
        pinUp_state = gpio_api.gpio_read (pinUp_number, invert_relay)
        pinDown_state = gpio_api.gpio_read (pinDown_number, invert_relay)
        
        state = 0    # Esto en Home assistant es estado abierto parado. 
                     # En HA hace distincion entre abierto parado y cerado parado, pero aqui no se sabe. 
        
        if pinUp_state == 1:
            state = 1
        if pinDown_state == 1:
            state = 2
        
        '''
        payload = {}
        payload.update({"Position":50})
        json_payload = json.dumps(payload)
        
        szTopic = MQTT_TOPIC_GPIO_COVER_STAT + "/" + name + "/position"
        infot = self.publish(szTopic, json_payload, qos=0, retain=True)
        Logfile.printError("Publish: " + json_payload)
        '''
        payload = {}
        payload.update({"State":state})
        json_payload = json.dumps(payload)
        
        
        szTopic = MQTT_TOPIC_GPIO_COVER_STAT + "/" + name + "/state"
        infot = self.publish(szTopic, json_payload, qos=0, retain=True)
        Logfile.printError("Publish: " + json_payload)
            
    
    
    
    def on_message_bytes(mosq, obj, msg):
        # This callback will only be called for messages with topics that match
        # $SYS/broker/bytes/#
        Logfile.printError("BYTES: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    
    
    def on_message(self, mqttc, obj, msg):
        # This callback will be called for messages that we receive that do not
        # match any patterns defined in topic specific callbacks, i.e. in this case
        # those messages that do not have topics $SYS/broker/messages/# nor
        # $SYS/broker/bytes/#
        Logfile.printError(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    
    def on_publish(self, mqttc, obj, mid):
        Logfile.printError("Publicado con exito. Mid: "+str(mid))
        
    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        Logfile.printError("Subscrito con exito. Mid: "+str(mid))
        
    def on_connect(self, mqttc, obj, flags, rc):
        Logfile.printError("MQTT Conectado. RC: " + str(rc))
        
        self.load_config()
        
        self.subscribe(MQTT_TOPIC_GPIO_COVER_CMD_SUBS, 0)
        self.subscribe(MQTT_TOPIC_GPIO_SWITCH_CMD_SUBS, 0)
        
        
        
        infot = self.publish("stat/mqtt_gw/Power", "online", qos=1, retain=True)
        
    def on_log(self, client, userdata, level, buf):
        Logfile.printError("Paho MQTT: " + str(buf))
        
    def run(self):
        self.message_callback_add(MQTT_TOPIC_GPIO_COVER_CMD_SUBS, self.on_message_gpio_cover_cmd)
        self.message_callback_add(MQTT_TOPIC_GPIO_SWITCH_CMD_SUBS, self.on_message_gpio_switch_cmd)
        self.message_callback_add(MQTT_TOPIC_GPIO_SWITCH_STAT_SUBS, self.on_message_gpio_switch_stat)
        
        self.will_set("stat/mqtt_gw/Power","offline",qos=1 ,retain=True)
        
        try:
            self.connect(MQTT_SERVER, 1883, 60)
        except:
            Logfile.printError("Paho MQTT: Problemas conectando")
        

        self.loop_forever() #Start loop

        
mqttc = MyMQTTClass()
rc = mqttc.run()

# Add message callbacks that will only trigger on a specific subscription match.

#mqttc.message_callback_add("$SYS/broker/bytes/#", on_message_bytes)
#mqttc.on_message = on_message
#mqttc.on_publish = on_publish



