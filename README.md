# Button Box
 
This is my attempt at creating my very own Button Box, fully documented for anyone to follow along if they want to give it ago!

## Finished Project
[![](https://github.com/jackdevonshire/Button-Box/blob/main/resources/img/production/box_final.jpg)](https://www.youtube.com/watch?v=0F-DfAic39k)

## How To Guide?

The whole build process is fully documented in [this Github's wiki](https://github.com/jackdevonshire/Button-Box/wiki)

## Current Features

* Fully Wireless (connects to PC via a REST API over WIFI, using a battery bank this is fully wireless)
* Map buttons to custom keyboard keybinds (multiple keybinds supported)
* Map buttons to run custom python scripts
* Map buttons to command prompt executions (e.g. open chrome to a specific website)
* Map buttons to specific Microsoft Teams functions
* Add requirements for button activiations (e.g. require button X to be activated before button Y can be)
* Set custom display messages after button presses
* Configure multiple modes to map buttons to different actions for different games e.g. (Zoom Meeting, Kerbal Space Program, Microsoft Flight Sim, Photoshop Editing etc)

## Planned Features
These are the features I actively plan to add

## Wish List
These are the features I would love to add given the time
* A fully customisable menu system
* Scrolling messages that aren't limited to 4x20 character lines
* Support for different display types
* Ability to stream live data to LCD screen - currently data can be retrieved from a game API via a custom script, but it can only be displayed for a set period of time and does not automatically refresh
* Make a program for customising the configuration to avoid having to work with raw JSON - Flask Website / Admin Panel?
* Implement [headless WIFI setup](https://github.com/drkmsmithjr/wifi-connect-headless-rpi) so the button box works across different networks
