#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Patrick Marlier <patrick.marlier@gmail.com>
# Copyright (c) 2014 Mascha Kurpicz <mascha.kurpicz@gmail.com>
#                    University of Neuchatel, Switzerland
#
# This file is part of powerspy.py.
#
# powerspy.py is free software; you can redistribute it and/or modify it under
# the terms of the Lesser GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# powerspy.py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# Lesser GNU Lesser General Public License for more details.
#
# You should have received a copy of the Lesser GNU Lesser General Public License
# along with powerspy.py.  If not, see <http://www.gnu.org/licenses/>.

import logging
import bluetooth
import struct  # conversion of type
import re      # matching responses
import math    # sqrt
import signal  # signal handler
import sys     # system exit
import time    # sleep/time

# All powerspy commands
CMD_ID = '?'
CMD_CAPTURE_LENGTH = 'L'
CMD_TRIGGER_CONF = 'T'
CMD_RESET = 'R'
CMD_EEPROM_READ = 'V'
CMD_EEPROM_WRITE = 'W'
CMD_START = 'S'
CMD_CANCEL = 'C'
CMD_FREQUENCY = 'F'
CMD_ASCII = 'A'
CMD_BINARY = 'B'
CMD_RT = 'J'
CMD_RT_STOP = 'Q'
CMD_RTC_SET = 'E'
CMD_RTC_GET = 'G'
CMD_LOG_PERIOD = 'M'
CMD_LOG_START = 'O'
CMD_LOG_STOP = 'P'
CMD_FILE_LIST = 'U'
CMD_FILE_DEL = 'Y'
CMD_FILE_GET = 'X'

# Generic responses
CMD_OK = 'K'
CMD_FAILED = 'Z'

# Global variable for the ctrl+c handler
running = True

# Constants
DEFAULT_TIMEOUT = 3.0 # secs (float allowed, timeout to receive response from PowerSpy)
DEFAULT_INTERVAL = 1.0 # secs (float allowed, interval between each output)

class PowerSpy:
  def __init__ (self):
    self.sock = None
    self.status = None
    self.pll_locked = None
    self.trigger_status = None
    self.sw_version = None
    self.hw_version = None
    self.hw_serial = None
    self.uscale_factory = self.iscale_factory = self.pscale_factory = None
    self.uscale_current = self.iscale_current = self.pscale_current = None
    self.frequency = None

  def connect(self, address):
    if self.sock != None:
      logging.warning("Already connected")
      return 1
    self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    logging.debug("Connecting to %s..." % str(address))
    try:
      self.sock.connect(address)
    except bluetooth.btcommon.BluetoothError as error:
      logging.error("Cannot connect to %s (%s)" % (str(address), str(error)))
      return 1

    # Should not set timeout before connect (connect may require more time)
    self.sock.settimeout(DEFAULT_TIMEOUT)
    return 0

  def sendCmd(self, c):
    assert(self.sock != None)
    # All powerspy commands are tagged with < >
    buf = '<%s>' % c
    logging.debug("SEND: %s" % buf)
    self.sock.sendall(buf)

  def recvCmd(self, size = 1):
    assert(self.sock != None)
    # All powerspy commands are tagged with < >
    buf = ""
    while True:
      try:
        r = self.sock.recv(size)
        # then read one by one
        size = 1
      except bluetooth.btcommon.BluetoothError as error:
        # TODO probably timeout but there is no specific exception for it
        logging.warning("Maybe timeout? %s" % error)
        break
      # FIXME what to do for multiple message? keep it in buffer...
      buf = "%s%s" % (buf,r)
      mat = re.search('<(.*)>', buf, re.MULTILINE)
      if mat:
        buf = mat.group(1)
        logging.debug("RECV: <%s>" % buf)
        break
    return buf

  # Check identity
  def checkID(self):
    self.sendCmd(CMD_ID)
    s = self.recvCmd(23)
    mat = re.match('POWERSPY(.)(.{12})', s)
    if not mat:
      # Unable to process response for ID
      return False
    self.status = mat.group(1)
    # 'R': Ready
    # 'W': Waiting trigger
    # 'A': Acquisition in progress
    # 'C': Acquisition complete
    # 'T': FIXME Undocumented status, triggered? Realtime activated?
    extra = mat.group(2)
    self.pll_locked     = extra[0:2]  # PLL Locked (0x01 if locked, 0x00 if not)
    self.trigger_status = extra[2:4]  # Trigger status (2 characters)
    self.sw_version     = extra[4:6]  # SW version (1 byte / 2 characters)
    self.hw_version     = extra[6:8]  # HW version (1 byte / 2 characters)
    self.hw_serial      = extra[8:12] # HW serial number (2 bytes / 4 characters)
    logging.debug('status: %s pll_locked: %s trigger_status: %s sw_version: %s hw_version: %s hw_serial: %s' % (self.status, self.pll_locked, self.trigger_status, self.sw_version, self.hw_version, self.hw_serial))
    return True


  # Read EEPROM float (values: must be an array of 4 elements)
  def get_eeprom_float(self, values):
    val = ""
    for i in values:
      self.sendCmd(CMD_EEPROM_READ + i)
      val += self.recvCmd(4)
    # Format 32 bits, REAL4
    # < indicates little-endian encoding
    f = struct.unpack('<f', val.decode("hex"))
    return f[0]

  # Factory correction voltage coefficient
  def get_uscale_factory(self):
    self.uscale_factory = self.get_eeprom_float(["02", "03", "04", "05"])
    return self.uscale_factory

  # Factory correction current coefficient
  def get_iscale_factory(self):
    self.iscale_factory = self.get_eeprom_float(["06", "07", "08", "09"])
    return self.iscale_factory

  # Actual correction voltage coefficient
  def get_uscale_current(self):
    self.uscale_current = self.get_eeprom_float(["0E", "0F", "10", "11"])
    return self.uscale_current

  # Actual correction current coefficient
  def get_iscale_current(self):
    self.iscale_current = self.get_eeprom_float(["12", "13", "14", "15"])
    return self.iscale_current

  def calc_pscale(self):
    if self.pscale_factory == None:
      if self.uscale_factory != None and self.iscale_factory != None:
        self.pscale_factory = self.uscale_factory * self.iscale_factory
    if self.pscale_current == None:
      if self.uscale_current != None and self.iscale_current != None:
        self.pscale_current = self.uscale_current * self.iscale_current

  def get_frequency(self):
    self.sendCmd(CMD_FREQUENCY)
    f = self.recvCmd(7)
    f = struct.unpack('>H', f[1:].decode("hex"))
    if self.hw_version == "02":
      self.frequency = 1000000.0 / f[0]
    else:
      self.frequency = 1382400.0 / f[0]
    return self.frequency

  # check and get PowerSpy parameters
  def init(self):
    if not self.checkID():
      logging.error("Cannot identify the device")
      self.close()
      return False
    if self.status != 'R' and self.status != 'C':
      # Device is busy let's force it to abort
      logging.warning("Device is in status %s, try to stop running action.", self.status)
      self.rt_stop()
      self.acquisition_stop()
    self.get_frequency()
    logging.debug("frequency:%.8f" % (self.frequency))
    # Retrieve device parameters
    self.get_uscale_factory()
    self.get_iscale_factory()
    self.get_uscale_current()
    self.get_iscale_current()
    self.calc_pscale()
    logging.debug("uscale_factory:%.8f iscale_factory:%.8f pscale_factory:%.8f" % (self.uscale_factory, self.iscale_factory, self.pscale_factory))
    logging.debug("uscale_current:%.8f iscale_current:%.8f pscale_current:%.8f" % (self.uscale_current, self.iscale_current, self.pscale_current))
    return True

  # deinitialize the PowerSpy device and close the serial port
  def close(self):
    if self.sock != None:
      # TODO deinit, if status ACQUIRING, ...
      self.sock.close()
      self.sock = None

  def acquisition_start(self):
    self.sendCmd(CMD_START)
    a = self.recvCmd(3)
    if a != CMD_OK:
      logging.error('CMD_START FAILED')
      return False
    return True

  def acquisition_stop(self):
    self.sendCmd(CMD_CANCEL)
    a = self.recvCmd(3)
    # FIXME Documentation says it returns CMD_OK but always get CMD_FAILED
    #if a != CMD_OK:
    #  logging.error('CMD_CANCEL FAILED')
    #  return False
    return True

  # Start real time monitoring with specific interval
  # rt_stop() must be called if the function succeed
  def rt_start(self, interval = DEFAULT_INTERVAL):
    # big interval will make the timeout to be reached
    if interval >= DEFAULT_TIMEOUT:
       logging.warning("Consider increasing the timeout value or decrease the interval")
    # Convert the interval using frequency to find the averaging periods
    avg_period = int(interval * self.frequency)
    # TODO check if not overflow 255 for v1 and 65535 for v2
    if self.hw_version == "02":
      # PowerSpy v1 (hw_version == "02") format for CMD_RT <JXX>
      self.sendCmd("%s%02X" % (CMD_RT, avg_period))
    else:
      self.sendCmd("%s%04X" % (CMD_RT, avg_period))
    a = self.recvCmd(3)
    if a != CMD_OK:
      logging.error('CMD_RT FAILED')
      return False
    return True

  # Display the column header for rt_read()
  def rt_cols(self):
    print("# timestamp\tV\tA\tW\tV\tA")

  # Read monitored values and display them
  def rt_read(self):
    # Periodically read the input
    res = self.recvCmd(40) # 38 without the end of line or 40 with
    # RMS (Root Mean Square)
    # square of the RMS voltage (8 hex digits)
    # square of the RMS current (8 hex digits)
    # square of the RMS power (8 hex digits)
    # peak voltage (4 hex digits)
    # peak current (4 hex digits)
    values = res.split()
    # Should be an array of 5 elements
    if len(values) != 5:
      logging.warning("Invalid response")
      return [0,0,0,0,0]
    # convert string to values
    conv = []
    for i in range(5):
      hexa = values[i].decode("hex")
      if len(hexa) == 2:
        fmt = '>H'
      elif len(hexa) == 4:
        fmt = '>I'
      else:
        logging.error("Invalid data %d %s" % (len(hexa), hexa))
      conv.insert(i, struct.unpack(fmt, hexa)[0])

    # Note: Initially scale_factory and scale_current are the same but in case of user calibration, scale_current must be used
    # Corrected RMS voltage = squareroot [ (square of the RMS voltage returned by fonction) x (Uscale_current)2 ]
    # Corrected RMS current = squareroot [ (square of the RMS current returned by fonction) x (Iscale_current)2 ]
    # Corrected RMS power = (square of the RMS current returned by fonction) x (Uscale_factory) x (Iscale_current)
    # Corrected peak voltage = peak voltage returned by fonction x Uscale_current
    # Corrected peak current = peak current returned by fonction x Iscale_current
    voltage = math.sqrt(self.uscale_current * self.uscale_current * conv[0])
    current = math.sqrt(self.iscale_current * self.iscale_current * conv[1])
    power = self.pscale_current * conv[2]
    pvoltage = self.uscale_current * conv[3]
    pcurrent = self.iscale_current * conv[4]

    print("%0.3f\t%0.3f\t%0.3f\t%0.3f\t%0.3f\t%0.3f" % (time.time(), voltage, current, power, pvoltage, pcurrent))

    return [voltage, current, power, pvoltage, pcurrent]

  # Stop the real time monitoring
  def rt_stop(self):
    # TODO can check status before to stop
    self.sendCmd(CMD_RT_STOP)
    # flush input because it can have still data to read
    while True:
      a = self.recvCmd(3)
      if a == CMD_FAILED:
        logging.error('CMD_RT_STOP FAILED')
        return False
      if a == CMD_OK:
        return True
    return True

# Signal handler to exit properly on SIGINT
def exit_gracefully(signal, frame):
  global running
  running = False

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Alciom PowerSpy reader.')
  # TODO can add mac address checker and normalizer
  parser.add_argument('device_mac', metavar='MAC', help='MAC address of the PowerSpy device.')
  parser.add_argument('-i', '--interval', type=float, default=1.0, help='Interval between each measurement.')
  parser.add_argument('-v', '--verbose', action='count', help='Verbose mode.')
  parser.add_argument('-t', '--time', type=int, default=0, help='Time of execution (seconds). 0 means running indefinitely.')
  # in case of release
  #parser.add_argument('--version', action='version', version='%(prog)s unreleased')
  args = parser.parse_args()

  if args.verbose > 0:
    logging.basicConfig(level=logging.DEBUG)

  # Setup signal handler for CTRL-C
  signal.signal(signal.SIGINT, exit_gracefully)

  dev = PowerSpy()
  if args.device_mac == "simulator":
    import powerspysimulator
    dev.sock = powerspysimulator.Simulator()
  else:
    # TODO set port to 1 but can be different?
    port = 1
    err = dev.connect((args.device_mac, port))
    if err:
      print("Cannot connect to the device %s" % args.device_mac)
      sys.exit(1)

  if not dev.init():
    print("Device cannot be initialized")
    sys.exit(1)
  dev.acquisition_start()
  # Wait at least the interval to get enough values
  time.sleep(args.interval)
  dev.rt_start(args.interval)

  dev.rt_cols()
  endsat = time.time() + args.time
  while (running and (args.time == 0 or time.time() < endsat)):
    dev.rt_read()
  dev.rt_stop()
  dev.acquisition_stop()
  dev.close()

