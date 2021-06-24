# Link-Tap

Link-Tap (https://link-tap.com) is a wireless watering system with a cloud located controler. It is accessible through a web site, mobile apps and an API.  

This project is a plugin to be added to the "Domoticz" home automation package (https://www.domoticz.com)

It enables Domoticz to communicate and effectively control a Link-Tap network using its API.

It will report alerts raised by Link-Tap such a leakage, clogged pipes, water cut-off... for further processing


# Installation and Configuration

The plugin must be installed following the usual procedure for any Domoticz plugin: just drop it in the Plugins directory.
Configuration is very simple
- Create an API key associated with your account on Link-Tap (https://www.link-tap.com/#!/api-for-developers)
- Enter you user name and key in the configuration page
- Restart Domoticz
Four devices will be automatically created for each of your link-tap boxes up to a maximum of 255
You can act on those devices in the exact same way you act on any standard Domotics device.

