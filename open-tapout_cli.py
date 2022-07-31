#!/usr/bin/python

from tapinout import tapinout
from time import sleep

console = tapinout(debug=True, showPackages=False)
lastState = None

knownModels = {'A032': 'Tamron SP 24-70mm F/2.8 Di VC USD G2'}

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