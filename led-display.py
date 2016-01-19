# Requires rgbmatrix.so library: github.com/adafruit/rpi-rgb-led-matrix

import atexit
import Image
import ImageDraw
import ImageFont
import math
import os
import time
from rgbmatrix import Adafruit_RGBmatrix

# Configurable stuff ---------------------------------------------------------

messages = [
  'Happy Birthday!!!',
  'The Big 4 0' ]

width          = 32  # Matrix size (pixels) -- change for different matrix
height         = 32  # types (incl. tiling).  Other code may need tweaks.
matrix         = Adafruit_RGBmatrix(32, 1) # rows, chain length
fps            = 20  # Scrolling speed (ish)

routeColor     = (255, 255, 255) # Color for route labels (usu. numbers)
descColor      = (110, 110, 110) # " for route direction/description
longTimeColor  = (  0, 255,   0) # Ample arrival time = green
midTimeColor   = (255, 255,   0) # Medium arrival time = yellow
shortTimeColor = (255,   0,   0) # Short arrival time = red
minsColor      = (110, 110, 110) # Commans and 'minutes' labels
noTimesColor   = (  0,   0, 255) # No predictions = blue

# TrueType fonts are a bit too much for the Pi to handle -- slow updates and
# it's hard to get them looking good at small sizes.  A small bitmap version
# of Helvetica Regular taken from X11R6 standard distribution works well:
font           = ImageFont.load(os.path.dirname(os.path.realpath(__file__))
                   + '/helvR08.pil')
fontYoffset    = -2  # Scoot up a couple lines so descenders aren't cropped


# Main application -----------------------------------------------------------

# Drawing takes place in offscreen buffer to prevent flicker
image       = Image.new('RGB', (width, height))
draw        = ImageDraw.Draw(image)
currentTime = 0.0
prevTime    = 0.0

# Clear matrix on exit.  Otherwise it's annoying if you need to break and
# fiddle with some code while LEDs are blinding you.
def clearOnExit():
	matrix.Clear()

atexit.register(clearOnExit)

# Populate a list of predict objects (from predict.py) from stops[].
# While at it, also determine the widest tile width -- the labels
# accompanying each prediction.  The way this is written, they're all the
# same width, whatever the maximum is we figure here.
tileWidth = 0                      # Clear list
for m in messages:                        # For each item in stops[] list...
	w = font.getsize(m)[0]
	if(w > tileWidth):                     # If widest yet,
		tileWidth = w                  # keep it
tileWidth += 6                         # Allow extra space between tiles


class tile:
	def __init__(self, x, y, p):
		self.x = x
		self.y = y
		self.message = message  # Corresponding messages[] object

	def draw(self):
		draw.text((self.x, self.y + fontYoffset), self.message, font=font, fill=routeColor)



# Allocate list of tile objects, enough to cover screen while scrolling
tileList = []
if tileWidth >= width: tilesAcross = 2
else:                  tilesAcross = int(math.ceil(width / tileWidth)) + 1

nextMessage = 0  # Index of messages item to attach to tile
for x in xrange(tilesAcross):
	for y in xrange(0, 2):
		tileList.append(tile(x * tileWidth + y * tileWidth / 2,
		  y * 17, messages[nextMessage]))
		nextMessage += 1
		if nextMessage >= len(messages):
			nextMessage = 0

# Initialization done; loop forever ------------------------------------------
while True:

	# Clear background
	draw.rectangle((0, 0, width, height), fill=(0, 0, 0))

	for t in tileList:
		if t.x < width:        # Draw tile if onscreen
			t.draw()
		t.x -= 1               # Move left 1 pixel
		if(t.x <= -tileWidth): # Off left edge?
			t.x += tileWidth * tilesAcross     # Move off right &
			t.message = messages[nextMessage] # assign prediction
			nextMessage += 1                # Cycle predictions
			if nextMessage >= len(predictList):
				nextMessage = 0

	# Try to keep timing uniform-ish; rather than sleeping a fixed time,
	# interval since last frame is calculated, the gap time between this
	# and desired frames/sec determines sleep time...occasionally if busy
	# (e.g. polling server) there'll be no sleep at all.
	currentTime = time.time()
	timeDelta   = (1.0 / fps) - (currentTime - prevTime)
	if(timeDelta > 0.0):
		time.sleep(timeDelta)
	prevTime = currentTime

	# Offscreen buffer is copied to screen
	matrix.SetImage(image.im.id, 0, 0)
