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
        <param field="Mode4" label="Polling interval" width="100px">
            <options>
                <option label="5mn" value="15" default="true"/>
                <option label="10mn" value="30"/>
                <option label="15mn" value="45"/>
                <option label="30mn" value="9O" />
            </options>
        </param>
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
        self.timer = -1
        self.token = ''
        self.url = ''
        self.headers = ''
        self.taplinkers = dict() # All taplinkers by id
        self.devices = dict()

    def onStart(self):
        # 2 sec resolution is enough
        Domoticz.Heartbeat(20)
        self.token = {'username':Parameters["Mode2"],'apiKey':Parameters['Mode3']}
        self.url = Parameters['Mode1'] + 'api/'
        self.headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        Domoticz.Debugging(int(Parameters["Mode6"]))
        Domoticz.Debug("onStart called")

        # Build list of devices in Domoticz
        for device in Devices:
            Domoticz.Debug("Device:" + str(device) + " " + str(Devices[device].DeviceID) + " - " + str(Devices[device]))
            self.devices[Devices[device].DeviceID] = device
            Domoticz.Debug("List of devices: " + Devices[device].DeviceID +  "," + str(device))

        # Build list of devices on API and create missing ones
        post = requests.post(self.url + 'getAllDevices', json=self.token, headers=self.headers)
        data=json.loads(post.text)
        for gateway in data['devices']:
            gatewayName = gateway['name']
            for taplinker in gateway['taplinker']:
                self.taplinkers[taplinker['taplinkerId']] = taplinker['taplinkerName']
                if not taplinker['taplinkerId'] in self.devices:
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
                    Domoticz.Device(Name=gatewayName + " - " + taplinker['taplinkerName'],  Unit=hole, TypeName='Waterflow',  DeviceID=taplinker['taplinkerId']).Create()
                    self.device[taplinker['taplinkerId']] = hole 
                    Domoticz.Log("Device " + taplinker['taplinkerName'] + " with ID " + taplinker['taplinkerId'] + " created")

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
        self.timer += 1
        Domoticz.Debug("onHeartbeat called " + str(self.timer) + " times")
        if self.timer % int(Parameters['Mode4']) == 0:
            post = requests.post(self.url + 'getAllDevices', json=self.token, headers=self.headers)
            data=json.loads(post.text)
            for gateway in data['devices']:
                for taplinker in gateway['taplinker']:
                    taplinkerId = taplinker['taplinkerId']
                    if taplinkerId in self.devices:
                        Domoticz.Log("Updating device: " + taplinker['taplinkerName'] + " with ID " + taplinkerId)
                        Devices[self.devices[taplinkerId]].Update(nValue=0, sValue='Test', SignalLevel=int(taplinker['signal']), BatteryLevel=int(taplinker['batteryStatus'][:-1]))

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


