#!/usr/bin/env python
"""

"""

from pyospray import *
import numpy as np
from PIL import Image

WIDTH = 1024
HEIGHT = 512

def main():
	error = ospInit([]);
	if error != OSP_NO_ERROR:
		raise Exception('Error occurred', err)
	
	with committing(PanoramicCamera()) as camera:
		camera.aspect = WIDTH / HEIGHT
		camera.pos = (0, 0, 0)
		camera.dir = (0.1, 0, 0.1)
		camera.up = (0, 1, 0)
	
	with committing(TriangleMesh()) as mesh:
		vertex = np.array([
			-1.0, -1.0, 3.0, 0.0,
			-1.0, 1.0, 3.0, 0.0,
			1.0, -1.0, 3.0, 0.0,
			0.1, 0.1, 0.3, 0.0,
		], dtype='float32')
		with releasing(Data(OSP_FLOAT3A, vertex, 0)) as data:
			data.commit()
			mesh.vertex = data
		
		color = np.array([
			0.9, 0.5, 0.5, 1.0,
			0.8, 0.8, 0.8, 1.0,
			0.8, 0.8, 0.8, 1.0,
			0.5, 0.9, 0.5, 1.0,
		], dtype='float32')
		with releasing(Data(OSP_FLOAT4, color, 0)) as data:
			data.commit()
			mesh.vertex__color = data
		
		index = np.array([
			0, 1, 2,
			1, 2, 3,
		], dtype='int32')
		with releasing(Data(OSP_INT3, index, 0)) as data:
			data.commit()
			mesh.index = data
	
	with committing(Model()) as world:
		world.add(mesh)
		mesh.release()

	with committing(SciVis()) as renderer:
		renderer.spp = 4
		renderer.bgColor = 0.5
		renderer.model = world
		renderer.camera = camera
		
		with committing(AmbientLight()) as light:
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
	
	with releasing(FrameBuffer(size, OSP_FB_SRGBA, OSP_FB_COLOR)) as fb:
		fb.clear(OSP_FB_COLOR)
		renderer.render(fb, OSP_FB_COLOR)
		buffer = ospToPixels(b"rgb", size, fb._ospray_object)
		image = Image.frombytes('RGB', (WIDTH, HEIGHT), buffer, 'raw')
		image.save('out.png')

	print('all good')


def cli():
	import argparse
	
	parser = argparse.ArgumentParser()
	args = parser.parse_args()
	
	main(**vars(args))


if __name__ == '__main__':
	cli()
