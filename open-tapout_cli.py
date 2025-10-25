#!/usr/bin/python

from tapinout import tapinout
from time import sleep

console = tapinout(debug=True, showPackages=False)
lastState = None

# Ref: https://www.tamron.com/global/consumer/support/download/firmware/
knownModels = {
    # APS-C format DSLR (Di II)
    'B016': 'Tamron 16-300mm F/3.5-6.3 Di II VC PZD MACRO',
    'B023': 'Tamron 10-24mm F/3.5-4.5 Di II VC HLD',
    'B028': 'Tamron 18-400mm F/3.5-6.3 Di II VC HLD',

    # Full-frame format DSLR (Di)
    'A009': 'Tamron SP 70-200mm F/2.8 Di VC USD',
    'A010': 'Tamron 28-300mm F/3.5-6.3 Di VC PZD',
    'A011': 'Tamron SP 150-600mm F/5-6.3 Di VC USD',
    'A012': 'Tamron SP 15-30mm F/2.8 Di VC USD',
    'A022': 'Tamron SP 150-600mm F/5-6.3 Di VC USD G2',
    'A025': 'Tamron SP 70-200mm F/2.8 Di VC USD G2',
    'A030': 'Tamron SP 70-300mm F/4-5.6 Di VC USD (Tungsten Silver Ring Design)',
    'A032': 'Tamron SP 24-70mm F/2.8 Di VC USD G2',
    'A034': 'Tamron 70-210mm F/4 Di VC USD',
    'A035': 'Tamron 100-400mm F/4.5-6.3 Di VC USD',
    'A037': 'Tamron 17-35mm F/2.8-4 Di OSD',
    'A041': 'Tamron SP 15-30mm F/2.8 Di VC USD G2',
    'F004': 'Tamron SP 90mm F/2.8 Di MACRO 1:1 VC USD',
    'F012': 'Tamron SP 35mm F/1.8 Di VC USD',
    'F013': 'Tamron SP 45mm F/1.8 Di VC USD',
    'F016': 'Tamron SP 85mm F/1.8 Di VC USD',
    'F017': 'Tamron SP 90mm F/2.8 Di MACRO 1:1 VC USD',
    'F045': 'Tamron SP 35mm F/1.4 Di USD',
}

def printLensModel():
  global console, knownModels
  model = console.model
  humanReadable = "???"
  if str(model) in knownModels:
    humanReadable = knownModels[model]
  print("Lens Model: "+str(model)+" aka. '"+humanReadable+"'")

doRun = True

while(doRun):
  console.animate()
  newState = console.state
  if newState != lastState:
    if   newState == console.ST_GETTING_CONSOLE_STATUS:
      print("Getting TAP-in console information")
    elif newState == console.ST_WAITING_FOR_LENS_ATTACHMENT:
      print("Waiting for lens attachment")
    elif newState == console.ST_POWER_ON_LENS:
      print("Powering on the lens")
    elif newState == console.ST_POWER_OFF_LENS:
      print("Powering the lens off")
      doRun = False
    elif newState == console.ST_GET_LENS_STATUS:
      print("Obtaining lens information")
    elif newState == console.ST_GET_LENS_SETTING:
      print("Obtaining lens setting")
    elif newState == console.ST_LOOP_LENS_STATUS:
      print("Entered idle loop")
  lastState = newState
  sleep(0.5)

sleep(2)
print("")
printLensModel()