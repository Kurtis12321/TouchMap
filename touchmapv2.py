#!/usr/bin/env python3

import pygame, touchgui, touchguipalate, touchguiconf, math, os
from pygame.locals import *
from array2d import array2d

# display_width, display_height = 1920, 1080
display_width, display_height = 1000, 800
# display_width, display_height = 1920, 1080
full_screen = False
# full_screen = True
toggle_delay = 250
cell_size = 50
btn_size = 50
cell_array = array2d(0, 0, " ")  # the contents will be written to the file and is the complete 2D map
button_array = array2d(0, 0, [None])  # contains just the 2D array of cells (buttons) visible on the tablet
xoffset = 0
yoffset = 0
xborder = 50  # pixels from the edge
yborder = 50  # pixels from the edge
black = (0, 0, 0)
dark_grey = (37, 56, 60)
light_grey = (182, 182, 180)
mid_grey = (132, 132, 130)
white = (255, 255, 255)
rooms_available = []  # any room number which was deleted is placed here
next_room = 1  # the next available room number to be used.
max_rooms = 9
num_rooms = 0
blank_t, wall_t, door_t, spawn_t, hell_t, light_t, tick_t, room_t, delete_t, floor_t = list(
    range(10))  # enumerated types
pointer_name = "cross"  # the image name used to mark cursor position on the map
wall_image_name = "wall"
door_image_name = "door"
hellknight_image_name = "hellknight"
tick_image_name = "tick"
spawn_image_name = "spawn"

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
        self._tile.set_images(blank_list(" ", cell_size))

    def to_wall(self):  # changes tile to a wall
        self._tile.set_images(private_map("wall", cell_size))

    def to_door(self):  # changes tile to door
        self._tile.set_images(private_map(door_image_name, cell_size))

    def to_hellknight(self):  # changes tile to hellknight
        self._tile.set_images(private_map(hellknight_image_name, cell_size))

    def to_tick(self):  # changes tile to tick
        self._tile.set_images(private_map(tick_image_name, cell_size))

    def to_light(self):  # changes tile to light
        self._tile.set_images(private_map("torch", cell_size))

    def to_spawn(self):  # changes tile to spawn
        self._tile.set_images(private_map(spawn_image_name, cell_size))

    def to_room(self, room):  # places room number to empty tile
        self._tile = touchgui.text_tile(black, light_grey, white, mid_grey,
                                        room, self._size,
                                        self._x, self._y,
                                        self._size, self._size, delroom, "room")

    def room_to_blank(self):  # changes room tile to blank tile
        self._tile = touchgui.image_tile(blank_list(" ", self._size),
                                         self._x, self._y,
                                         self._size, self._size, cellback)

    def get_tile(self):  # returns tile
        return self._tile


# this function will get the following room number
def get_next_room():
    global rooms_available, next_room
    if not rooms_available:
        if next_room > max_rooms:
            # there are no more rooms available
            return None
        else:
            room = str(next_room)
        next_room += 1
    else:
        room = rooms_available[0]
        if len(rooms_available) > 1:
            rooms_available = rooms_available[1:]
        else:
            rooms_available = []
    return room


# deletes room
def delroom(param, tap):
    global clicked, cell_array, button_array, double_tapped_cell, rooms_available, num_rooms, next_tile
    clicked = True
    mouse = pygame.mouse.get_pos()
    x, y = get_cell(mouse)
    button = button_array.get(x + xoffset, y + yoffset)
    button.room_to_blank()
    num_rooms = num_rooms - 1
    rooms_available += [cell_array.get(x + xoffset, y + yoffset)]
    cell_array.set_contents(x + xoffset, y + yoffset, " ")
    if next_tile != delete_t:
        cellback(param, tap)


# function that will write the assets found on the map to the txt file
def write_asset(f, a):
    s = "define %s %s\n" % (a, asset_desc[a])
    f.write(s)
    return f


def write_assets(f):
    for a in asset_list:
        f = write_asset(f, a)
    return f


# checks for user input
def event_test(event):
    if (event.type == KEYDOWN) and (event.key == K_ESCAPE):
        myquit(None)


# adds asset to the asset list
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


# saves map to a txt file
def save_map(name):
    f = open(name, "w")
    f = write_assets(f)
    f.write("\n")
    f = write_map(f)
    f.close()

    os.chdir(os.path.join(os.getenv("HOME"), "Sandpit/chisel/python"))
    r = os.system("./developer-txt2map " + "../maps/tiny.txt")

    os.chdir(os.path.join(os.getenv("HOME"), "Sandpit/TouchMap"))
    if r == 0:
        print("Everything is fine, running Doom3")
        os.system("./rundoom.sh")


# loads in the txt file
def load_map(name):
    global cell_array, button_array, asset_list, asset_count, asset_desc, next_room, num_rooms, rooms_available
    # clear the map
    cell_array = array2d(0, 0, " ")
    button_array = array2d(0, 0, [None])
    asset_list = []
    asset_desc = {}
    asset_count = {}
    next_room = 1
    num_rooms = 0
    rooms_available = []
    pygame.display.update()
    # load map from file
    f = open(name, "r")
    f = read_map(f)
    f.close()
    return f


# Loads map (txt file)
def myimport(name, tap):
    global clicked
    pygame.display.update()
    load_map(current_map_name)
    clicked = True
    pygame.display.update()


# creates the txt file that will be converted  to a pen map by using the dictionary to define
# what will the map be converted to
def write_map(f):
    left, right = determine_range()
    m = ""
    x, y = cell_array.high()
    for j in range(y):
        for i in range(left, right + 1):
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
            # Check if asset has any metadata (e.g, "monster monster_hellknight")
            if len(words) >= 4:
                include_asset(words[1], words[2] + " " + words[3])
            else:
                include_asset(words[1], words[2])


# reads in the floor
def read_floor(lines):
    seen_start = False
    y = 0
    ypos = 0
    for line in lines:
        # find the start of the map
        if line.find("#") >= 0 and line.find("define") < 0:
            seen_start = True
        if seen_start:
            add_xaxis(line, y, ypos)
            y += 1
            ypos += cell_size


def add_xaxis(line, y, ypos):
    global cell_array, button_array, next_room
    xpos = 0
    x = 0
    highest_num = 0
    for ch in line:
        b = button(xpos + xborder, ypos + yborder, cell_size)

        tile_chars = ["#", ".", " ", "S", "H"]
        bdict = {
            "#": b.to_wall,
            ".": b.to_door,
            " ": b.to_blank,
            "S": b.to_spawn,
            "H": b.to_hellknight,
            "T": b.to_tick,
            "L": b.to_light,

        }

        # Character is an asset
        if ch in tile_chars:
            cell_array.set_contents(x + xoffset, y + yoffset, ch)
            bdict[ch]()

        # Character is most likely a room
        else:
            ch = ch.strip().rstrip()
            if ch:
                b.to_room(ch)
                cell_array.set_contents(x + xoffset, y + yoffset, ch)
                next_room += 1

        button_array.set_contents(x + xoffset, y + yoffset, [b])
        xpos += cell_size
        x += 1


def read_map(f):
    lines = f.readlines()

    # Read assets
    read_assets(lines)
    # Read floor
    read_floor(lines)

    return f


# display the map on the command line
def myreturn(name, tap):
    pygame.display.update()
    x, y = cell_array.high()
    print("the map")
    m = ""
    for j in range(y):
        for i in range(x):
            ch = cell_array.get(i, j)
            m += ch
        m += "\n"
    print(m)
    save_map(current_map_name)


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
    pygame.display.update()


def recreate_button_grid():
    global button_array
    button_array = array2d(0, 0, [None])


# the function returns the converted image
def button_list(name, size):
    return [touchgui.image_gui(libimagedir("images/PNG/White/2x/%s.png") % name).white2grey(.5).resize(size, size),
            touchgui.image_gui(libimagedir("images/PNG/White/2x/%s.png") % (name)).white2grey(.1).resize(size, size),
            touchgui.image_gui(libimagedir("images/PNG/White/2x/%s.png") % (name)).resize(size, size),
            touchgui.image_gui(libimagedir("images/PNG/White/2x/%s.png") % (name)).white2rgb(.1, .2, .4).resize(size,
                                                                                                                size)]


# the function returns the converted image scaled for map
def private_map(name, size):
    return [touchgui.image_gui("%s.png" % (name)).grey().resize(size, size),
            touchgui.image_gui("%s.png" % (name)).grey().resize(size, size),
            touchgui.image_gui("%s.png" % (name)).resize(size, size),
            touchgui.image_gui("%s.png" % (name)).resize(size, size)]


# the function returns the converted image
def blank_list(name, size):
    return [touchgui.color_tile(touchguipalate.white, size, size),
            touchgui.color_tile(touchguipalate.white, size, size),
            touchgui.color_tile(touchguipalate.white, size, size),
            touchgui.color_tile(touchguipalate.white, size, size)]


# return a list of buttons for the user interface
def buttons():
    return [touchgui.image_tile(button_list("power", btn_size),
                                touchgui.posX(0.95), touchgui.posY(1.0),
                                btn_size, btn_size, myquit),
            touchgui.image_tile(button_list("export", btn_size),
                                touchgui.posX(0.0), touchgui.posY(1.0),
                                btn_size, btn_size, myreturn),
            touchgui.image_tile(button_list("import", btn_size),
                                touchgui.posX(0.1), touchgui.posY(1.0),
                                btn_size, btn_size, myimport),
            touchgui.image_tile(button_list("smaller", btn_size),
                                touchgui.posX(0.0), touchgui.posY(0.065),
                                btn_size, btn_size, myzoom, True),
            touchgui.image_tile(button_list("larger", btn_size),
                                touchgui.posX(0.95), touchgui.posY(0.065),
                                btn_size, btn_size, myzoom, False)]


# returns a list of assets that will be displayed in a 2d array
def assets():
    return [
        touchgui.image_tile(private_map(wall_image_name, btn_size),
                            touchgui.posX(0.95), touchgui.posY(0.935),
                            btn_size, btn_size, wallv),
        touchgui.image_tile(private_map(door_image_name, btn_size),
                            touchgui.posX(0.9), touchgui.posY(0.935),
                            btn_size, btn_size, door),
        touchgui.image_tile(private_map(spawn_image_name, btn_size),
                            touchgui.posX(0.9), touchgui.posY(0.870),
                            btn_size, btn_size, spawn),

        touchgui.image_tile(private_map(hellknight_image_name, btn_size),
                            touchgui.posX(0.9), touchgui.posY(0.805),
                            btn_size, btn_size, hellknight),
        touchgui.image_tile(private_map(tick_image_name, btn_size),
                            touchgui.posX(0.9), touchgui.posY(0.740),
                            btn_size, btn_size, tick),
        touchgui.image_tile(private_map("torch", btn_size),
                            touchgui.posX(0.95), touchgui.posY(0.805),
                            btn_size, btn_size, light),
        touchgui.image_tile(button_list("trashcanOpen", btn_size),
                            touchgui.posX(0.95), touchgui.posY(0.130),
                            btn_size, btn_size, trash)]


def glyphs():
    return [touchgui.text_tile(black, mid_grey, white, light_grey,
                               'room', touchgui.unitY(0.03),
                               touchgui.posX(0.475), touchgui.posY(1.0),
                               50, 50, myroom, "room")]


#
# callback functions
#

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


# places hellknight
def hellknight(name, tap):
    global next_tile
    pygame.display.update()
    if tap == 1:
        print("hellknight created", name, tap)
        next_tile = hell_t


def tick(name, tap):
    global next_tile
    pygame.display.update()
    if tap == 1:
        print("tick created", name, tap)
        next_tile = tick_t


# places light
def light(name, tap):
    global next_tile
    pygame.display.update()
    if tap == 1:
        print("light created", name, tap)
        next_tile = light_t


# places spawn point
def spawn(name, tap):
    global next_tile
    pygame.display.update()
    if tap == 1:
        print("spawn created", name, tap)
        next_tile = spawn_t


# places wall
def wallv(name, tap):
    global next_tile
    pygame.display.update()
    if tap == 1:
        print("wall created", name, tap)
        next_tile = wall_t


# places room number
def myroom(name, tap):
    global next_tile
    pygame.display.update()
    if tap == 1:
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


double_tapped_cell = None


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
        cell_array.set_contents(x + xoffset, y + yoffset, "#")
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
    # include_asset ('#', "wall for level")
    cell_array.set_contents(x + xoffset, y + yoffset, "#")
    if tap == 2:
        start_coordinate = [x, y]
    elif start_coordinate != None:
        fillWall(x, y)
        start_coordinate = None


# creates a door
def create_door(button, x, y, tap):
    global next_tile, cell_array
    button.to_door()
    # include_asset ('.', "Door for passage")
    cell_array.set_contents(x + xoffset, y + yoffset, ".")
    next_tile = door_t


# creates a hellknight
def create_hellknight(button, x, y, tap):
    global next_tile, cell_array
    button.to_hellknight()
    include_asset('H', "monster monster_demon_hellknight")
    cell_array.set_contents(x + xoffset, y + yoffset, "H")
    next_tile = hell_t


# creates a tick
def create_tick(button, x, y, tap):
    global next_tile, cell_array
    button.to_tick()
    include_asset('T', "monster monster_demon_tick")
    cell_array.set_contents(x + xoffset, y + yoffset, "T")
    next_tile = tick_t


# creates a light
def create_light(button, x, y, tap):
    global next_tile, cell_array
    button.to_light()
    include_asset('L', "light")
    cell_array.set_contents(x + xoffset, y + yoffset, "L")
    next_tile = light_t


# creates a spawn
def create_spawn(button, x, y, tap):
    global next_tile, cell_array
    button.to_spawn()
    include_asset('S', "worldspawn ")
    cell_array.set_contents(x + xoffset, y + yoffset, "S")
    next_tile = spawn_t


# creates a room number
def create_room(button, x, y, tap):
    global next_tile, cell_array, num_rooms, max_rooms
    if num_rooms >= max_rooms:
        return
    num_rooms = num_rooms + 1
    room = get_next_room()
    if room is None:
        return
    button.to_room(room)
    include_asset(room, "room " + room)
    cell_array.set_contents(x + xoffset, y + yoffset, room)
    next_tile = room_t


# deletes button
def delete_button(button, x, y, tap):
    global next_tile, cell_array
    print("Delete called")
    ch = cell_array.get(x, y)
    button.to_blank()
    exclude_asset(ch)
    cell_array.set_contents(x + xoffset, y + yoffset, " ")


# dictionary that uses the keywords to access create functions
function_create = {blank_t: create_blank,
                   wall_t: create_wall,
                   door_t: create_door,
                   hell_t: create_hellknight,
                   tick_t: create_tick,
                   light_t: create_light,
                   delete_t: delete_button,
                   room_t: create_room,
                   spawn_t: create_spawn}


# main function to place tiles to the map
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
                    cell_array.set_contents(x, j, "#")
        elif last_pos[1] == y:
            for i in range(min(x, last_pos[0]), max(x, last_pos[0]) + 1):
                old = cell_array.get(i, y)
                button = button_array.get(i, y)
                if old == " ":
                    button.to_wall()
                    cell_array.set_contents(i, y, "#")


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
        if content == "#":
            b.to_wall()
        elif content == ".":
            b.to_door()
        elif content == "H":
            b.to_hellknight()
        elif content == "T":
            b.to_tick()
        elif content == "L":
            b.to_light()
        elif content == "S":
            b.to_spawn()
        elif content != " ":
            b.to_room(content)

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
    for i, x in enumerate(range(xborder, (display_width - xborder * 2) - (size - 1), size)):
        for j, y in enumerate(range(yborder, (display_height - yborder) - (size - 1), size)):
            # print (i,j,x,y)
            c = get_button(i, j, x, y, size)
            assert (c != None)
            b += [c.get_tile()]
    return b


# Main function that runs the program
def main():
    global players, grid, cell_size

    pygame.init()
    if full_screen:
        gameDisplay = pygame.display.set_mode((display_width, display_height), FULLSCREEN)
    else:
        gameDisplay = pygame.display.set_mode((display_width, display_height))

    touchgui.set_display(gameDisplay, display_width, display_height)
    controls = buttons() + glyphs() + assets()

    gameDisplay.fill(touchguipalate.black)
    while True:
        gameDisplay.fill(touchguipalate.black)
        grid = button_grid(cell_size)
        forms = grid + controls
        touchgui.select(forms, event_test, finished)
        print("while")


main()
