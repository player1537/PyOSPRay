#!/usr/bin/env python
"""

"""

from pyospray import *

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
		vertex = [
			-1.0, -1.0, 3.0, 0.0,
			-1.0, 1.0, 3.0, 0.0,
			1.0, -1.0, 3.0, 0.0,
			0.1, 0.1, 0.3, 0.0,
		]
		with releasing(Data(OSP_FLOAT3A, vertex, 0)) as data:
			data.commit()
			mesh.vertex = data
		
		color = [
			0.9, 0.5, 0.5, 1.0,
			0.8, 0.8, 0.8, 1.0,
			0.8, 0.8, 0.8, 1.0,
			0.5, 0.9, 0.5, 1.0,
		]
		with releasing(Data(OSP_FLOAT4, color, 0)) as data:
			data.commit()
			mesh.vertex__color = data
		
		index = [
			0, 1, 2,
			1, 2, 3,
		]
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
		
		with committing(AmbientLight(renderer)) as light:
			pass
		
		with releasing(Data(OSP_LIGHT, [light], 0)) as lights:
			lights.commit()
			renderer.lights = lights
	
	size = osp_vec2i()
	size.x = WIDTH
	size.y = HEIGHT
	
	with releasing(FrameBuffer(size, OSP_FB_SRGBA, OSP_FB_COLOR)) as fb:
		fb.clear(OSP_FB_COLOR)
		renderer.render(fb, OSP_FB_COLOR)
		buffer = ospByteBuffer(WIDTH * HEIGHT * 3)
		ospToPixels(b"rgb", size, fb._ospray_object, buffer)
		print(f'[0] = {buffer[0]}')
		print(f'[1] = {buffer[1]}')
		print(f'[2] = {buffer[2]}')

	print('all good')


def cli():
	import argparse
	
	parser = argparse.ArgumentParser()
	args = parser.parse_args()
	
	main(**vars(args))


if __name__ == '__main__':
	cli()
