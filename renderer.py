import sdl2.ext

class Renderer():
    def __init__(self):
        sdl2.ext.init()

        self.window = sdl2.ext.Window("RefNES", size = (256,240))

            
