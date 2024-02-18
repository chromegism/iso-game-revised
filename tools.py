def sign(x: int | float):
    if x != 0:
        return x / abs(x)
    else:
        return 0

def to_cartesian(coords: tuple) -> tuple:
    """Converts Cartesian coordinates (x, y) into Isometric view coordinates"""

    x = - coords[0] + coords[1]
    y = coords[0] + coords[1]

    return (x, y)

def make_in_bounds(num, low, high):
    return max(low, min(num, high))

def divmod(num, x):
    from math import floor

    return [num % x, floor(num / x)]

if __name__ == '__main__':
    print(divmod(42, 37))