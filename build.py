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

import shutil

from tools import *

global layers, buildings
layers, buildings = {}, {}

class Noise_Terrain:
    def __init__(self, chunks: tuple | list):
        self.noise_arr = []

        self.chunksx = chunks[0]
        self.chunksy = chunks[1]

        self.sizex = self.chunksx * 32
        self.sizey = self.chunksy * 32


    def generate_pixel(self, x, y):
        val = 0
        for counter, octave in enumerate(self.octave_arr):
            val += 1 / self.diviser ** counter * octave([x / self.sizex, y / self.sizey])

        return val


    def generate_noise(self, octaves: tuple | list, diviser: float, func = lambda x: x) -> np.ndarray:
        self.octave_arr = [
            PerlinNoise(octave * (self.chunksx + self.chunksy) / 6) 
            for octave in octaves
            ]
        
        self.diviser = diviser

        self.pic = np.zeros((self.sizex, self.sizey))

        print('generating noise')
        for i in tqdm(range(self.sizex * self.sizey)):

            x, y = divmod(i, self.sizex)

            self.pic[x, y] = make_in_bounds((func(self.generate_pixel(x, y)) + 1) / 2, 0, 1)


    def turn_into_chunkarrays(self, layernames):
        self.split_pic = []

        print(f'creating chunks')

        ch1 = []
        for i in tqdm(range(self.chunksx)):
            ch2 = []
            for j in range(self.chunksy):
                chunk = []
                for x in range(32):
                    for y in range(32):
                        layer = self.pic[i * 32 + x][j * 32 + y] * (len(layernames) - 1)
                        chunk.append((x, y, layer, layernames[round(layer)]))

                ch2.append(chunk)

            ch1.append(ch2)

        return ch1
    
    
    def save_to_file(self):
        np.save(f'map/terrain', self.pic, allow_pickle=False)
        

    def load_from_file(self):
        print('loading chunks')

        for i in tqdm(range(1)):
            self.pic = np.load(f'map/terrain.npy', allow_pickle=False)

            
def start_packing():
    os.mkdir('map')


def pack_world(file_name):
    shutil.make_archive(f'saves/{file_name}', 'zip', 'map')

        
    for i in os.listdir('map'):
        os.remove(f'map/{i}')

    os.rmdir('map')


def unpack_world(file_name):
    shutil.unpack_archive(f'saves/{file_name}.zip', 'map')


def rm_temp_world():
    for i in os.listdir('map'):
        os.remove(f'map/{i}')

    os.rmdir('map')


class sdl2_tile:
    def __init__(self, texture: sdl2.video.Texture, rect: pygame.Rect | None = None):
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
            (tile.texture, (tile.rect.x + x_off, tile.rect.y + y_off))
            for tile in self.tiles
        ]

        fblits_pass = [tile for tile in fblits_pass if self.is_in_bounds(tile, viewport_size)]

        for i in fblits_pass:
            renderer.blit(i[0], pygame.Rect(i[1][0], i[1][1], i[0].width, i[0].height))


    def add(self, tile: sdl2_tile):
        self.tiles.append(tile)


class sdl2_building:
    def __init__(self, texture: sdl2.video.Texture, tiles_size: tuple | list, rect: pygame.Rect | None = None):
        self.texture = texture
        self.rect = rect
        self.tilesx = tiles_size[0]
        self.tilesy = tiles_size[1]


class building_Group:
    def __init__(self, tiles: list | tuple):
        self.tiles = list(tiles)

    def is_in_bounds(self, i, viewport_size):
        if i[1][0] + i[0].width >= - i[2][0] * 64 and i[1][0] <= viewport_size[0] + i[2][0] * 64:
                if i[1][1] + i[0].height >= - i[2][1] * 32 and i[1][1] <= viewport_size[1] + i[2][1] * 32:
                    return True
                
        return False
    

    def draw(self, renderer: sdl2.video.Renderer, viewport_pos: tuple | list, viewport_size: tuple | list):
        x_off = viewport_pos[0]
        y_off = viewport_pos[1]

        fblits_pass = [
            (spr.texture, (spr.rect.x + x_off, spr.rect.y + y_off), (spr.tilesx, spr.tilesy))
            for spr in self.tiles
        ]

        fblits_pass = [tile for tile in fblits_pass if self.is_in_bounds(tile, viewport_size)]

        for i in fblits_pass:
            renderer.blit(i[0], pygame.Rect(i[1][0], i[1][1] - 16 + i[0].height, i[0].width, i[0].height))


    def add(self, tile: sdl2_tile):
        self.tiles.append(tile)


class Chunk:
    '''A 32x32 chunk of tiles, buildings and entities'''
    def __init__(self, pos: tuple | list, renderer: sdl2.video.Renderer, layernames: tuple | list, layerimgs: tuple | list, tiles = list | tuple):
        self.x = pos[0]
        self.y = pos[1]

        self.renderer = renderer

        self.tile_group = Tile_Group([])
        self.tiles = tiles

        self.layernames = layernames
        self.layerimgs = layerimgs


    def sort_tiles(self):
        self.tiles.sort(key = lambda x: x[0] + x[1])


    def build(self):
        for tile in self.tiles:
            if tile[-1] not in self.layernames:
                raise IndexError(f'tile "{tile[-1]}" not found in layers')
            
            else:
                x, y = to_cartesian((tile[0], tile[1]))
                z = tile[2]

                spr = sdl2_tile(self.renderer)
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
        # viewport_center = to_cartesian(((- viewport_pos[0] + (viewport_size[0] / 2)) / (64 * 32),(- viewport_pos[1]) / (32 * 32)))
        viewport_center = to_cartesian(((- viewport_pos[0] + viewport_size[0] / 2) / 2048, (- viewport_pos[1] + viewport_size[1] / 2) / 1024))

        for c in self.chunks:
            if c.x - viewport_center[0] >= - render_distance and c.x - viewport_center[0] <= render_distance and c.y - viewport_center[1] >= - render_distance and c.y - viewport_center[1] <= render_distance:
                x, y = to_cartesian((c.x, c.y))

                c.blit_on((viewport_pos[0] + x * 32 * 32, viewport_pos[1] + y * 16 * 32), (viewport_size[0], viewport_size[1]))


    def build_chunks(self):
        print(f'rendering chunks')

        for c in tqdm(self.chunks):
            c.build()


def create_noise(q, x, y, names, alive, from_file=False, load_file=None):
    test_noise = Noise_Terrain((x, y))

    if not from_file:
        test_noise.generate_noise([2, 6], 4, func=lambda x: sign(x) * (-e ** (-16 * x ** 2) + 1))
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

    zoom = 1

    window = sdl2.video.Window('isometric game', (WIDTH, HEIGHT))
    window.resizable = True
    renderer = sdl2.video.Renderer(window, accelerated = 1, vsync = True)

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

    split_building_file = os.listdir("buildings/")

    building_names = [x[:-4] for x in split_building_file]

    building_images = [pygame.image.load(f'buildings/{x}') for x in split_building_file]
    building_textures = [sdl2.video.Texture.from_surface(renderer, x) for x in building_images]

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

    spr = sdl2_building(building_textures[2], (2, 2), pygame.Rect(-1, 0, 128, 128))
    sprgr = building_Group([spr])

    bwbh_wh_ratio = (BASE_HEIGHT * WIDTH) / (BASE_WIDTH * HEIGHT)

    if bwbh_wh_ratio < 1:
        LOGICAL_WIDTH = BASE_WIDTH * min(1, bwbh_wh_ratio)
        LOGICAL_HEIGHT = BASE_HEIGHT * max(1, bwbh_wh_ratio)
        renderer.logical_size = (LOGICAL_WIDTH * zoom, LOGICAL_HEIGHT * zoom)

    else:
        LOGICAL_WIDTH = BASE_WIDTH * max(1, 1 / bwbh_wh_ratio)
        LOGICAL_HEIGHT = BASE_HEIGHT * min(1, 1 / bwbh_wh_ratio)
        renderer.logical_size = (LOGICAL_WIDTH * zoom, LOGICAL_HEIGHT * zoom)

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

                bwbh_wh_ratio = (BASE_HEIGHT * WIDTH) / (BASE_WIDTH * HEIGHT)

                if bwbh_wh_ratio < 1:
                    LOGICAL_WIDTH = BASE_WIDTH * min(1, bwbh_wh_ratio)
                    LOGICAL_HEIGHT = BASE_HEIGHT * max(1, bwbh_wh_ratio)
                    renderer.logical_size = (LOGICAL_WIDTH * zoom, LOGICAL_HEIGHT * zoom)

                else:
                    LOGICAL_WIDTH = BASE_WIDTH * max(1, 1 / bwbh_wh_ratio)
                    LOGICAL_HEIGHT = BASE_HEIGHT * min(1, 1 / bwbh_wh_ratio)
                    renderer.logical_size = (LOGICAL_WIDTH * zoom, LOGICAL_HEIGHT * zoom)

            elif event.type == pygame.MOUSEWHEEL:
                prev_logical_size = renderer.logical_size

                zoom += - sign(event.y) / 20
                zoom = max(0.1, zoom)
                zoom = min(zoom, 2)

                bwbh_wh_ratio = (BASE_HEIGHT * WIDTH) / (BASE_WIDTH * HEIGHT)

                if bwbh_wh_ratio < 1:
                    LOGICAL_WIDTH = BASE_WIDTH * min(1, bwbh_wh_ratio)
                    LOGICAL_HEIGHT = BASE_HEIGHT * max(1, bwbh_wh_ratio)
                    renderer.logical_size = (LOGICAL_WIDTH * zoom, LOGICAL_HEIGHT * zoom)

                else:
                    LOGICAL_WIDTH = BASE_WIDTH * max(1, 1 / bwbh_wh_ratio)
                    LOGICAL_HEIGHT = BASE_HEIGHT * min(1, 1 / bwbh_wh_ratio)
                    renderer.logical_size = (LOGICAL_WIDTH * zoom, LOGICAL_HEIGHT * zoom)

                if zoom > 0.01 and zoom < 2:
                    viewport_pos[0] -= (prev_logical_size[0] - renderer.logical_size[0]) / (WIDTH / mouse_x)
                    viewport_pos[1] -= (prev_logical_size[1] - renderer.logical_size[1]) / (HEIGHT / mouse_y)

        mouse_clicked = pygame.mouse.get_pressed()

        last_mouse_x, last_mouse_y = mouse_x, mouse_y
        mouse_x, mouse_y = pygame.mouse.get_pos()

        if mouse_clicked[0]:
            viewport_pos[0] += (mouse_x - last_mouse_x) * (LOGICAL_WIDTH / WIDTH) * zoom
            viewport_pos[1] += (mouse_y - last_mouse_y) * (LOGICAL_HEIGHT / HEIGHT) * zoom

        world.render_chunks(1.5, viewport_pos, (BASE_WIDTH * zoom, BASE_HEIGHT * zoom))

        sprgr.draw(renderer, viewport_pos, (BASE_WIDTH * zoom, BASE_HEIGHT * zoom))

        renderer.present()
        # print(clock.get_fps())

if __name__ == '__main__':
    main()