# Added a mechanic for saving and loading terrain

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame
import pygame._sdl2 as sdl2

import sys
import random
from scipy.ndimage import gaussian_filter
from tqdm import tqdm

from perlin_noise import PerlinNoise
from math import *
import numpy as np
import multiprocessing as mp
import matplotlib.pyplot as plt

import shutil

global layers
layers = {}

def sign(x: int | float):
    if x != 0:
        return x / abs(x)
    else:
        return 0

def average_of_list(x: list | tuple | set):
    return sum(x)/len(x)

def to_cartesian(coords: tuple) -> tuple:
    """Converts Cartesian coordinates (x, y) into Isometric view coordinates"""

    x = - coords[0] + coords[1]
    y = coords[0] + coords[1]

    return (x, y)

class Noise_Terrain:
    def __init__(self, octaves: tuple | list, chunks: tuple | list, base = 2):
        self.noise_arr = []

        self.chunksx = chunks[0]
        self.chunksy = chunks[1]

        for i in octaves:
            self.noise_arr.append(PerlinNoise(i * (self.chunksx + self.chunksy) / 6))

        self.sizex = self.chunksx * 32
        self.sizey = self.chunksy * 32

        self.base = base

    def generate_noise(self, seed: int | None = None, func = lambda x: x):
        pic = np.zeros((self.sizex, self.sizey), np.float16)
        #pic = []

        print(f'generating noise')

        for i in tqdm(range(self.sizex)):
            # print(f'row {i + 1} / {self.chunksx * 32}')
            row = []
            for j in range(self.sizey):
                noise_val = 0
                for c, noise in enumerate(self.noise_arr):
                    noise_val += 1 / self.base ** c * noise([i / self.sizex, j / self.sizey])

                #row.append(min(max((func(noise_val) + 1) / 2, -1), 1))
                pic[i][j] = min(max((func(noise_val) + 1) / 2, -1), 1)

            #pic.append(row)

        self.noise_pic = pic
        #plt.imshow(self.noise_pic, cmap='gray', vmin=0, vmax = 1)
        #plt.show()
        return pic

    def gaussian_blur(self, kernel_size = 5):
        self.noise_pic = gaussian_filter(self.noise_pic, kernel_size)

    def turn_into_chunkarrays(self, sp):
        self.split_noise_pic = []

        print(f'creating chunks')

        ch1 = []
        for i in tqdm(range(self.chunksx)):
            ch2 = []
            for j in range(self.chunksy):
                default_full_chunk = []
                for x in range(32):
                    for y in range(32):
                        layer = self.noise_pic[i * 32 + x][j * 32 + y] * (len(sp) - 1)
                        default_full_chunk.append((x, y, layer, sp[round(layer)]))

                ch2.append(default_full_chunk)

            ch1.append(ch2)

        return ch1
    
    def save_to_file(self):
        np.save(f'map/terrain', self.noise_pic, allow_pickle=False)

    def load_from_file(self):
        print('loading chunks')

        for i in tqdm(range(1)):
            self.noise_pic = np.load(f'map/terrain.npy', allow_pickle=False)
            
def start_packing():
    os.mkdir('map')

def pack_world(file_name):
    shutil.make_archive(f'{file_name}', 'zip', 'map')
        
    for i in os.listdir('map'):
        os.remove(f'map/{i}')

    os.rmdir('map')

def unpack_world(file_name):
    shutil.unpack_archive(f'{file_name}.zip', 'map')

def rm_temp_world():
    for i in os.listdir('map'):
        os.remove(f'map/{i}')

    os.rmdir('map')

class sdl2_sprite:
    def __init__(self, texture: sdl2.video.Texture, rect: pygame.Rect | tuple | list | None = None):
        self.texture = texture
        self.rect = rect

class Tile_Group:
    def __init__(self, tiles: list | tuple):
        self.tiles = list(tiles)

    def is_in_bounds(self, i, viewport_size):
        if i[1][0] + i[0].width >= 0 and i[1][0] <= viewport_size[0]:
                if i[1][1] + i[0].height >= 0 and i[1][1] <= viewport_size[1]:
                    return True
                
        return False

    def draw(self, renderer: sdl2.video.Renderer, viewport_pos: tuple | list, viewport_size: tuple | list):
        x_off = viewport_pos[0]
        y_off = viewport_pos[1]

        fblits_pass = [
            (spr.texture, (spr.rect.x + x_off, spr.rect.y + y_off))
            for spr in self.tiles
        ]

        fblits_pass = [tile for tile in fblits_pass if self.is_in_bounds(tile, viewport_size)]

        for i in fblits_pass:
            renderer.blit(i[0], pygame.Rect(i[1][0], i[1][1], i[0].width, i[0].height))

    def add(self, tile: sdl2_sprite):
        self.tiles.append(tile)

class Chunk:
    '''A 32x32 chunk of tiles, buildings and entities'''
    def __init__(self, pos: tuple | list, renderer: sdl2.video.Renderer, spritenames: tuple | list, spriteimgs: tuple | list, tiles = list | tuple):
        self.x = pos[0]
        self.y = pos[1]

        self.renderer = renderer

        self.tile_group = Tile_Group([])
        self.tiles = tiles

        self.spritenames = spritenames
        self.spriteimgs = spriteimgs

    def sort_tiles(self):
        self.tiles.sort(key = lambda x: x[0] + x[1])

    def build(self):
        for tile in self.tiles:
            if tile[-1] not in self.spritenames:
                raise IndexError(f'tile "{tile[-1]}" not found in layers')
            
            else:
                x, y = to_cartesian((tile[0], tile[1]))
                z = tile[2]

                spr = sdl2_sprite(self.renderer)
                spr.texture = layers[tile[-1]]
                w = spr.texture.width
                h = w / 2
                th = spr.texture.height

                spr.rect = pygame.Rect((x * w / 2 - 32, y * h / 2 - z * 14, w, th))
                self.tile_group.add(spr)

    def blit_on(self, viewport_pos: tuple| list, viewport_size: tuple | list):
        self.tile_group.draw(self.renderer, viewport_pos, viewport_size)

    def add_tile(self, tile: tuple | list, sort_tiles = True, rerender = True):
        self.tiles.append(tuple(tile))

        if sort_tiles:
            self.sort_tiles()
        
        if rerender:
            self.build()

    def add_tiles(self, tiles: tuple | list, sort_tiles = True, rerender = True):
        for tile in tiles:
            self.tiles.append(tuple(tile))

        if sort_tiles:
            self.sort_tiles()
        
        if rerender:
            self.build()

    def __len__(self):
        return len(self.tiles)
    
    def __getitem__(self, x):
        return self.tiles[x]

    # def get_size(self):
    #     return (max(self.tiles, key=lambda x: x[0]) - min(self.tiles, key=lambda x: x[0]), max(self.tiles, key=lambda x: x[1]) - min(self.tiles, key=lambda x: x[1]))

class Chunk_Group:
    def __init__(self, renderer):
        self.chunks = []
        self.renderer = renderer

    def add_chunk(self, chunk: Chunk):
        self.chunks.append(chunk)

    def sort_chunks(self):
        self.chunks.sort(key=lambda i: i.x + i.y)

    def render_chunks(self, render_distance: float | int, viewport_pos: tuple | list, viewport_size: tuple | list):
        viewport_center = to_cartesian(((- viewport_pos[0] + (viewport_size[0] / 2)) / (64 * 32),(- viewport_pos[1]) / (32 * 32)))
        # viewport_center = to_cartesian((- viewport_pos[0] / (64 * 32), - viewport_pos[1] / (32 * 32)))

        for c in self.chunks:
            if c.x - viewport_center[0] >= - render_distance and c.x - viewport_center[0] <= render_distance and c.y - viewport_center[1] >= - render_distance and c.y - viewport_center[1] <= render_distance:
                x, y = to_cartesian((c.x, c.y))

                c.blit_on((viewport_pos[0] + x * 32 * 32, viewport_pos[1] + y * 16 * 32), (viewport_size[0], viewport_size[1]))

    def build_chunks(self):
        print(f'rendering chunks')

        for c in tqdm(self.chunks):
            c.build()

def create_noise(q, x, y, names, alive, from_file=False, load_file=None):
    test_noise = Noise_Terrain((2, 6), (x, y), base=4)

    if not from_file:
        test_noise.generate_noise(func=lambda x: sign(x) * (-e ** (-16 * x ** 2) + 1))
        #test_noise.gaussian_blur()
        start_packing()
        test_noise.save_to_file()
        pack_world('save')

    else:
        unpack_world(load_file)
        test_noise.load_from_file()
        rm_temp_world()

    noise_arr = test_noise.turn_into_chunkarrays(names)

    q.put(noise_arr)
    print('passing to main process')

    alive.value = 0

def main():
    args = sys.argv[1:]
    load = False
    load_file = None
    if len(args) > 0:
        load = True
        load_file = args[0]

    WIDTH = 1280
    HEIGHT = 720

    BASE_WIDTH = 1920
    BASE_HEIGHT = 1080

    CHUNKSX = 8
    CHUNKSY = 8

    window = sdl2.video.Window('isometric game', (WIDTH, HEIGHT))
    window.resizable = True
    renderer = sdl2.video.Renderer(window, accelerated = 1, vsync = True)
    renderer.logical_size = (WIDTH, HEIGHT)

    clock = pygame.time.Clock()

    split_tile_file = [x.split() for x in open('layers.txt', 'r')]
    temp_list = []
    for i in split_tile_file:
        for j in range(int(i[1])):
            temp_list.append(i)

    split_tile_file = temp_list

    tile_names = [x[0][:-4] for x in split_tile_file]

    tile_images = [pygame.image.load(f'layers/{x[0]}') for x in split_tile_file]
    tile_textures = [sdl2.video.Texture.from_surface(renderer, x) for x in tile_images]

    for i, name in enumerate(tile_names):
        layers[name] = tile_textures[i]

    viewport_pos = [0, 0]

    window.set_icon(random.choice(tile_images))
    fullscreen = False

    mp.set_start_method('spawn')
    process_alive = mp.Value('i', 1)
    q = mp.Queue()
    noise_process = mp.Process(target=create_noise, args=[q, CHUNKSX, CHUNKSY, tile_names, process_alive, load, load_file], daemon=True)
    noise_process.start()

    while process_alive.value == 1:
        renderer.clear()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
               print(f'\tterminated')
               noise_process.terminate()
               pygame.quit()
               sys.exit()
    
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                   print(f'\tterminated')
                   noise_process.terminate()
                   pygame.quit()
                   sys.exit()

                elif event.key == pygame.K_F11:
                    fullscreen = not fullscreen

                    if fullscreen:
                        window.set_fullscreen(True)

                    else:
                        window.set_windowed()

                    WIDTH = window.size[0]
                    HEIGHT = window.size[1]

                    renderer.set_viewport(pygame.Rect(0, 0, WIDTH, HEIGHT))

            elif event.type == pygame.WINDOWRESIZED:
                WIDTH = window.size[0]
                HEIGHT = window.size[1]

                renderer.set_viewport(pygame.Rect(0, 0, WIDTH, HEIGHT))
                renderer.logical_size = (BASE_WIDTH, BASE_HEIGHT)

        renderer.present()

        clock.tick(30)

    noise_arr = q.get()
    noise_process.join()

    world = Chunk_Group(renderer)

    for ix in range(CHUNKSX):
        for iy in range(CHUNKSY):
            s = ix * CHUNKSX + iy
            testchunk = Chunk((ix - floor(CHUNKSX / 2), iy - floor(CHUNKSY / 2)), renderer, tile_names, tile_textures, [])

            testchunk.add_tiles(noise_arr[ix][iy], rerender=False)
            world.add_chunk(testchunk)

            # print(testchunk.get_size())

    mouse_x, mouse_y = (0, 0)

    world.build_chunks()

    while True:
        renderer.clear()
        dt = clock.tick()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                elif event.key == pygame.K_F11:
                    fullscreen = not fullscreen

                    if fullscreen:
                        window.set_fullscreen(True)

                    else:
                        window.set_windowed()

                    WIDTH = window.size[0]
                    HEIGHT = window.size[1]

                    renderer.set_viewport(pygame.Rect(0, 0, WIDTH, HEIGHT))

            elif event.type == pygame.WINDOWRESIZED:
                WIDTH = window.size[0]
                HEIGHT = window.size[1]

                renderer.set_viewport(pygame.Rect(0, 0, WIDTH, HEIGHT))
                renderer.logical_size = (BASE_WIDTH, BASE_HEIGHT)

        mouse_clicked = pygame.mouse.get_pressed()

        last_mouse_x, last_mouse_y = mouse_x, mouse_y
        mouse_x, mouse_y = pygame.mouse.get_pos()

        if mouse_clicked[0]:
            viewport_pos[0] += (mouse_x - last_mouse_x) * max((BASE_WIDTH / WIDTH), (BASE_HEIGHT / HEIGHT))
            viewport_pos[1] += (mouse_y - last_mouse_y) * max((BASE_WIDTH / WIDTH), (BASE_HEIGHT / HEIGHT))

        world.render_chunks(1.5, viewport_pos, (BASE_WIDTH, BASE_HEIGHT))

        renderer.present()
        # print(clock.get_fps())

if __name__ == '__main__':
    main()