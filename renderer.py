import sdl2.ext

class Palette():
    def __init__(self):
        self.colors = [(0x7C,0x7C,0x7C),(00,00,0xFC),(00,00,0xBC),(44,28,0xBC),(94,00,84),(0xA8,00,20),(0xA8,10,00),(88,14,00),(50,30,00),(00,78,00),(00,68,00),(00,58,00),(00,40,58),(00,00,00),(00,00,00),(00,00,00),(0xBC,0xBC,0xBC),(00,78,0xF8),(00,58,0xF8),(68,44,0xFC),(0xD8,00,0xCC),(0xE4,00,58),(0xF8,38,00),(0xE4,0x5C,10),(0xAC,0x7C,00),(00,0xB8,00),(00,0xA8,00),(00,0xA8,44),(00,88,88),(00,00,00),(00,00,00),(00,00,00),(0xF8,0xF8,0xF8),(0x3C,0xBC,0xFC),(68,88,0xFC),(98,78,0xF8),(0xF8,78,0xF8),(0xF8,58,98),(0xF8,78,58),(0xFC,0xA0,44),(0xF8,0xB8,00),(0xB8,0xF8,18),(58,0xD8,54),(58,0xF8,98),(00,0xE8,0xD8),(78,78,78),(00,00,00),(00,00,00),(0xFC,0xFC,0xFC),(0xA4,0xE4,0xFC),(0xB8,0xB8,0xF8),(0xD8,0xB8,0xF8),(0xF8,0xB8,0xF8),(0xF8,0xA4,0xC0),(0xF0,0xD0,0xB0),(0xFC,0xE0,0xA8),(0xF8,0xD8,78),(0xD8,0xF8,78),(0xB8,0xF8,0xB8),(0xB8,0xF8,0xD8),(00,0xFC,0xFC),(0xF8,0xD8,0xF8),(00,00,00),(00,00,00)]


    def GetColor(self, colorNum):
        return self.colors[colorNum]

class Renderer():
    def __init__(self, scale=3):
        self.palette = Palette()
        sdl2.ext.init()
        self.scale = scale
        self.window = sdl2.ext.Window("RefNES", size = (256*scale,240*scale))
        self.world = sdl2.ext.World()
        self.spriteRenderer = sdl2.ext.SoftwareSpriteRenderSystem(self.window)
        self.world.add_system(self.spriteRenderer)
        self.factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
        self.window.show()


    # draw a pixelly thing
    def Update(self, screen, x, y):
        screenIndex = (y * 256) + x
        rgb = self.palette.GetColor(screen[screenIndex])
        color = sdl2.ext.Color(rgb[0], rgb[1], rgb[2])
       
        pixel = self.factory.from_color(color, size=(self.scale, self.scale))
        pixel.position = (x*self.scale, y*self.scale)
        self.world.process()
        self.window.refresh()
