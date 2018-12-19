#!/usr/bin/env python3.7
"""

"""


from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn, ForkingMixIn
from dataclasses import dataclass
from random import random
from math import pi, cos, sin, acos
from pathlib import Path
from pyospray import *
from mss.tools import to_png
import numpy as np
from functools import partial
import logging
from collections import deque
from queue import Queue
from PIL import Image
from io import BytesIO


print = partial(print, flush=True)


_g_scenes = Queue()
WIDTH, HEIGHT = (256, 256)
BG = (38, 36, 54, 0)


class TapestryRequestHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		if self.path == '/':
			self.do_GET_index()
		elif self.path == '/random':
			u = random()
			v = random()
			theta = 2 * pi * u
			phi = acos(2 * v - 1)
			r = 200
			x = r * sin(phi) * cos(theta)
			y = r * sin(phi) * sin(theta)
			z = r * cos(phi)
			
			self.path = f'/{x}/{y}/{z}/0/1/0/{-x}/{-y}/{-z}'
			#print(self.path)
			self.do_GET_image()
			
		elif self.path == '/favicon.ico':
			self.send_error(404)
		else:
			self.do_GET_image()
	
	def do_GET_index(self):
		path = Path.cwd() / 'index.html'
		content = path.read_bytes()
		self.send_response(200)
		self.send_header('Content-Type', 'text/html')
		self.end_headers()
		self.wfile.write(content)
	
	def _do_GET_image(self, scene):
		x, y, z, ux, uy, uz, vx, vy, vz = map(float, self.path[1:].split('/'))
		with committing(scene.camera) as camera:
			camera.pos = (x, y, z)
			camera.up = (ux, uy, uz)
			camera.dir = (vx, vy, vz)
		
		scene.renderer.commit()
		
		scene.fb.clear(OSP_FB_COLOR)
		scene.renderer.render(scene.fb, OSP_FB_COLOR)
		data = ospToPixels(b"rgb", scene.size, scene.fb._ospray_object)
		'''
		source = np.frombuffer(data, dtype='B')
		data = source.copy()
		print(source[:8], source.shape)
		for j in range(HEIGHT):
			row = source[4*j*WIDTH:]
			for i in range(WIDTH):
				index = j * WIDTH + i
				r = row[4*i+0]
				g = row[4*i+1]
				b = row[4*i+2]
				a = row[4*i+3]
				w = a / 255
				if i < 4 and j < 4:
					print((r, g, b, a, w))
				composite = BG[3] != 0
				data[4*index+0] = r * w + (BG[0] * (1 - w) if composite else 0)
				data[4*index+1] = g * w + (BG[1] * (1 - w) if composite else 0)
				data[4*index+2] = b * w + (BG[2] * (1 - w) if composite else 0)
				data[4*index+3] = a * w + (BG[3] * (1 - w) if composite else 0)
		print(data[:8], data.shape)
		data = data.reshape((-1, 4))
		print(data[:4], data.shape)
		data = data[:, :-1]
		print(data[:4], data.shape)
		data = data.reshape((-1,))
		data = data.tobytes()
		'''
		return data
	
	def do_GET_image(self):
		scene = None
		try:
			try:
				scene = _g_scenes.get()
			except IndexError:
				print('making new scene')
				scene = make_scene()
		
			data = self._do_GET_image(scene)
			
			image = Image.frombytes('RGB', (WIDTH, HEIGHT), data, 'raw')
			f = BytesIO()
			image.save(f, 'JPEG')
			
			#png = to_png(data, (WIDTH, HEIGHT))
			
			self.send_response(200)
			self.send_header('Content-Type', 'image/jpeg')
			self.end_headers()
			self.wfile.write(f.getvalue())
		finally:
			assert scene is not None
			_g_scenes.put(scene)
	
	def log_message(*args):
		pass


@dataclass
class Scene:
	camera: Camera
	renderer: Renderer
	size: osp_vec2i
	fb: FrameBuffer
	

def make_scene():
	with committing(PiecewiseLinear()) as transferFunction:
		colors = np.array(builtin.colormaps['coolToWarm'], dtype='float32')
		with releasing(Data(OSP_FLOAT3, colors, 0)) as data:
			data.commit()
			transferFunction.colors = data
		
		opacities = 0.6 * np.array(builtin.opacitymaps['ramp'], dtype='float32')
		with releasing(Data(OSP_FLOAT, opacities, 0)) as data:
			data.commit()
			transferFunction.opacities = data
		
		transferFunction.valueRange = (0.0, 255.0)
	
	with committing(StructuredVolume()) as volume:
		voxels = np.fromfile('teapot.raw', dtype='float32').T
		#print(voxels.min(), voxels.max(), len(voxels.flat))
		with releasing(Data(OSP_FLOAT, voxels, 0)) as data:
			data.commit()
			volume.voxelData = data

		volume.transferFunction = transferFunction
		volume.voxelRange = (0.0, 255.0)
		volume.dimensions = (256, 256, 178)
		volume.gridOrigin = (-256/2, -256/2, -178/2)
		volume.voxelType = b'float'
	
	with committing(PerspectiveCamera()) as camera:
		camera.aspect = WIDTH / HEIGHT
		camera.pos = (0, 0, 0)
		camera.dir = (0.1, 0, 0.1)
		camera.up = (0, 1, 0)

	with committing(Model()) as model:
		model.add(volume)

	with committing(SciVis()) as renderer:
		#with committing(DirectionalLight(renderer)) as light:
		#	light.angularDiameter = 0.53
		#
		#lights = np.array([
		#	light,
		#], dtype=object)
		#with releasing(Data(OSP_LIGHT, lights, 0)) as data:
		#	data.commit()
		#	renderer.lights = data
		
		renderer.spp = 4
		renderer.bgColor = (BG[0]/255, BG[1]/255, BG[2]/255, BG[3]/255)
		renderer.model = model
		renderer.camera = camera
		#renderer.oneSidedLighting = False
	
	size = osp_vec2i()
	size.x = WIDTH
	size.y = HEIGHT
		
	fb = FrameBuffer(size, OSP_FB_SRGBA, OSP_FB_COLOR)
	
	return Scene(
		camera,
		renderer,
		size,
		fb,
	)


class MyHTTPServer(HTTPServer):
	request_queue_size = 100


class ForkingHTTPServer(ForkingMixIn, HTTPServer):
	request_queue_size = 100


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
	request_queue_size = 100


def main(port, verbose, mode):
	error = ospInit([]);
	if error != OSP_NO_ERROR:
		raise Exception('Error occurred', err)
		
	if verbose:
		logging.basicConfig(level=logging.DEBUG)
	
	if mode == 'threading':
		server_class = ThreadingHTTPServer
	elif mode == 'forking':
		server_class = ForkingHTTPServer
	elif mode == 'normal':
		server_class = MyHTTPServer
	else:
		raise NotImplementedError

	for _ in range(3):
		_g_scenes.put(make_scene())
	
	print(f'Listening at {port}...')
	
	server = server_class(('', port), TapestryRequestHandler)
	server.serve_forever()


def cli():
	import argparse
	import os
	
	parser = argparse.ArgumentParser()
	
	parser.add_argument('--port', type=int, default=8819)
	parser.add_argument('-v', '--verbose', action='store_true')
	parser.add_argument('--mode', choices=('threading', 'forking', 'normal'), default='normal')
	
	args = vars(parser.parse_args())
	
	main(**args)


if __name__ == '__main__':
	cli()
