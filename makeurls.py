from random import random
from math import *

def make_url():
	u = random()
	v = random()
	theta = 2 * pi * u
	phi = acos(2 * v - 1)
	r = 200
	x = r * sin(phi) * cos(theta)
	y = r * sin(phi) * sin(theta)
	z = r * cos(phi)
	
	return f'http://accona.eecs.utk.edu:8819/image/supernova/{x}/{y}/{z}/0/1/0/{-x}/{-y}/{-z}/256/tiling,0-1'


for _ in range(100000):
	print(make_url())
