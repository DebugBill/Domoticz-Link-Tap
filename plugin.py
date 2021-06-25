#!/usr/bin/env python3
# coding: utf-8 -*-
#
# Link-Tap Domoticz plugin
#
# API Documentation 1.2: https://www.link-tap.com/#!/api-for-developers
#
# Author: DebugBill June 2021
#
"""
<plugin key="linktap" name="Link-Tap Watering System" author="DebugBill" version="0.1" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://github.com/DebugBill/Link-Tap">
    <description>
        <h2>Link-Tap watering system</h2><br/>
        This plugin will allow Domoticz to read data from the Link-Tap cloud API. <br/>
        API key from LinkTap is required.<br/>
        More info on Link-Tap hardware can be found at https://link-tap.com<br/><br/>
        <h3>Features</h3>
        Several devices are created
        <ul style="list-style-type:square">
            <li>Reads waterflow counters and stores data</li>
            <li>Sets watering modes using preconfigures settings in Watertap</li>
            <li>Turns watering On and Off</li>
            <li>Displays alerts if any</li>
        </ul>
        <h3>Devices</h3>
        Five devices are created for each Linkt-Tap box
        <ul style="list-style-type:square">
            <li>Mode: allows for selecting the watering more</li>
            <li>Status: Displays alerts collected by Link-Tap</li>
            <li>Flow: Instant flow in l/mn</li>
            <li>Volume: Total volume of last watering cycle</li>
            <li>On/Off: Immediate On or Off in instant mode</li>
        </ul>
        <h3>Configuration</h3>
    </description>
    <params>
        <param field="Username" label="User" width="300px" required="true"/>
        <param field="Password" label="Key" width="300px" required="true"/>
        <param field="Mode1" label="Return to previous wateting mode after manual mode" width="50px">
            <options>
                <option label="True" value=true default="true"/>
                <option label="False" value=false/>
            </options>
        </param>
        <param field="Mode2" label="Maximum Watering duration before automatic turn off (1 - 1439 sec)" width="40px" required="true" default=1439 />
        <param field="Mode6" label="Debug Level" width="300px">
            <options>
                <option label="None" value="0"  default="true"/>
                <option label="Plugin Verbose" value="2"/>
                <option label="Domoticz Plugin" value="4"/>
                <option label="Domoticz Devices" value="8"/>
                <option label="Domoticz Connections" value="16"/>
                <option label="Verbose+Plugin+Devices" value="14"/>
                <option label="Verbose+Plugin+Devices+Connections" value="30"/>
                <option label="Domoticz Framework - All (useless but in case)" value="1"/>
            </options>
	</param>
    </params>
</plugin>
"""
import Domoticz
import json
import requests

class BasePlugin:
    enabled = False
    def __init__(self):
        self.version = '0.1'
        self.timer = 0
        self.token = ''
        self.url = 'https://www.link-tap.com/api/'
        self.taplinkers = dict() # All taplinkers by id
        self.devices = dict()
        self.gateways = dict()
        self.types  = {'flow':'-243-30', 'volume':'-243-33', 'modes':'-244-62', 'status':'-243-22', 'on-off':'-244-73'}
        self.images = {'modes':20, 'status':20}
        self.headers = {'Content-type': 'application/json', 'Accept': 'text/plain'} 
        self.getAllDevices = dict()

    def onStart(self):
        # Rate limiting is in place at Link-Tap, highest freq is 15 sec
        Domoticz.Heartbeat(15)
        self.token = {'username':Parameters["Username"],'apiKey':Parameters['Password']}
        Domoticz.Debugging(int(Parameters["Mode6"]))
        Domoticz.Debug("onStart called")
        self.CreateDevices()
        self.CheckVersion()

    def onCommand(self, Unit, Command, Level, Hue):
        type = '-' + str(Devices[Unit].Type) + '-' + str(Devices[Unit].SubType)
        taplinkerId = Devices[Unit].DeviceID
        Domoticz.Debug("onCommand called for device " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        if type == self.types['modes']:
            if Level == 10: method = "activateIntervalMode"
            elif Level == 20: method = "activateOddEvenMode"
            elif Level == 30: method = "activateSevenDayMode"
            elif Level == 40: method = "activateMonthMode"
            else: 
                Domoticz.Error("Unknown level received (" + str(Level) + ") for device id " + str(Unit))
                return
            token = {'username':Parameters["Username"],'apiKey':Parameters['Password'], 'gatewayId':self.gateways[taplinkerId], 'taplinkerId':taplinkerId}
            post = requests.post(self.url + method, json=token, headers=self.headers, timeout=2)
            status = json.loads(post.text)
            if status['result'] == 'ok':
                Domoticz.Log('Command sent successfully to Taplinker ' + taplinkerId)
            elif status['result'] == 'error':
                Domoticz.Error('Error sending command to taplinker ' + taplinkerId + ': ' + status['message'])
            else:
                Domoticz.Error('Error while retreiving datafor Taplinker ' + taplinkerId + ', result code is: ' + status['result'])
        elif type == self.types['on-off']:
            method = "activateInstantMode"
            if Command == 'On': switch = True
            elif Command == 'Off': switch = False
            else:
                Domoticz.Error("Unknown command received (" + Command + ") for device id " + str(Unit))
                return
            duration = int(Parameters["Mode2"])
            if duration > 1439 or duration < 1: duration = 1439
            token = {'username':Parameters["Username"],'apiKey':Parameters['Password'], 'gatewayId':self.gateways[taplinkerId], 'taplinkerId':taplinkerId, 'action':switch, 'duration':duration, 'autoBack':Parameters["Mode1"]}
            post = requests.post(self.url + method, json=token, headers=self.headers, timeout=2)
            status = json.loads(post.text)
            if status['result'] == 'ok':
                Domoticz.Log('Command sent successfully to Taplinker ' + taplinkerId)
                Devices[Unit].Update(nValue=switch, sValue="Test")
            elif status['result'] == 'error':
                Domoticz.Error('Error sending command to taplinker ' + taplinkerId + ': ' + status['message'])
            else:
                Domoticz.Error('Error while retreiving datafor Taplinker ' + taplinkerId + ', result code is: ' + status['result'])


    def onHeartbeat(self):
        self.timer += 1
        Domoticz.Debug("onHeartbeat called ")
        if self.timer % 480 == 0: self.CheckVersion() #Every 2 hours, check if new version is available
        if self.timer %  20 == 0: # Rate limiting is 5mn on this method call
            self.CreateDevices() # Call just in case hardware is added or devices are removed
        if self.timer %  2 == 0: # Rate limiting is 30 seconds
            for gateway in self.getAllDevices['devices']:
                for taplinker in gateway['taplinker']:
                    taplinkerId = taplinker['taplinkerId']
                    if taplinkerId + self.types['flow'] or taplinkerId + self.types['volume'] or taplinkerId + self.types['status'] in self.devices:
                        token = {'username':Parameters["Username"],'apiKey':Parameters['Password'],'taplinkerId':taplinkerId}
                        post = requests.post(self.url + 'getWateringStatus', json=token, headers=self.headers, timeout=2)
                        status = json.loads(post.text)
                        vel = 0
                        vol = 0
                        currentStatus = ''
                        if status['result'] == 'ok':
                            updateNeeded = False
                            if status['status'] is not None:
                                vel = round(int(status['status']['vel'])/1000)
                                vol = round(int(status['status']['vol'])/1000)
                                currentStatus = 'Watering'
                                if Devices[self.devices[taplinkerId + self.types['on-off']]].nValue == False:
                                    updateNeeded = True
                                    Devices[self.devices[taplinkerId + self.types['on-off']]].Update(nValue = True, sValue = 'On')
                            else:
                                currentStatus = 'Idle'
                                if Devices[self.devices[taplinkerId + self.types['on-off']]].nValue == True:
                                    updateNeeded = True
                                    Devices[self.devices[taplinkerId + self.types['on-off']]].Update(nValue = False, sValue = 'Off')
                        elif status['result'] == 'error':
                            Domoticz.Error('Error while retreiving data: ' + status['message'])
                        else:
                            Domoticz.Error('Error while retreiving data, result is: ' + status['result'])
                        if  taplinkerId + self.types['flow'] in self.devices:
                            Devices[self.devices[taplinkerId + self.types['flow']]].Update(nValue=0, sValue=str(vel), BatteryLevel=int(taplinker['batteryStatus'][:-1]), SignalLevel=int((taplinker['signal']+5)/10))
                        if  taplinkerId + self.types['volume'] in self.devices and currentStatus == 'Watering': # Don't reset volume at the end of a watering cycle
                            Devices[self.devices[taplinkerId + self.types['volume']]].Update(nValue=0, sValue=str(vol), BatteryLevel=int(taplinker['batteryStatus'][:-1]), SignalLevel=int((taplinker['signal']+5)/10))
                        Domoticz.Log('Updated device counters: ' + taplinker['taplinkerName'] + ' with ID ' + taplinkerId + '. Vel is ' + str(vel) + ', volume is ' + str(vol) + '. Signal is: ' + str(taplinker['signal']))
                        if self.timer %  20 == 0 or updateNeeded: #Status info has been updated are change on/off has been detected 
                            alert = 1
                            alertText = ' Alert(s):'
                            #0 : Grey
                            #1 : Green
                            #2 : Greenish Yellow
                            #3 : Orange
                            #4 : Red
                            if taplinker['fall']:
                                alert =4
                                alertText +=' fall'
                            if taplinker['noWater']:
                                alert =4
                                alertText += ' No water'
                            if taplinker['leakFlag']:
                                alert =4
                                alertText += ' Leak'
                            if taplinker['clogFlag']:
                                alert =4
                                alertText += ' Clog'
                            if taplinker['valveBroken']:
                                alert =4
                                alertText +=' Valve broken'
                            workMode = taplinker['workMode']
                            if workMode == 'M':
                                currentStatus += ' Manual mode'
                            elif workMode == 'I':
                                currentStatus += ' Intervals mode'
                            elif workMode == 'O':
                                currentStatus += ' Odd/Even mode'
                            elif workMode == 'T':
                                currentStatus += ' Seven Days mode'
                            elif workMode == 'N':
                                currentStatus +=  ' Month mode'
                            else:
                                currentStatus += ' Unknown mode ' + workMode
                            if alert == 4: 
                                currentStatus += alertText
                            Devices[self.devices[taplinkerId + self.types['status']]].Update(nValue=alert, sValue=currentStatus, SignalLevel=int((taplinker['signal']+5)/10), BatteryLevel=int(taplinker['batteryStatus'][:-1]))
                            Domoticz.Log('Updated device status: ' + taplinker['taplinkerName'] + ' with ID ' + taplinkerId +'. Status is ' + currentStatus)

    # Function to create devices from LinkTap and refresh plugin's internal structures
    # Rate limiting is in place at LinkTap, minimum interval is 5 minutes
    def CreateDevices(self):
        self.devices = dict()
        # Build list of current devices in Domoticz
        for device in Devices:
            Domoticz.Debug("Current device:" + str(device) + " " + str(Devices[device].DeviceID) + " " + str(Devices[device].Type)+ " " + str(Devices[device].SubType) + " " + str(Devices[device].SwitchType)+ " - " + str(Devices[device]))
            self.devices[Devices[device].DeviceID + '-' + str(Devices[device].Type) + '-' + str(Devices[device].SubType)] = device
    
        # Build list of devices on API and create missing ones
        post = requests.post(self.url + 'getAllDevices', json=self.token, headers=self.headers, timeout=2)
        self.getAllDevices = json.loads(post.text)
        for gateway in self.getAllDevices['devices']:
            gatewayName = gateway['name']
            for taplinker in gateway['taplinker']:
                taplinkerId = taplinker['taplinkerId']
                self.gateways[taplinkerId] = gateway['gatewayId']
                self.taplinkers[taplinkerId] = taplinker['taplinkerName']
                for type in self.types:
                    if not taplinkerId + self.types[type] in self.devices:
                        # Find a hole in the device IDs
                        hole = 1
                        if len(Devices) > 0:
                            sortedIDs = sorted(self.devices.values())
                            previous = 0
                            for id in sortedIDs:
                                if id != previous+1:
                                    hole = previous+1
                                    break
                                else:
                                    previous = id
                                    hole = id + 1
                        if hole > 255:
                            Domoticz.Error("Maximum of 255 devices per hardware has been reached, can't create any more devices")
                            return
                        if type == 'flow':
                            Domoticz.Device(Name=gatewayName + " - " + taplinker['taplinkerName'] + ' - Flow',  Unit=hole, Type=243, Subtype=30, DeviceID=taplinkerId).Create()
                        elif type == 'volume':
                            Domoticz.Device(Name=gatewayName + " - " + taplinker['taplinkerName'] + ' - Volume',  Unit=hole, Type=243, Subtype=33, Switchtype=2, DeviceID=taplinkerId).Create()
                        elif type == 'modes':
                            Options = {"Scenes": "||||", "LevelActions": "||||", "LevelNames": "0|Intervals|Odd-Even|Seven days|Months", "LevelOffHidden": "true", "SelectorStyle": "1"}
                            Domoticz.Device(Name = gatewayName + " - " + taplinker['taplinkerName'] + " - Watering Modes",  DeviceID=taplinkerId, Image = 20, Unit=hole, Type=244, Subtype=62 , Switchtype=18, Options = Options).Create()
                        elif type == 'status':
                            Domoticz.Device(Name = gatewayName + " - " + taplinker['taplinkerName'] + " - Status",  DeviceID=taplinkerId, Unit=hole, TypeName='Alert').Create()
                        elif type == 'on-off':
                            Domoticz.Device(Name = gatewayName + " - " + taplinker['taplinkerName'] + " - On/Off",  DeviceID=taplinkerId, Unit=hole, Type=244, Subtype=73 , Switchtype=0, Image=20).Create()
                        else :
                            Domoticz.Error("Device type " + type + " not implemented")
                            return
                        self.devices[taplinkerId + self.types[type]] = hole
                        Domoticz.Log("Device " + taplinker['taplinkerName'] + " of type '" + type + "' with ID " +taplinkerId + " created")

    # Function to check on GitHub if a new release of the plugin is available
    def CheckVersion(self):
        post = requests.get('https://api.github.com/repos/DebugBill/Link-Tap/releases/latest', headers={'Accept': 'application/vnd.github.v3+json'}, timeout=2)
        if 'tag_name' in json.loads(post.text): 
            version = str(json.loads(post.text)['tag_name'])
            if version != self.version:
                Domoticz.Error("Newer version of Link-Tap plugin is available: " + version + ". Current version is: " + self.version)
            else:
                Domoticz.Log("Current version (" + self.version + ") of Link-Tap plugin is up to date")
        else: 
            Domoticz.Log('Could not contact GitHub to check for latest version')

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()
