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

float sign(float x)
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


SDL_Rect isometrify(SDL_Rect coords)
{
	float x = - coords.x + coords.y;
	float y = coords.x + coords.y;

	SDL_Rect r;
	r.x = x;
	r.y = y;
	r.w = coords.w;
	r.h = coords.h;

	return r;
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
		SDL_Rect rect;
		SDL_Point iso_pos;

		void render()
		{
			SDL_RenderCopy(renderer, texture, NULL, &rect);
		}
};


class TileGroup
{
	public:
		vector<Tile> tiles;

		bool is_in_bounds(SDL_Rect rect, int x_off, int y_off, int viewport_size_x, int viewport_size_y)
		{
			if (rect.x + x_off + rect.w >= 0 && rect.x + y_off <= viewport_size_x)
			{
				if (rect.y + x_off + rect.h >= 0 && rect.y + y_off <= viewport_size_y)
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
				SDL_Rect isorect = isometrify(tile.rect);
				isorect.x = isorect.x * 32 + viewport_pos_x;
				isorect.y = isorect.y * 16 + viewport_pos_y;

				if (is_in_bounds(isorect, viewport_pos_x, viewport_pos_y, viewport_size_x, viewport_size_y))
				{					
					SDL_RenderCopy(tile.renderer, tile.texture, NULL, &isorect);
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
			sort(tile_group.tiles.begin(), tile_group.tiles.end(), [](const Tile t1, const Tile t2){
				SDL_Rect rect1 = isometrify(t1.rect);
				SDL_Rect rect2 = isometrify(t2.rect);

				return (rect1.x + rect1.y < rect2.x + rect2.y);
				});
		}

		void add_tile(Tile tile, bool sort = true)
		{
			tile_group.tiles.push_back(tile);

			if (sort)
			{
				sort_tiles();
			}
		}

		void add_tiles(vector<Tile> tiles, bool sort = true)
		{
			for (Tile tile : tiles)
			{
				add_tile(tile, false);
			}

			if (sort)
			{
				sort_tiles();
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
	SDL_Point size = gettexturesize(t.texture);
	t.rect.x = 0;
	t.rect.y = 0;
	t.rect.w = size.x;
	t.rect.h = size.y;

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
		tile.rect.x = 0;
		tile.rect.y = texture_count;
		layer_textures.push_back(tile);
		texture_count++;
	}

	float viewport_pos_x = 0;
	float viewport_pos_y = 0;

	int mouse_x, mouse_y;
	int last_mouse_x, last_mouse_y;

	SDL_GetMouseState(&mouse_x, &mouse_y);

	bool mouse_pressed[3];

	float zoom = 1;

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
					continue;

				case SDL_KEYDOWN:
					switch(event.key.keysym.sym)
					{
						case SDLK_ESCAPE:
						running = false;
					}
					continue;

				case SDL_MOUSEBUTTONDOWN:
					if (event.button.button == SDL_BUTTON_LEFT)
					{
						mouse_pressed[0] = true;
					}
					else if (event.button.button == SDL_BUTTON_MIDDLE)
					{
						mouse_pressed[1] = true;
					}
					else if (event.button.button == SDL_BUTTON_RIGHT)
					{
						mouse_pressed[2] = true;
					}
					continue;

				case SDL_MOUSEBUTTONUP:
					if (event.button.button == SDL_BUTTON_LEFT)
					{
						mouse_pressed[0] = false;
					}
					else if (event.button.button == SDL_BUTTON_MIDDLE)
					{
						mouse_pressed[1] = false;
					}
					else if (event.button.button == SDL_BUTTON_RIGHT)
					{
						mouse_pressed[2] = false;
					}
					continue;
			}
		}

		// SDL_RenderCopy(renderer, layer_textures[0].texture, NULL, &layer_textures[0].rect);
		// layer_textures[gen_rand(0, 8)].render();

		last_mouse_x = mouse_x;
		last_mouse_y = mouse_y;
		SDL_GetMouseState(&mouse_x, &mouse_y);

		if (mouse_pressed[0])
		{
			viewport_pos_x += (mouse_x - last_mouse_x) * (LOGICAL_WIDTH / ScreenWidth) * zoom;
			viewport_pos_y += (mouse_y - last_mouse_y) * (LOGICAL_HEIGHT / ScreenHeight) * zoom;
		}

		ch.draw(viewport_pos_x, viewport_pos_y, LOGICAL_WIDTH, LOGICAL_HEIGHT);

		SDL_RenderPresent(renderer);
    }

    return 0;
}