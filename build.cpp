#include <iostream>
#include <stdio.h>
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <tuple>
#include <math.h>
#include <vector>
#include <filesystem>
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


SDL_Point getsize(SDL_Texture *texture) {
    SDL_Point size;
    SDL_QueryTexture(texture, NULL, NULL, &size.x, &size.y);
    return size;
}


Tile load_tile(SDL_Renderer *renderer, const char *file)
{
	Tile t;
	t.renderer = renderer;
	t.texture = IMG_LoadTexture(renderer, file);
	t.size = getsize(t.texture);
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
    	layer_textures.push_back(load_tile(renderer, p.string().c_str()));
		texture_count++;
  	}

    bool running = true;
	SDL_Event event;

	SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);

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
		layer_textures[gen_rand(0, 8)].render();

		SDL_RenderPresent(renderer);
    }

    return 0;
}