#include <iostream>
#include <stdio.h>
#include <SDL2/SDL.h>
#include <tuple>
#include <math.h>
#undef main

#define SCREEN_WIDTH   1280
#define SCREEN_HEIGHT  720

using namespace std;

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
	return max(0, min(val, 1));
}

tuple<int, int> divmod(int num, int modulator)
{
	tuple<int, int> t = make_tuple<int, int>(num % modulator, floor(num / modulator));

	return t;
}

int main (int argc, char* argv[])
{
    SDL_Window *window;
    SDL_Renderer *renderer;

    if (SDL_Init(SDL_INIT_VIDEO) < 0)
	{
		printf("Couldn't initialize SDL: %s\n", SDL_GetError());
		exit(1);
	}

    window = SDL_CreateWindow("isometric game", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, SCREEN_WIDTH, SCREEN_HEIGHT, SDL_RENDERER_ACCELERATED | SDL_WINDOW_RESIZABLE);

    if (!window)
	{
		printf("Failed to open %d x %d window: %s\n", SCREEN_WIDTH, SCREEN_HEIGHT, SDL_GetError());
		exit(1);
	}

    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "linear");

	renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);

	if (!renderer)
	{
		printf("Failed to create renderer: %s\n", SDL_GetError());
		exit(1);
	}

    bool running = true;
	SDL_Event event;

    while (running)
    {
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
    }

    return 0;
}