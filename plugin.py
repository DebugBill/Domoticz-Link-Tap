#!/usr/bin/env python3
# coding: utf-8 -*-
#
# Link-Tap Domoticz plugin
# 
# Author: DebugBill
#
"""
<plugin key="linktap" name="Link-Tap Watering System plugin" author="DebugBill" version="0.1" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://github.com/DebugBill/Link-Tap">
    <description>
        <h2>Link-Tap watering system</h2><br/>
        This plugin will allow Domoticz to read data from the Link-Tap cloud API.
        API key is required
        More info on Link-Tap hardware can be found at https://link-tap.com 
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Feature one...</li>
            <li>Feature two...</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Device Type - What it does...</li>
        </ul>
        <h3>Configuration</h3>
        Configuration options...
    </description>
    <params>
        <param field="Mode1" label="Link-Tap API URL" width="300px" required="true" default="https://www.link-tap.com/"/>
        <param field="Mode2" label="User" width="300px" required="true"/>
        <param field="Mode3" label="Key" width="300px" required="true"/>
        <param field="Mode4" label="Polling internval" width="100px">
            <options>
                <option label="5mn" value="10" default="true"/>
                <option label="10mn" value="20"/>
                <option label="15mn" value="30"/>
                <option label="30mn" value="60" />
            </options>
        </param>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="0" value=0/>
                <option label="1" value=1/>
                <option label="2" value=2/>
                <option label="7" value=7/>
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
        self.timer = 0
        self.token = ''
        self.url = ''
        self.headers = ''

    def onStart(self):
        # 2 sec resolution is enough
        Domoticz.Heartbeat(2)
        self.token = {'username':Parameters["Mode2"],'apiKey':Parameters['Mode3']}
        self.url = Parameters['Mode1'] + 'api/'
        self.headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        Domoticz.Debugging(int(Parameters["Mode6"]))
        Domoticz.Log("onStart called")

        post = requests.post(self.url + 'getAllDevices', json=self.token, headers=self.headers)

        data=json.loads(post.text)
        for gateway in data['devices']:
            print(gateway['name'])
            for taplinker in gateway['taplinker']:
               taplinkerName = taplinker['taplinkerName']
               taplinkerId = taplinker['taplinkerId']
        if (len(Devices) == 0):
            Domoticz.Device(Name=taplinkerName,  Unit=1, TypeName='Waterflow',  DeviceID=taplinkerId).Create()
            Domotics.Status("Device " + taplinkerName + " created")

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called " + str(self.timer) + " times")
        if self.timer == 0:
            DumpAllToLog()
            GetAllDevices()
        self.timer += 1
        Devices[1].Update(nValue=0, sValue='Test', SignalLevel=5, BatteryLevel=100)

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return


def DumpDevicesToLog():
    # Show devices
    Domoticz.Debug("Device count.........: {}".format(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device...............: {} - {}".format(x, Devices[x]))
        Domoticz.Debug("Device Idx...........: {}".format(Devices[x].ID))
        Domoticz.Debug(
            "Device Type..........: {} / {}".format(Devices[x].Type, Devices[x].SubType)
        )
        Domoticz.Debug("Device Name..........: '{}'".format(Devices[x].Name))
        Domoticz.Debug("Device nValue........: {}".format(Devices[x].nValue))
        Domoticz.Debug("Device sValue........: '{}'".format(Devices[x].sValue))
        Domoticz.Debug("Device Options.......: '{}'".format(Devices[x].Options))
        Domoticz.Debug("Device Used..........: {}".format(Devices[x].Used))
        Domoticz.Debug("Device ID............: '{}'".format(Devices[x].DeviceID))
        Domoticz.Debug("Device LastLevel.....: {}".format(Devices[x].LastLevel))
        Domoticz.Debug("Device Image.........: {}".format(Devices[x].Image))


def DumpImagesToLog():
    # Show images
    Domoticz.Debug("Image count..........: {}".format((len(Images))))
    for x in Images:
        Domoticz.Debug("Image '{}'...: '{}'".format(x, Images[x]))


def DumpParametersToLog():
    # Show parameters
    Domoticz.Debug("Parameters count.....: {}".format(len(Parameters)))
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("Parameter '{}'...: '{}'".format(x, Parameters[x]))


def DumpSettingsToLog():
    # Show settings
    Domoticz.Debug("Settings count.......: {}".format(len(Settings)))
    for x in Settings:
        Domoticz.Debug("Setting '{}'...: '{}'".format(x, Settings[x]))


def DumpAllToLog():
    DumpDevicesToLog()
    DumpImagesToLog()
    DumpParametersToLog()
    DumpSettingsToLog()
    return

# API Documentation 1.2: https://www.link-tap.com/#!/api-for-developers

# Get All Devices (Gateway and Taplinker)'s Info
def GetAllDevices():
    data = {'username':Parameters["Mode2"],
    'apiKey':Parameters['Mode3'],}
    url = Parameters['Mode1'] + 'api/getAllDevices'
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    r = requests.post(url, json=data, headers=headers)
#    Domoticz.Error(url)
#    Domoticz.Error(r.text)

#POST https://www.link-tap.com/api/getAllDevices
#Please note: Rate limiting is applied for this API. The minimum interval of calling this API is 5 minutes.

#Body object:
#username: Required. String type. Your LinkTap account's username
#apiKey: Required. String type. Your API key
#Response (success):
#result: 'ok'
#devices: Array of device's info, including gateway and taplinker's online/offline status, device ID and name, remaining battery, wireless signal strength, current watering plan and watering status, etc.

#Explanation of some fields:
#workMode: currently activated work mode. ‘O’ is for Odd-Even Mode, ‘M’ is for Instant Mode, ‘I’ is for Interval Mode, ‘T’ is for 7-Day Mode, ‘Y’ is for Month Mode, ‘N’ means no work mode assigned.
#slot: current watering plan. 'H' represents hour, 'M' represents minute, 'D' represents duration.
#vel: latest flow rate (unit: ml per minute. For G2 and G2S only).
#fall: fall incident flag (boolean. For G2 and G2S only).
#valveBroken: valve failed to open flag (boolean. For G2 and G2S only).
#noWater: water cut-off flag (boolean. For G2 and G2S only).
#Response (failure):
#result: 'error'
#message: various error messages
#Curl example:
#curl -d "username=YourUsername&apiKey=YourApiKey" -X POST https://www.link-tap.com/api/getAllDevices
