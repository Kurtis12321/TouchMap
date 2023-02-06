#!/usr/bin/env python3

import pygame, touchgui, touchguipalate, touchguiconf, math, os
from pygame.locals import *
from array2d import array2d

# display_width, display_height = 1920, 1080
display_width, display_height = 800, 600
# display_width, display_height = 1920, 1080
full_screen = False
# full_screen = True
toggle_delay = 250
cell_size = 100
btn_size = 40
cell_array = array2d(0, 0, " ")  # the contents will be written to the file and is the complete 2D map
button_array = array2d(0, 0, [None])  # contains just the 2D array of cells (buttons) visible on the tablet
xoffset = 0
yoffset = 0
xborder = 100  # pixels from the edge
yborder = 100  # pixels from the edge
black = (0, 0, 0)
dark_grey = (37, 56, 60)
light_grey = (182, 182, 180)
mid_grey = (132, 132, 130)
white = (255, 255, 255)
rooms_available = []  # any room number which was deleted is placed here
next_room = 1  # the next available room number to be used.
blank_t, wall_t, door_t, spawn_t, hell_t, tick_t, room_t, delete_t, floor_t = list(range(9))  # enumerated types
pointer_name = "cross"  # the image name used to mark cursor position on the map
wall_image_name = "wall"
door_image_name = "door"

minDoorLength = 3


next_tile = wall_t
current_map_name = "tiny.txt"
last_pos = []  # the last saved position
start_coordinate = None

asset_list = []  # list of assets
asset_desc = {}  # dictionary of asset descriptions
asset_count = {}  # how many of each asset are we using?


# initializing the button class that will be the Interface
class button:
    def __init__(self, x, y, size):
        self._x = x
        self._y = y
        self._size = size
        self._tile = touchgui.image_tile(blank_list("wall", size),
                                         x, y,
                                         size, size, cellback)

    def to_blank(self):  # changes tile to blank
        self._tile.set_images(blank_list("wall", cell_size))

    def to_wall(self):  # changes tile to a wall
        self._tile.set_images(wall_list("v", cell_size))

    def to_door(self):  # changes tile to door
        self._tile.set_images(private_map(door_image_name, cell_size))

    def to_hellknight(self):  # changes tile to hellknight
        self._tile.set_images(private_map("hellknight", cell_size))

    def to_tick(self):  # changes tile to tick
        self._tile.set_images(private_map("tick", cell_size))

    def to_spawn(self): # changes tile to spawn
        self._tile.set_images(private_map("spawn", cell_size))

    def to_room(self): # changes tile to next_room
        self._tile.set_text(str(next_room))

    def get_tile(self):  # returns tile
        return self._tile


# functin that will write the assets found on the map to the txt file
def write_asset(f, a):
    s = "define %s %s\n" % (a, asset_desc[a])
    f.write(s)
    return f


##check horizonttoly for doors on the map
def checkHowizontal():
    x, y = cell_array.high()
    for j in range(y):
        doorWidth = 0
        seenWall = False
        for i in range(x):
            if cell_array.get(i, j) == ".":
                if seenWall:
                    doorWidth += 1
            elif cell_array.get(i, j) == "#":
                if (doorWidth > 0) and (doorWidth < minDoorLength):
                    return False
                doorWidth = 0
            else:
                seenWall = False
        if doorWidth > 0:
            return False
    return True


# check verticali for doors on the map
def checkVertical():
    x, y = cell_array.high()
    for i in range(x):
        doorWidth = 0
        seenWall = False
        for j in range(y):
            if cell_array.get(i, j) == ".":
                if seenWall:
                    doorWidth += 1
            elif cell_array.get(i, j) == "#":
                if (doorWidth > 0) and (doorWidth < minDoorLength):
                    return False
                doorWidth = 0
            else:
                seenWall = False
    return True


def write_assets(f):
    for a in asset_list:
        f = write_asset(f, a)
    return f


# checks for user input
def event_test(event):
    if (event.type == KEYDOWN) and (event.key == K_ESCAPE):
        myquit(None)
    if event.type == USEREVENT + 1:
        reduceSignal()


# adds asset to the asste list
def include_asset(a, desc):
    global asset_list, asset_desc, asset_count
    if not (a in asset_list):
        asset_list += [a]
    asset_desc[a] = desc
    if a in asset_count:
        asset_count[a] += 1
    else:
        asset_count[a] = 1


# deletes asset for asset list
def exclude_asset(a):
    global asset_list, asset_count
    if a in asset_count:
        asset_count[a] -= 1
        if asset_count[a] == 0:
            del asset_count[a]
            asset_list.remove(a)


# Quits the application
def myquit(name=None, tap=1):
    pygame.display.update()
    pygame.time.delay(toggle_delay * 2)
    pygame.quit()
    quit()


# creates the txt file that will be converted  to a pen map by using the dictionary to define
# what will the map be converted to
def write_map(f):
    left, right = determine_range()
    m = ""
    mdict = {"v": "#", "h": "#", "-": ".", ".": ".", "|": ".", " ": " ",
             "H": "H", "S": "S", "T": "T", "W": "W"}
    x, y = cell_array.high()
    for j in range(y):
        for i in range(left, right + 1):
            if cell_array.get(i, j) in mdict:
                m += mdict[cell_array.get(i, j)]
            else:
                m += cell_array.get(i, j)
        # skip blank lines
        m = m.rstrip()
        if len(m) > 0:
            m += "\n"
    f.write(m)
    return f


# this funtion will limit the number of walls on a map
def determine_range():
    left = -1
    x, y = cell_array.high()
    right = x
    for j in range(y):
        for i in range(x):
            if cell_array.get(i, j) != " ":
                if (left == -1) or (i < left):
                    left = i
                if i > right:
                    right = i
    return left, right


# reads in assets from the map and includes them in a asset list
def read_assets(lines):
    for line in lines:
        words = line.lstrip().split()
        if (len(words) > 2) and (words[0] == "define"):
            include_asset(words[1], words[2])


# reads in the floor
def read_floor(lines):
    screen_start = False
    y = 0
    ypos = 0
    for line in lines:
        if len(line.split('#')) > 0:
            screen_start = True
        if screen_start:
            add_xaxis(line, y, ypos)
            y += 1
            ypos += cell_size


# checks for doors (Horizontal and vertical)and returns false if any function does not pass
def CheckDoors():
    return checkVertical() and checkHowizontal()


# display the map on the command line
def myreturn(name, tap):
    pygame.display.update()
    x, y = cell_array.high()
    print("the map")
    m = ""
    mdict = {"v": "#", "h": "#", "-": ".", "|": ".", " ": " ", "s": "s", "H": "H", "T": "T", "S": "S", "W": "W"}
    for j in range(y):
        for i in range(x):
            ch = cell_array.get(i, j)
            if ch in mdict:
                m += mdict[cell_array.get(i, j)]
            else:
                m += ch
        m += "\n"
    print(m)


def libimagedir(name):
    return os.path.join(touchguiconf.touchguidir, name)


# this function will set the cell_size larger or smaller
def myzoom(is_larger, tap):
    global cell_size, clicked
    clicked = True
    if is_larger:
        cell_size += 10
    else:
        cell_size -= 10
    recreate_button_grid()


def recreate_button_grid():
    global button_array
    button_array = array2d(0, 0, [None])


# the function returns the converted image
def button_list(name):
    return [touchgui.image_gui(libimagedir("images/PNG/White/2x/%s.png") % (name)).white2grey(.5),
            touchgui.image_gui(libimagedir("images/PNG/White/2x/%s.png") % (name)).white2grey(.1),
            touchgui.image_gui(libimagedir("images/PNG/White/2x/%s.png") % (name)),
            touchgui.image_gui(libimagedir("images/PNG/White/2x/%s.png") % (name)).white2rgb(.1, .2, .4)]


# the function returns the converted image
def private_list(name):
    return [touchgui.image_gui("%s.png" % (name)).white2grey(.5),
            touchgui.image_gui("%s.png" % (name)).white2grey(.1),
            touchgui.image_gui("%s.png" % (name)),
            touchgui.image_gui("%s.png" % (name)).white2rgb(.1, .2, .4)]


# the function returns the converted image
def image_list(name):
    return [touchgui.image_gui("%s.png" % (name)).grey(),
            touchgui.image_gui("%s.png" % (name)).grey(),
            touchgui.image_gui("%s.png" % (name)),
            touchgui.image_gui("%s.png" % (name))]


# the function returns the converted image
def private_quake(name):
    return [touchgui.image_gui("%s.png" % (name)).grey().resize(50, 50),
            touchgui.image_gui("%s.png" % (name)).grey().resize(50, 50),
            touchgui.image_gui("%s.png" % (name)).resize(50, 50),
            touchgui.image_gui("%s.png" % (name)).resize(50, 50)]


# the function returns the converted image scaled for map
def private_map(name, size):
    return [touchgui.image_gui("%s.png" % (name)).grey().resize(size, size),
            touchgui.image_gui("%s.png" % (name)).grey().resize(size, size),
            touchgui.image_gui("%s.png" % (name)).resize(size, size),
            touchgui.image_gui("%s.png" % (name)).resize(size, size)]


# the function returns the converted image
def blank_list(name, size):
    return [touchgui.color_tile(touchguipalate.black, size, size),
            touchgui.color_tile(touchguipalate.black, size, size),
            touchgui.image_gui("%s.png" % (name)).resize(size, size),
            touchgui.image_gui("%s.png" % (name)).resize(size, size)]


# the function returns the converted image
def wall_list(orientation, size):
    return [touchgui.image_gui("wall.png").grey().resize(size, size),
            touchgui.image_gui("wall.png").grey().resize(size, size),
            touchgui.image_gui("wall.png").resize(size, size),
            touchgui.image_gui("wall.png").resize(size, size)]


# the function returns the converted image
def door_list(orientation, size):
    return [touchgui.image_gui("door.png").grey().resize(size, size),
            touchgui.image_gui("door.png").grey().resize(size, size),
            touchgui.image_gui("door.png").resize(size, size),
            touchgui.image_gui("door.png").resize(size, size)]


# the function returns the converted image
def hellknight_list(orientation, size):
    return [touchgui.image_gui("hellknight.png").grey().resize(size, size),
            touchgui.image_gui("hellknight.png").grey().resize(size, size),
            touchgui.image_gui("hellknight.png").resize(size, size),
            touchgui.image_gui("hellknight.png").resize(size, size)]


# return a list of buttons for the user interface
def buttons():
    return [touchgui.image_tile(button_list("power"),
                                touchgui.posX(0.90), touchgui.posY(1.0),
                                100, 100, myquit),
            touchgui.image_tile(button_list("export"),
                                touchgui.posX(0.0), touchgui.posY(1.0),
                                100, 100, myreturn),

            touchgui.image_tile(button_list("smaller"),
                                touchgui.posX(0.0), touchgui.posY(0.15),
                                100, 100, myzoom, True),
            touchgui.image_tile(button_list("larger"),
                                touchgui.posX(0.90), touchgui.posY(0.15),
                                100, 100, myzoom, False)]


# returns a list of assets that will be displayed in a 2d array
def assets():
    return [
        touchgui.image_tile(private_quake(wall_image_name),
                            touchgui.posX(0.9), touchgui.posY(0.8),
                            40, 40, wallv),
        touchgui.image_tile(private_quake(door_image_name),
                            touchgui.posX(0.9), touchgui.posY(0.7),
                            40, 40, door),
        touchgui.image_tile(private_quake("hellknight"),
                            touchgui.posX(0.9), touchgui.posY(0.6),
                            40, 40, hellknight),
        touchgui.image_tile(private_quake("tick"),
                            touchgui.posX(0.9), touchgui.posY(0.5),
                            40, 40, tick),
        touchgui.image_tile(private_quake("spawn"),
                            touchgui.posX(0.9), touchgui.posY(0.4),
                            40, 40, spawn),
        touchgui.image_tile(button_list("trashcanOpen"),
                            touchgui.posX(0.9), touchgui.posY(0.25),
                            40, 40, trash),
        touchgui.text_tile(touchguipalate.wood_dark, touchguipalate.gold, touchguipalate.wood_light, touchguipalate.wood_light,
                                '\u00F7', touchgui.unitY (0.05),
                                touchgui.posX (0.0), touchgui.posY (1.0),
                                100, 100, newRoom, str(next_room))]


# list of function that will call the (function__create) dictionary and run corresponding function
# deletes tile
def trash(name, tap):
    global next_tile
    next_tile = delete_t


# places door
def door(name, tap):
    global next_tile
    pygame.display.update()
    if tap == 1:
        print("Door created", name, tap)
        next_tile = door_t


# places wall
def wallv(name, tap):
    global next_tile
    pygame.display.update()
    if tap == 1:
        print("wall created", name, tap)
        next_tile = wall_t


# places hellknight
def hellknight(name, tap):
    global next_tile
    pygame.display.update()
    if tap == 1:
        print("hellknight created", name, tap)
        next_tile = hell_t


# places tick
def tick(name, tap):
    global next_tile
    pygame.display.update()
    if tap == 1:
        print("tick created", name, tap)
        next_tile = tick_t


# places spawn
def spawn(name, tap):
    global next_tile
    pygame.display.update()
    if tap == 1:
        print("spawn created", name, tap)
        next_tile = spawn_t

def newRoom(name, tap):
    global next_tile
    pygame.display.update()
    if tap == 1:
        print("new room created", name, tap)
        next_tile = room_t

#
#  save_wall_pos - saves the coordinate [x, y] to last_pos
#

def save_wall_pos(x, y):
    global last_pos
    last_pos = [x, y]


#
#  match_line - return True if [x, y] is the same as the last_pos
#

def match_line(x, y):
    return (last_pos != []) and ((last_pos[0] == x) or (last_pos[1] == y))


def mygrid(name, tap):
    print("grid callback")


def blank(x, y, size):
    b = touchgui.image_tile(blank_list("wallv", size),
                            x, y,
                            size, size, cellback)
    assert (b != None)
    return b


# returns the position of the mouse on the grid
def get_cell(mouse):
    x, y = mouse
    x -= xborder
    y -= yborder
    return int(x / cell_size), int(y / cell_size)


double_tapped_cell = None  # deletes room


def delete_room(button, x, y, tap):
    global next_tile, cell_array
    print("Delete called")
    button.to_blank()
    ch = cell_array.get(x, y)
    exclude_asset(ch)


# create function that correspond to the dictionay(create_function) and places a tile to the given coordinates
def create_blank(button, x, y, tap):
    global next_tile, cell_array
    button.to_blank()
    include_asset(' ', "empty space")
    cell_array.set_contents(x + xoffset, y + yoffset, " ")
    next_tile = blank_t


def change_tile_to_wall(x, y):
    global cell_array, start_coordinate
    ch = cell_array.get(x + xoffset, y + yoffset)
    if ch == " ":
        cell_array.set_contents(x + xoffset, y + yoffset, "v")
        button = button_array.get(x + xoffset, y + yoffset)
        button.to_wall()
    print("changing coordinates", x, y, "into wall")


# this function will use 2 sets of x and y coordinates and creates a line of wall inbetween
def fillWall(x, y):
    if x == start_coordinate[0]:
        y0 = min(y, start_coordinate[1])
        y1 = max(y, start_coordinate[1])
        for j in range(y0, y1 + 1):
            change_tile_to_wall(x, j)
    elif y == start_coordinate[1]:
        x0 = min(x, start_coordinate[0])
        x1 = max(x, start_coordinate[0])
        for i in range(x0, x1 + 1):
            change_tile_to_wall(i, y)


# creates a wall tile and if the tap count goes to 2
# it will be the start point and the second set of coordinates will be the end point for the wall line
def create_wall(button, x, y, tap):
    global next_tile, cell_array, start_coordinate
    button.to_wall()
    include_asset('v', "wall for level")
    cell_array.set_contents(x + xoffset, y + yoffset, "v")
    if tap == 2:
        start_coordinate = [x, y]
    elif start_coordinate != None:
        fillWall(x, y)
        start_coordinate = None


# creates a door
def create_door(button, x, y, tap):
    global next_tile, cell_array
    button.to_door()
    include_asset('|', "Door for passage")
    cell_array.set_contents(x + xoffset, y + yoffset, "|")
    next_tile = door_t


# creates a hellknight
def create_hellknight(button, x, y, tap):
    global next_tile, cell_array
    button.to_hellknight()
    include_asset('H', "Hellknight for level")
    cell_array.set_contents(x + xoffset, y + yoffset, "H")
    next_tile = hell_t


# creates a tick
def create_tick(button, x, y, tap):
    global next_tile, cell_array
    button.to_tick()
    include_asset('T', "Tick for level")
    cell_array.set_contents(x + xoffset, y + yoffset, "T")
    next_tile = tick_t


# creates a spawn
def create_spawn(button, x, y, tap):
    global next_tile, cell_array
    button.to_spawn()
    include_asset('S', "Spawn for level")
    cell_array.set_contents(x + xoffset, y + yoffset, "S")
    next_tile = spawn_t

# creates a new room
def create_newRoom(button, x, y, tap):
    # create a new room by displaying a room number in the tile
    global next_tile, cell_array
    button.to_newRoom()
    include_asset('R', "New Room")
    cell_array.set_contents(x + xoffset, y + yoffset, "R")
    next_tile = room_t

# deletes room
def delete_room(button, x, y, tap):
    global next_tile, cell_array
    print("Delete called")
    button.to_blank()
    ch = cell_array.get(x, y)
    exclude_asset(ch)


# dictionary that uses the keywords to access create functions
function_create = {blank_t: create_blank,
                   wall_t: create_wall,
                   door_t: create_door,
                   hell_t: create_hellknight,
                   tick_t: create_tick,
                   spawn_t: create_spawn,
                   room_t: create_newRoom,
                   delete_t: delete_room}


# main function to plase tiles to the map
def cellback(param, tap):
    global clicked, cell_array, button_array, last_pos
    clicked = True
    mouse = pygame.mouse.get_pos()
    x, y = get_cell(mouse)
    old = cell_array.get(x + xoffset, y + yoffset)
    button = button_array.get(x + xoffset, y + yoffset)
    function_create[next_tile](button, x, y, tap)


#
#  draw_line - draw a line from the last_pos to, [x, y] providing [x, y]
#              lies on the same axis.
#


def draw_line(x, y):
    global cell_array, button_array
    if last_pos != []:
        if last_pos[0] == x:
            for j in range(min(y, last_pos[1]), max(y, last_pos[1]) + 1):
                old = cell_array.get(x, j)
                button = button_array.get(x, j)
                if old == " ":
                    button.to_wall()
                    cell_array.set_contents(x, j, "v")
        elif last_pos[1] == y:
            for i in range(min(x, last_pos[0]), max(x, last_pos[0]) + 1):
                old = cell_array.get(i, y)
                button = button_array.get(i, y)
                if old == " ":
                    button.to_wall()
                    cell_array.set_contents(i, y, "v")


#
#  get_button - returns an existing cell if it exists, or create a new blank button.
#

def get_button(i, j, x, y, size):
    global cell_array, button_array
    if cell_array.inRange(xoffset + i, yoffset + j):
        if button_array.inRange(xoffset + i, yoffset + j):
            b = button_array.get(xoffset + i, yoffset + j)
            if b != None:
                return b
        content = cell_array.get(xoffset + i, yoffset + j)
        b = button(x, y, size)
        if content == "v":
            b.to_wall()
        elif content == "|":
            b.to_door()

        button_array.set_contents(xoffset + i, yoffset + j, [b])
        return b
    b = button(x, y, size)
    b.to_blank()
    cell_array.set_contents(xoffset + i, yoffset + j, " ")
    button_array.set_contents(xoffset + i, yoffset + j, [b])
    return b


# returns a value if the mouse has been clicked or not
def finished():
    return clicked


# creates the grid where all the buttons are displayed
def button_grid(size):
    global clicked

    clicked = False
    b = []
    for i, x in enumerate(range(xborder, display_width - xborder, size)):
        for j, y in enumerate(range(yborder, display_height - yborder, size)):
            c = get_button(i, j, x, y, size)
            assert (c != None)
            b += [c.get_tile()]
    return b


def add_xaxis(line, y, ypos):
    global cell_array, button_array, next_room
    xpos = 0
    x = 0
    highest_num = 0
    for ch in line:
        b = button(xpos + xborder, ypos + yborder, cell_size)

        title_chars = ["#", ".", " ", "S", "H"]
        bdict = {
            "#": b.to_wall,
            ".": b.to_door,
            " ": b.to_blank,
            "S": b.to_spawn,
            "H": b.to_hellknight,
        }

        #Character is an asset
        if ch in title_chars:
            cell_array.set_contents(x + xoffset, y + yoffset, ch)
            bdict[ch]()

        #Character is a room number
        else:
            ch = ch.strip().rstrip()
            if ch:
                b.to_room(ch)
                cell_array.set_contents(x + xoffset, y + yoffset, ch)
                next_room += 1

        button_array.set_contents(x + xoffset, y + yoffset, [b])
        xpos += cell_size
        x += 1


def save_map(name):
    f = open(name, "w")
    f = write_assets(f)
    f.write("\n")
    f = write_map(f)
    f.close()


# Main function that runs the program
def main():
    global players, grid, cell_size

    pygame.init()
    if full_screen:
        gameDisplay = pygame.display.set_mode((display_width, display_height), FULLSCREEN)
    else:
        gameDisplay = pygame.display.set_mode((display_width, display_height))

    touchgui.set_display(gameDisplay, display_width, display_height)
    controls = buttons() + assets()

    gameDisplay.fill(touchguipalate.black)
    while True:
        grid = button_grid(cell_size)
        forms = controls + grid
        touchgui.select(forms, event_test, finished)


main()
