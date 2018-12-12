#!/usr/bin/env python3.7
"""

"""


from http.server import HTTPServer, BaseHTTPRequestHandler
from dataclasses import dataclass
from pathlib import Path
from pyospray import *
from mss.tools import to_png
import numpy as np
from functools import partial
import logging


print = partial(print, flush=True)


_g_scene = None
WIDTH, HEIGHT = (256, 256)


class TapestryRequestHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		if self.path == '/':
			self.do_GET_index()
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
	
	def do_GET_image(self):
		x, y, z, ux, uy, uz, vx, vy, vz = map(float, self.path[1:].split('/'))
		with committing(_g_scene.camera) as camera:
			camera.pos = (x, y, z)
			camera.up = (ux, uy, uz)
			camera.view = (vx, vy, vz)
		
		_g_scene.renderer.commit()
		
		_g_scene.fb.clear(OSP_FB_COLOR)
		_g_scene.renderer.render(_g_scene.fb, OSP_FB_COLOR)
		data = ospToPixels(b"rgb", _g_scene.size, _g_scene.fb._ospray_object)
		png = to_png(data, (WIDTH, HEIGHT))
		
		self.send_response(200)
		self.send_header('Content-Type', 'image/png')
		self.end_headers()
		self.wfile.write(png)


@dataclass
class Scene:
	camera: Camera
	renderer: Renderer
	light: Light
	size: osp_vec2i
	fb: FrameBuffer
	

def make_scene():
	error = ospInit([]);
	if error != OSP_NO_ERROR:
		raise Exception('Error occurred', err)
		
	with committing(PiecewiseLinear()) as transferFunction:
		colors = np.array([
			0.2, 0.0, 0.0,
			0.8, 0.0, 0.0,
		], dtype='float32')
		with releasing(Data(OSP_FLOAT3, colors, 0)) as data:
			data.commit()
			transferFunction.colors = data
		
		opacities = np.array([
			0.1, 0.9,
		], dtype='float32')
		with releasing(Data(OSP_FLOAT, opacities, 0)) as data:
			data.commit()
			transferFunction.opacities = data
		
		transferFunction.valueRange = (0.0, 255.0)
	
	with committing(StructuredVolume()) as volume:
		voxels = np.fromfile('teapot.raw', dtype='float32').T
		print(voxels.min(), voxels.max(), len(voxels.flat))
		with releasing(Data(OSP_FLOAT, voxels, 0)) as data:
			data.commit()
			volume.voxelData = data

		volume.transferFunction = transferFunction
		volume.voxelRange = (0.0, 255.0)
		volume.dimensions = (256, 256, 178)
		volume.voxelType = b'float'
	
	with committing(OrthographicCamera()) as camera:
		camera.height = HEIGHT
		camera.aspect = WIDTH / HEIGHT
		camera.pos = (0, 0, 0)
		camera.dir = (0.1, 0, 0.1)
		camera.up = (0, 1, 0)

	with committing(Model()) as model:
		model.add(volume)

	with committing(SciVis()) as renderer:
		with committing(AmbientLight(renderer)) as light:
			pass
		
		lights = np.array([
			light,
		], dtype=object)
		with releasing(Data(OSP_LIGHT, lights, 0)) as data:
			data.commit()
			renderer.lights = data
		
		renderer.spp = 4
		renderer.bgColor = 0.5
		renderer.model = model
		renderer.camera = camera
		#renderer.oneSidedLighting = False
	
	size = osp_vec2i()
	size.x = WIDTH
	size.y = HEIGHT
		
	fb = FrameBuffer(size, OSP_FB_RGBA8, OSP_FB_COLOR)
	
	return Scene(
		camera,
		renderer,
		light,
		size,
		fb,
	)


def main(port, verbose):
	if verbose:
		logging.basicConfig(level=logging.DEBUG)
	
	scene = make_scene()
	
	global _g_scene
	_g_scene = scene
	
	server = HTTPServer(('', port), TapestryRequestHandler)
	server.serve_forever()


def cli():
	import argparse
	import os
	
	parser = argparse.ArgumentParser()
	
	parser.add_argument('--port', type=int, default=8819)
	parser.add_argument('-v', '--verbose', action='store_true')
	
	args = vars(parser.parse_args())
	
	main(**args)


if __name__ == '__main__':
	cli()
