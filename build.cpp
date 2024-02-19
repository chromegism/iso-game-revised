#include <iostream>
#include <stdio.h>
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <tuple>
#include <math.h>
#include <vector>
#include <filesystem>
#include <algorithm>
#undef main

#define LOGICAL_WIDTH  1280
#define LOGICAL_HEIGHT 720

using namespace std;
namespace fs = std::filesystem;

float sign (float x)
{
	if (!x == 0)
	{
		return x / abs(x);
	}
	else
	{
		return 0;
	}
}


tuple<float, float> to_cartesian(tuple<float, float> coords)
{
	float x = - get<0>(coords) + get<1>(coords);
	float y = get<0>(coords) + get<1>(coords);

	tuple<float, float> t = make_tuple(x, y);

	return t;
}


float make_in_bounds(float val, float low, float high)
{
	return max(low, min(val, high));
}


float make_between_0_1(float val)
{
	return max(0.0f, min(val, 1.0f));
}

tuple<int, int> divmod(int num, int modulator)
{
	tuple<int, int> t = make_tuple<int, int>(num % modulator, floor(num / modulator));

	return t;
}


class Tile
{
	public:
		SDL_Renderer *renderer;
		SDL_Texture *texture;
		SDL_Point size;
		SDL_Rect rect;

		void render()
		{
			SDL_RenderCopy(renderer, texture, NULL, &rect);
		}
};


class TileGroup
{
	public:
		vector<Tile> tiles;

		bool is_in_bounds(Tile tile, int x_off, int y_off, int viewport_size_x, int viewport_size_y)
		{
			if (tile.rect.x + x_off + tile.rect.w >= 0 && tile.rect.x + y_off <= viewport_size_x)
			{
				if (tile.rect.y + x_off + tile.rect.h >= 0 && tile.rect.y + y_off <= viewport_size_y)
				{
					return true;
				}
			}

			return false;
		}

		void draw(SDL_Renderer *renderer, int viewport_pos_x, int viewport_pos_y, int viewport_size_x, int viewport_size_y)
		{
			for (Tile tile : tiles)
			{
				if (is_in_bounds(tile, viewport_pos_x, viewport_pos_y, viewport_size_x, viewport_size_y))
				{
					SDL_RenderCopy(tile.renderer, tile.texture, NULL, &tile.rect);
				}
			}
		}
};


class Chunk
{
	public:
		int x;
		int y;

		SDL_Renderer *renderer;

		TileGroup tile_group;

		void draw(int viewport_pos_x, int viewport_pos_y, int viewport_size_x, int viewport_size_y)
		{
			tile_group.draw(renderer, viewport_pos_x, viewport_pos_y, viewport_size_x, viewport_size_y);
		}

		void sort_tiles()
		{
			
		}

		void add_tile(Tile tile)
		{
			tile_group.tiles.push_back(tile);
		}

		void add_tiles(vector<Tile> tiles)
		{
			for (Tile tile : tiles)
			{
				add_tile(tile);
			}
		}
};


SDL_Point gettexturesize(SDL_Texture *texture) {
    SDL_Point size;
    SDL_QueryTexture(texture, NULL, NULL, &size.x, &size.y);
    return size;
}


Tile load_tile(SDL_Renderer *renderer, const char *file)
{
	Tile t;
	t.renderer = renderer;
	t.texture = IMG_LoadTexture(renderer, file);
	t.size = gettexturesize(t.texture);
	t.rect.x = 0;
	t.rect.y = 0;
	t.rect.w = t.size.x;
	t.rect.h = t.size.y;

	return t;
}


int gen_rand(int min, int max)
{
	return rand() % (max - min + 1) + min;
}


int main(int argc, char* argv[])
{
	int ScreenWidth = 1280;
	int ScreenHeight = 720;

    SDL_Window *window;
    SDL_Renderer *renderer;

    if (SDL_Init(SDL_INIT_VIDEO) < 0)
	{
		printf("Couldn't initialize SDL: %s\n", SDL_GetError());
		exit(1);
	}

    window = SDL_CreateWindow("isometric game", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, ScreenWidth, ScreenHeight, SDL_RENDERER_ACCELERATED | SDL_WINDOW_RESIZABLE);

    if (!window)
	{
		printf("Failed to open %d x %d window: %s\n", ScreenWidth, ScreenHeight, SDL_GetError());
		exit(1);
	}

    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "linear");

	renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);

	if (!renderer)
	{
		printf("Failed to create renderer: %s\n", SDL_GetError());
		exit(1);
	}

	SDL_RenderSetLogicalSize(renderer, LOGICAL_WIDTH, LOGICAL_HEIGHT);

	vector<Tile> layer_textures;

	int texture_count = 0;
	for (const auto & entry : fs::directory_iterator("layers")) {
		fs::path p = entry.path();
		Tile tile = load_tile(renderer, p.string().c_str());
		tile.rect.x = gen_rand(0, LOGICAL_WIDTH - 64);
		tile.rect.y = gen_rand(0, LOGICAL_HEIGHT - 48);
    	layer_textures.push_back(tile);
		texture_count++;
  	}

	int viewport_pos_x = 0;
	int viewport_pos_y = 0;

    bool running = true;
	SDL_Event event;

	SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);

	Chunk ch;
	ch.add_tiles(layer_textures);

    while (running)
    {
		SDL_RenderClear(renderer);

		while(SDL_PollEvent(&event))
		{
			switch(event.type)
			{
				case SDL_QUIT:
					running = false;
					break;

				case SDL_KEYDOWN:
					switch(event.key.keysym.sym)
					{
						case SDLK_ESCAPE:
						running = false;
					}
					break;
			}
		}

		// SDL_RenderCopy(renderer, layer_textures[0].texture, NULL, &layer_textures[0].rect);
		// layer_textures[gen_rand(0, 8)].render();

		ch.draw(viewport_pos_x, viewport_pos_y, LOGICAL_WIDTH, LOGICAL_HEIGHT);

		SDL_RenderPresent(renderer);
    }

    return 0;
}