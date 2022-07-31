from serial.tools import list_ports
from serial import Serial
from crccheck.crc import Crc16Base
from datetime import datetime
import os
import struct

class tapinout:
  ST_INVALID = -1
  ST_GETTING_CONSOLE_STATUS = 0
  ST_WAITING_FOR_LENS_ATTACHMENT = 1
  ST_POWER_ON_LENS = 2
  ST_POWER_OFF_LENS = 3
  ST_GET_LENS_STATUS = 4
  ST_GET_LENS_SETTING = 5
  ST_LOOP_LENS_STATUS = 6

  PROTOCOL_PREAMBLE  = 0x0F
  PROTOCOL_POSTAMBLE = 0xF0

  DEST_LENS = 0
  DEST_CONSOLE = 1

  CMD_IS_LENS_ATTACHED = 0xF7
  CMD_POWER_ON = 0xF8
  CMD_POWER_OFF = 0xF9
  CMD_GET_STATUS = 0xFA
  CMD_GET_SETTINGS = 0XFC

  CMD_ERROR = 0xFF

  CONFIG_MAX_RX_BUFFER_LENGTH = 1000
  CONFIG_TIMEOUT = 3

  OFFSET_STATUS_MODEL = 0x4
  LENGTH_STATUS_MODEL = 16

  def __init__(self, serialDevice=None, debug=False, showPackages=False):
    self.debug = debug
    self.showPackages = showPackages
    self.port = None
    self.nextPackageIndex = 1
    self.lastPackageIndex = 0
    self.rxBuffer = bytearray()
    self.state = self.ST_INVALID
    self.lastRxDateTime = datetime.now()

    self.model = None

    self.crc = Crc16Base()
    self.crc._poly = 0x1021
    self.crc._reflect_input = False
    self.crc._reflect_output = False
    self.crc._initvalue = 0xf1ef
    self.crc._xor_output = 0x0000

    if serialDevice == None:
      ports = list_ports.comports()
      for port in ports:
        if port.vid==0x2CD1 and port.pid==0x0001:
          serialDevice = port.device
          break

    if serialDevice == None:
      print("Unable to find a Tamron Tap-in console")
      os._exit(1)

    self.debugPrint("Found a Tap-in console on: {:s}".format(serialDevice))

    self.debugPrint("Opening Port")
    self.port = Serial(port=serialDevice, timeout=0.05)

    self.changeState(self.ST_GETTING_CONSOLE_STATUS)

    #self.sendPackage(self.DEST_CONSOLE, bytes([self.CMD_POWER_ON, 0]))

    # reply = self.port.read(100)
    # dataAsString = []
    # for i in reply:
    #   dataAsString.append("{:02X}".format(i))
    # print("R: "+":".join(dataAsString))

    # self.sendPackage(1, bytearray([0xF7]))

    # reply = self.port.read(100)
    # dataAsString = []
    # for i in reply:
    #   dataAsString.append("{:02X}".format(i))
    # print("R: "+":".join(dataAsString))


  def debugPrint(self, string):
    if self.debug:
      print(string)

  def packagePrint(self, string):
    if self.showPackages:
      print(string)

  def sendPackage(self, destination, message):
    data = bytearray(struct.pack("<BBHH", 0x0F, self.nextPackageIndex, destination, len(message)))
    for i in message:
      data.append(i)

    crcInt = self.crc.calc(data)
    crcBytes = struct.pack("<H", crcInt)
    data += crcBytes
    data.append(0xF0)

    dataAsString = []
    for i in data:
      dataAsString.append("{:02X}".format(i))
    self.packagePrint("W: "+":".join(dataAsString))

    self.lastPackageIndex = self.nextPackageIndex
    self.nextPackageIndex += 1
    if self.nextPackageIndex > 0xFF:
      self.nextPackageIndex = 1
    self.port.write(data)

  def changeState(self, state):
    self.state = state
    if   state == self.ST_GETTING_CONSOLE_STATUS:
      self.sendPackage(self.DEST_CONSOLE, bytes([self.CMD_GET_STATUS]))
    elif state == self.ST_WAITING_FOR_LENS_ATTACHMENT:
      self.sendPackage(self.DEST_CONSOLE, bytes([self.CMD_IS_LENS_ATTACHED]))
    elif state == self.ST_POWER_ON_LENS:
      self.sendPackage(self.DEST_CONSOLE, bytes([self.CMD_POWER_ON, 0x00]))
    elif state == self.ST_POWER_OFF_LENS:
      self.sendPackage(self.DEST_CONSOLE, bytes([self.CMD_POWER_OFF]))
    elif state == self.ST_GET_LENS_STATUS:
      self.sendPackage(self.DEST_LENS, bytes([self.CMD_GET_STATUS]))
    elif state == self.ST_GET_LENS_SETTING:
      self.sendPackage(self.DEST_LENS, bytes([self.CMD_GET_SETTINGS]))
    elif state == self.ST_LOOP_LENS_STATUS:
      self.sendPackage(self.DEST_LENS, bytes([self.CMD_GET_STATUS]))

    else:
      self.debugPrint("Internal ERROR bad state change (:d)!".format(state))
      self.state = self.ST_GETTING_CONSOLE_STATUS

  def decodeLensStatus(self, payload):
    length = len(payload)
    if len(payload)>self.OFFSET_STATUS_MODEL+self.LENGTH_STATUS_MODEL:
      self.model = ""
      for i in payload[self.OFFSET_STATUS_MODEL: self.OFFSET_STATUS_MODEL+self.LENGTH_STATUS_MODEL]:
        if i != 0:
          self.model += chr(i)
        else:
          break


  def onInputData(self, destination, payload):
    dataAsString = []
    for i in payload:
      dataAsString.append("{:02X}".format(i))
    dataAsString = ":".join(dataAsString)

    if len(payload)>=1:
      [command] = struct.unpack("<B", payload[0:1])

      if   self.state == self.ST_GETTING_CONSOLE_STATUS and command == self.CMD_GET_STATUS:
        self.changeState(self.ST_WAITING_FOR_LENS_ATTACHMENT)
      
      elif self.state == self.ST_WAITING_FOR_LENS_ATTACHMENT and command == self.CMD_IS_LENS_ATTACHED:
        if len(payload)>=2:
          [isConnected] = struct.unpack("<B", payload[1:2])
          if isConnected != 0:
            self.changeState(self.ST_POWER_ON_LENS)
        else:
          self.debugPrint("Is lens attached response too short: "+dataAsString)
      
      elif self.state == self.ST_POWER_ON_LENS and command == self.CMD_POWER_ON:
        #todo check return code
        self.changeState(self.ST_GET_LENS_STATUS)

      elif self.state == self.ST_GET_LENS_STATUS and command == self.CMD_GET_STATUS:
        self.decodeLensStatus(payload)
        self.changeState(self.ST_GET_LENS_SETTING)

      elif self.state == self.ST_GET_LENS_SETTING and command == self.CMD_GET_SETTINGS:
        #self.changeState(self.ST_LOOP_LENS_STATUS)
        self.changeState(self.ST_POWER_OFF_LENS)

      elif self.state == self.ST_LOOP_LENS_STATUS and command == self.CMD_GET_STATUS:
        self.changeState(self.ST_LOOP_LENS_STATUS)

      elif self.state == self.ST_POWER_OFF_LENS and command == self.CMD_POWER_OFF:
        #todo check return code
        {}


      elif command == self.CMD_ERROR:
        self.changeState(self.ST_POWER_OFF_LENS)
      else:
        self.debugPrint("Unexpected data from console in state ({:d}): ".format(self.state)+dataAsString)

  def analyseRxBuffer(self):
    if len(self.rxBuffer) > self.CONFIG_MAX_RX_BUFFER_LENGTH:
      self.rxBuffer = bytearray()
      self.debugPrint("Flushed buffer due to overflow/max size exceeded")
    if len(self.rxBuffer)>=6:
      [preamble, sequenceIndex, destination, length] = struct.unpack("<BBHH", self.rxBuffer[0:6])
      if len(self.rxBuffer) == 6+length+3:
        dataAsString = []
        for i in self.rxBuffer:
          dataAsString.append("{:02X}".format(i))
        self.packagePrint("R: "+":".join(dataAsString))
        dataOk = True
        if sequenceIndex != self.lastPackageIndex:
          self.debugPrint("Out of order package got index {:d} expected {:d}".format(sequenceIndex, self.lastPackageIndex))
          dataOk = False
        
        crc = self.crc.calc(self.rxBuffer[0:-3])
        [crcInData, postAmble] = struct.unpack("<HB", self.rxBuffer[-3:])

        if preamble != self.PROTOCOL_PREAMBLE:
          self.debugPrint("Bad preamble 0x{02X}, internal error should not be possible", preamble)
          dataOk = False

        if postAmble != self.PROTOCOL_POSTAMBLE:
          self.debugPrint("Bad postamble 0x{02X}", postAmble)
          dataOk = False

        if crcInData != crc:
          self.debugPrint("Bad CRC of data 0x{04X} but calculated as 0x{04X}".format(crcInData, crc))
          dataOk = False

        if dataOk:
          self.onInputData(destination, self.rxBuffer[6:-3])
        self.rxBuffer = bytearray()


  def appendRxByte(self, byte):
    if len(self.rxBuffer) >= 1:
      self.rxBuffer.append(byte)
      self.analyseRxBuffer()
    else:
      if byte == self.PROTOCOL_PREAMBLE:
        self.rxBuffer.append(byte)
        self.analyseRxBuffer()

  def animate(self):
    inputData = self.port.read(100)
    if len(inputData)>0:
      for byte in inputData:
        self.appendRxByte(byte)
      self.lastRxDateTime = datetime.now()

    deltaRxTime = datetime.now()-self.lastRxDateTime
    if deltaRxTime.seconds > self.CONFIG_TIMEOUT:
      self.changeState(self.state)