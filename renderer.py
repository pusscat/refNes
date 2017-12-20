import sdl2.ext

class Palette():
    def __init__(self, palettePath):
        # load a palette from a modern VGA palette file here
        self.colors = [0] * 0x40
        pass

    def GetColor(self, colorNum):
        return self.colors[colorNum]

class Renderer():
    def __init__(self):
        self.palette = Palette("./nesPal.pal")
        sdl2.ext.init()

        self.window = sdl2.ext.Window("RefNES", size = (256,240))

    # draw a pixelly thing
    def Update(self, screen, x, y):
        screenIndex = (y * 256) + x
        color = self.palette.GetColor(screen[screenIndex])
        
