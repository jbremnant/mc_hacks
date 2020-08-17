#!/home/jbkim/anaconda3/bin/python
import os, sys
sys.path.append('/opt/minecraft/tools/mcpi_hacks')
import math
import time
import argparse
import mcpi.minecraft as minecraft
import mcpi.block as block
import minecraftstuff as mcstuff

# Block Orientation
#   x : width
#   y : height
#   z : depth

def do_where(args, mc, do_print=True):
  elist = mc.getPlayerEntityIds()
  data = []
  for e in elist:
    pos = mc.entity.getTilePos(e)
    p = {'name': mc.entity.getName(e), 'id': e,
         'x': int(pos.x), 'y': int(pos.y), 'z': int(pos.z)}
    data.append(p)
    if do_print:
      print("{}[{}]: {}".format(p['name'], p['id'], pos))
  return data


def do_show(args, mc):
  """Show the locations of the players"""
  import curses

  class Coord(object):
    def __init__(self, xmin, xmax, ymin, ymax, screen_xsize, screen_ysize, radius=10):
      self.radius =  radius
      self.xmin = xmin - radius
      self.xmax = xmax + radius
      self.ymin = ymin - radius
      self.ymax = ymax + radius
      self.screen_xsize = screen_xsize
      self.screen_ysize = screen_ysize
    def updateScreenSize( self, rows, cols ):
      if rows!=self.screen_xsize: self.screen_xsize = rows
      if cols!=self.screen_ysize: self.screen_ysize = cols
    def getXRange( self ):
      return (self.xmin, self.xmax)
    def getYRange( self ):
      return (self.ymin, self.ymax)
    def getScreenCoord( self, xpos, ypos ):
      if xpos < self.xmin: self.xmin = xpos - self.radius
      if xpos > self.xmax: self.xmax = xpos + self.radius
      if ypos < self.ymin: self.ymin = ypos - self.radius
      if ypos > self.ymax: self.ymax = ypos + self.radius
      xspan = self.xmax - self.xmin
      yspan = self.ymax - self.ymin
      xrelpos = (xpos - self.xmin) / xspan
      yrelpos = (ypos - self.ymin) / yspan
      # print(f"xrange: ({self.xmin}:{self.xmax}), yrange: ({self.ymin}:{self.ymax}), position: {xpos}, {ypos} -> {xrelpos}, {yrelpos}")
      return (min(max(1, int(self.screen_xsize*xrelpos)), self.screen_xsize-2),
              min(max(1, int(self.screen_ysize*yrelpos)), self.screen_ysize-2))

  if args.do_screen:
    s = curses.initscr()
    s.nodelay(1) # otherwise you don't see the updates
    curses.noecho()
    curses.cbreak()
    s.keypad(1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_WHITE)

  loc = Coord(0, 0, 0, 0, 50, 50)

  while True:
    elist = do_where(args, mc, False)
    tsize = os.get_terminal_size()
    rows, cols = s.getmaxyx() if args.do_screen else (tsize.lines, tsize.columns)
    loc.updateScreenSize(rows, cols)

    if args.do_screen:
      s.clear()
      s.border(0)
      s.addstr(0, 3, "Player Coordinates", curses.A_BOLD|curses.color_pair(1))
      s.addstr(0, 22, "[x:{} y:{}]".format(loc.getXRange(), loc.getYRange()),
               curses.color_pair(1))

    for e in elist:
      sx, sy = loc.getScreenCoord( e['x'], e['z'] )
      if args.do_screen:
        s.addstr(sx, sy, 'x', curses.color_pair(3))
        s.addstr(sx, sy+2, "{} ({},{},{})".format(e['name'], e['x'], e['y'], e['z']),
                 curses.A_NORMAL)
      else:
        print("{} ({},{},{}) scr({},{}) scrpos({},{})".format(
          e['name'], e['x'], e['y'], e['z'], rows, cols, sx, sy))
     
    time.sleep(0.1) 
    if args.do_screen:
      s.refresh()
      ch = s.getch()
      if ch == ord('q'):
        break

  if args.do_screen:
    s.keypad(0)
    s.clear()
    curses.echo()
    curses.nocbreak()
    curses.endwin()


def do_rainbow(args, mc):
  playerpos = mc.player.getTilePos()
  playerdir = mc.player.getDirection()
  dsign = -1 if playerdir.z < 0  else 1
  print("player currently in {}".format(playerpos))
  w = args.width + int(playerpos.x)
  h = args.height + int(playerpos.y)
  d = 20 + int(dsign*playerpos.z) # some offset from where the player is
  colors = [14, 1, 4, 5, 3, 11, 10]
  height = args.height
  # wipe clean the area: block.id == 0 is air (erase) 
  mc.setBlocks(-w,0,d, w,h+len(colors),d, 0)
  if args.erase:
    return
  # draw the rainbow
  for xidx in range(0, w*2):
    for colourindex in range(0, len(colors)):
      y = math.sin((xidx / (w*2)) * math.pi) * height + colourindex
      x = xidx - w
      z = d
      cl = colors[len(colors)-1-colourindex] 
      mc.setBlock(x, y, z, block.WOOL.id, cl)


def do_clear(args, mc):
  mc.postToChat("hit (right click) with sword to clear cube around you")
  count = 0
  while count < args.repeat:
    hits = mc.events.pollBlockHits()
    if len(hits)>0:
      print("got block hit!")
      pos = hits[0].pos
      x0 = pos.x - int(0.5*args.width)
      y0 = pos.y - int(0.5*args.height)
      z0 = pos.z - int(0.5*args.depth)
      x1 = pos.x + int(0.5*args.width)
      y1 = pos.y + int(0.5*args.height)
      z1 = pos.z + int(0.5*args.depth)
      print("player currently in {}".format(pos))
      print("clearing cube ({}) ({})".format((x0,y0,z0),(x1,y1,z1)))
      mc.setBlocks(x0, y0, z0, x1, y1, z1, 0)
      count += 1


def do_trace(args, mc):
  start = time.time() 
  end = start + args.duration
  blkid = args.blockid
  poslist = [mc.player.getTilePos()]
  while time.time() < end:
    pos = mc.player.getTilePos()
    if poslist[-1] != pos:
      poslist.append(pos)
      print("setting block near {}, len(poslist)={}".format(pos, len(poslist)))
      mc.setBlock(pos.x, pos.y, pos.z-1, blkid)
    if len(poslist) > args.size:
      # clear old blocks
      old = poslist.pop(0)
      mc.setBlock( old.x, old.y, old.z-1, 0 )
    time.sleep(0.2)


def do_pixel(args, mc):
  """Convert gif image to pixel art"""
  from PIL import Image
  import requests
  from io import BytesIO

  def _getBlockFromColor(RGB):
    smallestDistIndex = -1
    smallestDist = 300000
    curIndex = 0
    for block in possibleBlocks:
      for blockRGB in block[2]:
        curDist = math.sqrt( pow(RGB[0]-blockRGB[0],2) \
                      + pow(RGB[1]-blockRGB[1],2) \
                      + pow(RGB[2]-blockRGB[2],2))
        if (curDist < smallestDist):
          smallestDist = curDist
          smallestDistIndex = curIndex
      curIndex = curIndex + 1
    if (smallestDistIndex == -1):
      return -1
    return possibleBlocks[smallestDistIndex]
  
  # Possible blocks  in (Name, ID, (RGB1,RGB2,..),Data)
  # RGBs are used to color match.
  possibleBlocks = (
      ("Air", 0, ( (0, 136, 255) ,),0),
      ("Smooth Stone", 1, ( (125,125, 125) ,),0),
      ("Dirt", 3, ( (133,96,66),),0),
      ("Cobblestone", 4, ( (117,117,117),),0),
      ("Wooden Plank", 5, ( (156,127,78),),0),
      ("Bedrock", 7, ( (83,83,83),),0),
      ("Sand", 12, ( (217,210,158),),0),
      ("Gravel", 13, ( (136, 126, 125),),0),
      ("Gold Ore", 14, ( (143,139,124),),0),
      ("Iron Ore", 15, ( (135,130,126),),0),
      ("Coal Ore", 16, ( (115,115,115),),0),
      ("Wood", 17, ( (154,125,77),),0),
      ("Sponge", 19, ( (182,182,57),),0),
      ("White Wool", 35, ( (221,221,221),),0),
      ("Orange Wool", 35, ( (233,126,55),),1),
      ("Magenta Wool", 35, ( (179,75,200),),2),
      ("Light Blue Wool", 35, ( (103,137,211),),3),
      ("Yellow Wool", 35, ( (192,179,28),),4),
      ("Light Green Wool", 35, ( (59,187,47),),5),
      ("Pink Wool", 35, ( (217,132,153),),6),
      ("Dark Gray Wool", 35, ( (66,67,67),),7),
      ("Gray Wool", 35, ( (157,164,165),),8),
      ("Cyan Wool", 35, ( (39,116,148),),9),
      ("Purple Wool", 35, ( (128,53,195),),10),
      ("Blue Wool", 35, ( (39,51,153),),11),
      ("Brown Wool", 35, ( (85,51,27),),12),
      ("Dark Green Wool", 35, ( (55,76,24),),13),
      ("Red Wool", 35, ( (162,44,42),),14),
      ("Black Wool", 35, ( (26,23,23),),15),
      ("Gold", 41, ( (249,236,77),),0),
      ("Iron", 42, ( (230,230,230),),0),
      ("TwoHalves", 43, ( (159,159,159),),0),
      ("Brick", 45, ( (155,110,97),),0),
      ("Mossy Cobblestone", 48, ( (90,108,90),),0),
      ("Obsidian", 49, ( (20,18,29),),0),
      ("Diamond Ore", 56, ( (129,140,143),),0),
      ("Diamond Block", 57, ( (99,219,213),),0),
      ("Workbench", 58, ( (107,71,42),),0),
      ("Redstone Ore", 73, ( (132,107,107),),0),
      ("Snow Block", 80, ( (239,251,251),),0),
      ("Clay", 82, ( (158,164,176),),0),
      ("Jukebox", 84, ( (107,73,55),),0),
      ("Pumpkin", 86, ( (192,118,21),),0),
      ("Netherrack", 87, ( (110,53,51),),0),
      ("Soul Sand", 88, ( (84,64,51),),0),
      ("Glowstone", 89, ( (137,112,64),),0)
  )
  # load the image
  im = None
  if args.file.startswith("http"):
    response = requests.get(args.file)
    print("retrieved response {}".format(response))
    im = Image.open(BytesIO(response.content))
  elif os.path.exist(args.file):
    im = Image.open(args.file)
  else:
    raise ValueError("supply valid file or http url")
  # crop to thumbnail size
  maxsize = (100, 100)
  im.thumbnail(maxsize, Image.ANTIALIAS)
  rgb_im = im.convert('RGB')
  rows, columns = rgb_im.size
  pos = mc.player.getPos()
  for r in range(rows):
      for c in range(columns):
          rgb = rgb_im.getpixel((r, c))
          mc_block = _getBlockFromColor(rgb)
          mc.setBlock(pos.x+r, pos.y, pos.z+c, mc_block[1])


def do_cube(args, mc):
  #test shape
  sz = args.size
  pos = mc.player.getTilePos()
  pos.y += 2*sz
  pos.z += 2*sz
  print("player pos: {}".format(pos))
  myShape = mcstuff.MinecraftShape(mc, pos, visible=True)
  r = int(0.5*sz)
  try:
      print("draw shape")
      myShape.setBlocks(-r, -r, -r, r, r, r, block.GLASS.id, 5)
      print("draw shape done")
      time.sleep(1)
      roll = 0
      pitch = 0
      yaw = 0
      # angles = [15,30,45,60,75,90]
      angles = range(1, 91, 1)
      # angles = [45, 90]
      for roll in angles:
          myShape.rotate(yaw, pitch, roll)
          print("roll angle {} done".format(roll))
          time.sleep(0.05)
      # for count in range(0,5):
      #     myShape.moveBy(1,0,0)
      #     time.sleep(0.5)
  
      time.sleep(2)
  finally:
      myShape.clear()


def main():
  parser = argparse.ArgumentParser(description='Generate structures in minecraft')
  parser.add_argument("--host", type=str, default='homecompute1.lan', help='host')
  parser.add_argument("--port", type=int, default=4711, help='4711 (dev), 4712 (prod)')
  parser.add_argument("--debug", action='store_true')
  parser.add_argument("--entity", type=int, default=None, help='entity id')
  subparsers = parser.add_subparsers(help='sub-command help')

  par_where = subparsers.add_parser('where', help='print where players are')
  par_where.set_defaults(func=do_where) 

  par_rainbow = subparsers.add_parser('rainbow', help='create a rainbow')
  par_rainbow.add_argument('--height', type=int, default=60)
  par_rainbow.add_argument('--width', type=int, default=64)
  par_rainbow.add_argument('--erase', action='store_true')
  par_rainbow.set_defaults(func=do_rainbow) 

  par_clear = subparsers.add_parser('clear', help='blank out block of area')
  par_clear.add_argument('--height', type=int, default=5)
  par_clear.add_argument('--width', type=int, default=5)
  par_clear.add_argument('--depth', type=int, default=5)
  par_clear.add_argument('--repeat', type=int, default=1)
  par_clear.set_defaults(func=do_clear) 

  par_trace = subparsers.add_parser('trace', help='create trailing blocks on player')
  par_trace.add_argument('--duration', type=int, default=30)
  par_trace.add_argument('--blockid', type=int, default=2)  # Block(2) GLASS
  par_trace.add_argument('--size', type=int, default=4)  # Block(2) GLASS
  par_trace.set_defaults(func=do_trace) 

  par_pixel = subparsers.add_parser('pixel', help='reproduce minecraft pixel image')
  par_pixel.add_argument('--file', type=str, required=True)
  par_pixel.set_defaults(func=do_pixel) 

  par_cube = subparsers.add_parser('cube', help='create rotating cube')
  par_cube.add_argument('--size', type=int, required=False, default=5)
  par_cube.set_defaults(func=do_cube) 

  par_show = subparsers.add_parser('show', help='display where players are')
  par_show.add_argument('--do-screen', action='store_true')
  par_show.set_defaults(func=do_show) 

  args = parser.parse_args()

  conn = minecraft.Connection(args.host, args.port)
  mc = minecraft.Minecraft(conn)

  if args.debug: import ipdb; ipdb.set_trace()

  args.func(args, mc)


if __name__ == '__main__':
  main()
