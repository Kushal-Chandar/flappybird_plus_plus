import math
import numpy as np
from matplotlib import pyplot as plt
import pygame

plt.rcParams["figure.figsize"] = [3.50, 3.50]
plt.rcParams["figure.autolayout"] = True


def parabola(a: float, t: float, k: float):
    return math.pow(a * t * (1.0 - t), k)


def smoothstep(t: float):
    t1 = math.pow(t, 2)
    t2 = 1 - math.pow(1 - t, 2)
    return pygame.math.lerp(t1, t2, t)


points = np.linspace(0, 1, 100)

plt.plot(points, [math.pow(x, 2) for x in points], color="blue")
plt.plot(points, [smoothstep(x) for x in points], color="black")
plt.plot(points, [1 - math.pow(1 - x, 2) for x in points], color="green")
# plt.plot(points, [parabola(4, x, 2) for x in points], color="red")

plt.show()
