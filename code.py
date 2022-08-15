'''
This project was inspired by Dave's Garage 'Live' coding of a analog clock
displaying on his LED display.
I do not have his display or hardware.
I do have a Matrix M4 portal and 64x32 display gathering dust.

References:
Dave's Garage: https://www.youtube.com/watch?v=yIpdBVu9xv8
Various Adafruit howto's, API documentation and *gasp* looking at various Adafruit git repos.

All mistakes are my fault.
'''
import time
import math
import busio
import board
import displayio
import framebufferio
import gc
import rgbmatrix
#https://docs.circuitpython.org/projects/matrixportal/en/latest/
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
#https://docs.circuitpython.org/projects/display-shapes/en/latest/index.html
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.line import Line
from digitalio import DigitalInOut
import adafruit_requests as requests
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi

WHITE  = 0xffffff
YELLOW = 0xffff00
BLUE   = 0x0000ff
RED    = 0xff0000
ORANGE = 0xffa500
GREEN  = 0x00FF00
WIDTH  = 32
HEIGHT = 32
centerX = centerY = radius = 0
HOUR = 0
MIN  = 0
SEC  = 0
HOURS_PASSED = 0
network = None

'''
Get wifi details and more from a secrets.py file
Required fileds
  - ssid
  - password
  - timezone
  - aio_username
  - aio_key
'''
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

'''
This was an early test to draw random circles around the screen.
with a passed in color
'''
def randomizeCircles(output, color):
    xp0 = random.randrange( 1, WIDTH-1 )
    yp0 = random.randrange( 1, HEIGHT-1 )
    xmin = min(xp0,WIDTH-1-xp0)
    ymin = min(yp0,HEIGHT-1-yp0)
    radius = max(min(xmin, ymin),1)
    print( "X: %d Y: %d r: %d " % ( xp0, yp0, radius) )
    circle = Circle( xp0, yp0, radius, fill=None, outline=color)
    output.pop(0)
    output.append(circle)

'''
Draw the big clock circle
'''
def drawClockCircle(output):
    circle = Circle(centerX, centerY, radius, fill=None, outline=WHITE )
    output.append(circle)

'''
Draw the center circle
'''
def drawClockCenter(output):
    radius = 1
    circle = Circle(centerX, centerY, radius, fill=None, outline=WHITE)
    output.append(circle)

'''
Draw each of the tics around the clock face
'''
def drawClockHourTics(output):
  z = 0
  while z < 360:
    angle = math.radians(z)
    x2 = int( centerX + (math.sin(angle) * radius) )
    y2 = int( centerY - (math.cos(angle) * radius) )
    x3 = int( centerX + (math.sin(angle) * (radius-2) ) )
    y3 = int( centerY - (math.cos(angle) * (radius-2) ) )

    line = Line( x2, y2, x3, y3, RED )
    output.append( line )

    z += 30

'''
Draw the clock hand
'''
def drawClockSecHand( output ):
    angle = math.radians(SEC * 6)
    x2 = int( centerX + (math.sin(angle) * (radius) ) )
    y2 = int( centerY - (math.cos(angle) * (radius) ) )
    line = Line( centerX, centerY, x2, y2, RED )
    output.append( line )

'''
Draw the minute hand
'''
def drawClockMinHand( output ):
    angle = math.radians(MIN * 6)
    x2 = int( centerX + (math.sin(angle) * (radius-3) ) )
    y2 = int( centerY - (math.cos(angle) * (radius-3) ) )
    line = Line( centerX, centerY, x2, y2, ORANGE )
    output.append( line )

def drawClockHourHand( output ):
    #HOUR can be up to 24 but the math still works because its a circle.
    angle = math.radians(HOUR * 30 + int(MIN/12*6))
    x2 = int( centerX + (math.sin(angle) * (radius/2) ) )
    y2 = int( centerY - (math.cos(angle) * (radius/2) ) )
    line = Line( centerX, centerY, x2, y2, BLUE )
    output.append( line )

def drawClock(display):
  global HOUR
  global MIN
  global SEC
  global HOURS_PASSED
  global network
  curr_time = time.localtime()

  if curr_time.tm_hour != HOUR:
      HOURS_PASSED += 1
  if HOURS_PASSED > 12:
      network.get_local_time()
      HOURS_PASSED = 0

  HOUR = curr_time.tm_hour
  MIN  = curr_time.tm_min
  SEC  = curr_time.tm_sec
  #print("Current time: %d:%d:%d" % (curr_time.tm_hour, curr_time.tm_min, curr_time.tm_sec) )

  palette = displayio.Palette(8)
  palette[1] = 0xffffff
  b1 = displayio.Bitmap(WIDTH, HEIGHT, 8)
  tg1 = displayio.TileGrid(b1, pixel_shader=palette)
  g1 = displayio.Group()
  g1.append(tg1)
  display.show(g1)
  drawClockCircle(g1)
  drawClockCenter(g1)
  drawClockHourTics(g1)
  drawClockSecHand(g1)
  drawClockMinHand(g1)
  drawClockHourHand(g1)

def connectNetwork():
    global network
    #this creates a network object but does not actually connect
    network = Network(status_neopixel=board.NEOPIXEL, debug=False)
    attempt = 0
    while not network._wifi.is_connected:
        try:
            network.connect()
        except ConnectionError as e:
            print("could not connect to AP, retrying: ", e)
            continue
    network.get_local_time()

def main():
  global WIDTH
  global HEIGHT
  global centerX
  global centerY
  global radius

  matrix = Matrix()
  display = matrix.display

  WIDTH = display.width
  HEIGHT = display.height
  centerX = int((WIDTH-1)/2)
  centerY = int((HEIGHT-1)/2)
  radius = min(centerX, centerY)

  drawClock(display)

  display.auto_refresh = True

  connectNetwork()

  while True:
    drawClock(display)
    #Cannt let it run wild. Too much flicker
    time.sleep(1)

if __name__ == "__main__":
    main()