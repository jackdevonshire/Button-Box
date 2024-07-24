# Button Box
 
This is my attempt at creating my very own Button Box, fully documented for anyone to follow along if they want to give it ago!

## Finished Project
[![](https://github.com/jackdevonshire/Button-Box/blob/main/resources/img/production/box_final.jpg)](https://www.youtube.com/watch?v=0F-DfAic39k)

## How To Guide?

The whole build process is fully documented in [this Github's wiki](https://github.com/jackdevonshire/Button-Box/wiki)

## Current Features

* Fully wireless (no wires needed at all with powerbank), with no need to log into Rasperry Pi after first setup
* Map buttons to
  * Keyboard Shortcuts
  * Custom Python Scripts
  * Command Line executions (e.g. open chrome to specific website)
  * Microsoft Teams functions
  * Microsoft Flight Simulator functions
* Ability to set requirements for button activiations (e.g. button X must be on before Y can be activated)
* Custom display messages with support for streaming live messages to the display (e.g. to show game information such as flight simulator air speed)
* Multiple modes for different use cases without programatic switching - can create and switch between as many modes as you like

## Planned Features
These are the features I actively plan to add
* Ability to toggle between different actions each time a button is pressed, rather than just ON/OFF

## Wish List
These are the features I would love to add given the time
* A fully customisable menu system
* Scrolling messages that aren't limited to 4x20 character lines
* Support for different display types
* Make a program for customising the configuration to avoid having to work with raw JSON - Flask Website / Admin Panel?
* Implement [headless WIFI setup](https://github.com/drkmsmithjr/wifi-connect-headless-rpi) so the button box works across different networks
