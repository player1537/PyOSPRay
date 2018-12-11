#!/usr/bin/env python3.7
"""

"""


from http.server import HTTPServer, BaseHTTPRequestHandler
from dataclasses import dataclass
from pathlib import Path
from pyospray import *
from mss.tools import to_png
import numpy as np


_g_scene = None
WIDTH, HEIGHT = (512, 512)


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
		
		with releasing(FrameBuffer(_g_scene.size, OSP_FB_SRGBA, OSP_FB_COLOR)) as fb:
			fb.clear(OSP_FB_COLOR)
			_g_scene.renderer.render(fb, OSP_FB_COLOR)
			data = ospToPixels(b"rgb", _g_scene.size, fb._ospray_object)
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
	

def make_scene():
	error = ospInit([]);
	if error != OSP_NO_ERROR:
		raise Exception('Error occurred', err)
	
	with committing(OrthographicCamera()) as camera:
		camera.height = HEIGHT
		camera.aspect = WIDTH / HEIGHT
		camera.pos = (0, 0, 0)
		camera.dir = (0.1, 0, 0.1)
		camera.up = (0, 1, 0)
	
	with committing(TriangleMesh()) as geometry:
		vertex = np.array([
			-1.0, -1.0, 3.0, 0.0,
			-1.0, 1.0, 3.0, 0.0,
			1.0, -1.0, 3.0, 0.0,
			0.1, 0.1, 0.3, 0.0,
		], dtype='float32')
		with releasing(Data(OSP_FLOAT3A, vertex, 0)) as data:
			data.commit()
			geometry.vertex = data
		
		color = np.array([
			0.9, 0.5, 0.5, 1.0,
			0.8, 0.8, 0.8, 1.0,
			0.8, 0.8, 0.8, 1.0,
			0.5, 0.9, 0.5, 1.0,
		], dtype='float32')
		with releasing(Data(OSP_FLOAT4, color, 0)) as data:
			data.commit()
			geometry.vertex__color = data
		
		index = np.array([
			0, 1, 2,
			1, 2, 3,
		], dtype='int32')
		with releasing(Data(OSP_INT3, index, 0)) as data:
			data.commit()
			geometry.index = data
	
	with committing(Model()) as model:
		with releasing(geometry):
			model.add(geometry)

	with committing(SciVis()) as renderer:
		renderer.spp = 4
		renderer.bgColor = 0.5
		renderer.model = model
		renderer.camera = camera
		renderer.oneSidedLighting = False
		
		with committing(AmbientLight(renderer)) as light:
			pass
		
		lights = np.array([
			light,
		], dtype=object)
		with releasing(Data(OSP_LIGHT, lights, 0)) as lights:
			lights.commit()
			renderer.lights = lights
	
	size = osp_vec2i()
	size.x = WIDTH
	size.y = HEIGHT
	
	return Scene(
		camera,
		renderer,
		light,
		size,
	)


def main(port):
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
	
	args = vars(parser.parse_args())
	
	main(**args)


if __name__ == '__main__':
	cli()
