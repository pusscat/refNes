import time

import pygame

class Palette():
    def __init__(self, ppu):
        self.ppu = ppu
        # NES 2C02 palette, indexed by 6-bit color number
        self.colors = [
            (0x7C, 0x7C, 0x7C), (0x00, 0x00, 0xFC), (0x00, 0x00, 0xBC), (0x44, 0x28, 0xBC),
            (0x94, 0x00, 0x84), (0xA8, 0x00, 0x20), (0xA8, 0x10, 0x00), (0x88, 0x14, 0x00),
            (0x50, 0x30, 0x00), (0x00, 0x78, 0x00), (0x00, 0x68, 0x00), (0x00, 0x58, 0x00),
            (0x00, 0x40, 0x58), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
            (0xBC, 0xBC, 0xBC), (0x00, 0x78, 0xF8), (0x00, 0x58, 0xF8), (0x68, 0x44, 0xFC),
            (0xD8, 0x00, 0xCC), (0xE4, 0x00, 0x58), (0xF8, 0x38, 0x00), (0xE4, 0x5C, 0x10),
            (0xAC, 0x7C, 0x00), (0x00, 0xB8, 0x00), (0x00, 0xA8, 0x00), (0x00, 0xA8, 0x44),
            (0x00, 0x88, 0x88), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
            (0xF8, 0xF8, 0xF8), (0x3C, 0xBC, 0xFC), (0x68, 0x88, 0xFC), (0x98, 0x78, 0xF8),
            (0xF8, 0x78, 0xF8), (0xF8, 0x58, 0x98), (0xF8, 0x78, 0x58), (0xFC, 0xA0, 0x44),
            (0xF8, 0xB8, 0x00), (0xB8, 0xF8, 0x18), (0x58, 0xD8, 0x54), (0x58, 0xF8, 0x98),
            (0x00, 0xE8, 0xD8), (0x78, 0x78, 0x78), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
            (0xFC, 0xFC, 0xFC), (0xA4, 0xE4, 0xFC), (0xB8, 0xB8, 0xF8), (0xD8, 0xB8, 0xF8),
            (0xF8, 0xB8, 0xF8), (0xF8, 0xA4, 0xC0), (0xF0, 0xD0, 0xB0), (0xFC, 0xE0, 0xA8),
            (0xF8, 0xD8, 0x78), (0xD8, 0xF8, 0x78), (0xB8, 0xF8, 0xB8), (0xB8, 0xF8, 0xD8),
            (0x00, 0xFC, 0xFC), (0xF8, 0xD8, 0xF8), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
        ]


    def get_color(self, colorNum):
        if colorNum == 0x40:    # not drawn yet: show the backdrop color
            return self.colors[self.ppu.read_memory(0x3F00) & 0x3F]
        return self.colors[colorNum]

class Renderer():
    WIDTH = 256
    HEIGHT = 240

    def __init__(self, ppu, scale=1):
        self.palette = Palette(ppu)
        pygame.init()
        self.scale = scale
        self.window = pygame.display.set_mode([self.WIDTH*scale, self.HEIGHT*scale])
        pygame.display.set_caption('refNes')

        # The frame is an 8-bit surface whose palette is the 64 NES colors, so the PPU's
        # color numbers are copied in as raw bytes once per frame and SDL does the color
        # conversion. Entry 0x40 ("not drawn yet") is set to the backdrop color each frame.
        self.frame = pygame.Surface((self.WIDTH, self.HEIGHT), depth=8)
        self.frame.set_palette(list(self.palette.colors) + [(0, 0, 0)] * (256 - 64))

        # Speed limit: hold emulation to the NTSC frame rate (debugger 'limit' toggles it;
        # the setting lives on the CPU so it survives reset)
        self.limit_speed = getattr(ppu.cpu, 'limit_speed', True)
        self.next_frame = None   # when the next frame is due (time.perf_counter() seconds)

        # FPS overlay (toggled from the debugger; the setting lives on the CPU so it survives reset)
        self.show_fps = getattr(ppu.cpu, 'show_fps', False)
        self.font = None
        self.fps_text = None
        self.fps_frames = 0
        self.fps_start = None
        self.last_present = None

    def load_frame(self):
        """Copy the PPU's screen buffer (NES color numbers) into the frame surface."""
        ppu = self.palette.ppu
        self.frame.set_palette_at(0x40, self.palette.colors[ppu.memory[0x3F00] & 0x3F])
        data = bytes(ppu.screen)
        pitch = self.frame.get_pitch()
        buf = self.frame.get_buffer()     # locks the surface until released below
        if pitch == self.WIDTH:
            buf.write(data)
        else:
            for y in range(self.HEIGHT):
                buf.write(data[y*self.WIDTH:(y+1)*self.WIDTH], y * pitch)
        del buf

    def set_scale(self, scale):
        """Resize the window to `scale` times 256x240 and redraw the current frame."""
        self.scale = scale
        self.window = pygame.display.set_mode([self.WIDTH*scale, self.HEIGHT*scale])
        self.present()

    NTSC_FPS = 60.0988
    FRAME_TIME = 1 / NTSC_FPS

    def wait_for_frame(self):
        """Sleep until this frame is due, keeping an even 60.1 fps on average."""
        now = time.perf_counter()
        if self.next_frame is None or now - self.next_frame > 0.1:
            # first frame, or far behind (e.g. paused in the debugger): restart the clock
            # rather than racing to catch up
            self.next_frame = now
        elif now < self.next_frame:
            # Busy-wait instead of sleeping: with power-saving CPU governors, sleeping
            # lets the CPU clock down, the next frame then runs slow and arrives late.
            # Spinning keeps frame spacing even (measured: 4.6 ms jitter with sleep,
            # 0.65 ms spinning) for about the same CPU use, since emulation already
            # keeps one core nearly busy at full speed.
            deadline = self.next_frame
            while time.perf_counter() < deadline:
                pass
        # schedule from the deadline, not from now, so sleep overshoot doesn't add up;
        # a frame that ran a little late is made up by the next ones
        self.next_frame += self.FRAME_TIME

    def update_fps(self):
        """Count frames and refresh the FPS text about twice a second."""
        now = time.perf_counter()
        # a long gap means emulation was paused (e.g. in the debugger): start a new measurement
        if self.last_present is None or now - self.last_present > 0.25:
            self.fps_start = now
            self.fps_frames = 0
        self.last_present = now
        self.fps_frames += 1
        elapsed = now - self.fps_start
        if elapsed >= 0.5:
            fps = (self.fps_frames - 1) / elapsed
            self.fps_text = f"{fps:4.1f} fps  {100 * fps / self.NTSC_FPS:3.0f}%"
            self.fps_start = now
            self.fps_frames = 1

    def draw_fps(self):
        if self.font is None:
            pygame.font.init()
            self.font = pygame.font.Font(None, 20)
        text = self.font.render(self.fps_text or "-- fps", True, (255, 255, 255))
        box = text.get_rect(topleft=(4, 4)).inflate(6, 4)
        self.window.fill((0, 0, 0), box)
        self.window.blit(text, (box.x + 3, box.y + 2))

    def present(self):
        """Show the finished frame. Call once per frame (at vblank)."""
        self.load_frame()
        if self.scale == 1:
            self.window.blit(self.frame, (0, 0))
        else:
            # scaling can't write into the window directly (different pixel format)
            self.window.blit(pygame.transform.scale(self.frame, self.window.get_size()), (0, 0))
        if self.limit_speed:
            self.wait_for_frame()
        if self.show_fps:
            self.update_fps()
            self.draw_fps()
        pygame.display.update()
        # Keep the window responsive; the OS flags it as hung if events never get read.
        pygame.event.pump()
