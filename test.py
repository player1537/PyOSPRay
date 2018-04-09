#!/usr/bin/env python
"""

"""

from ospray import *
from contextlib import contextmanager


@contextmanager
def committing(obj):
	yield obj
	obj.commit()


# Thanks https://stackoverflow.com/a/6849299
class lazy_property(object):
    '''
    meant to be used for lazy evaluation of an object attribute.
    property should represent non-mutable data, as it replaces itself.
    '''

    def __init__(self, fget):
        self.fget = fget
        self.func_name = fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return None
        value = self.fget(obj)
        setattr(obj, self.func_name, value)
        return value


class ManagedObjectMeta(type):
	pass


class ManagedObject(metaclass=ManagedObjectMeta):
	@lazy_property
	def _ospray_object(self):
		return self.get_ospray_object()

	def commit(self):
		ospCommit(self._ospray_object)
	
	def get_ospray_object(self, *args, **kwargs):
		return self.ospray_class(*args, **kwargs)


class Committer(object):
	def __init__(self, type):
		self.setter = Committer.get_ospray_setter(type)
		self.name = None

	def __get__(self, obj, objtype=None):
		raise NotImplementedError()
	
	def __set__(self, obj, value):
		ospray_object = obj._ospray_object
		if isinstance(value, tuple):
			args = value
		else:
			args = (value,)
		self.setter(ospray_object, self.name, *args)
	
	def __set_name__(self, owner, name):
		self.name = name
	
	@staticmethod
	def get_ospray_setter(type):
		if type == 'OSPCamera':
			return None
		elif type == 'OSPData':
			return None
		elif type == 'OSPLight[]':
			return None
		elif type == 'OSPModel':
			return None
		elif type == 'OSPTexture2D':
			return None
		elif type == 'OSPVolume':
			return None
		elif type == 'bool':
			return None
		elif type == 'float':
			return ospSet1f
		elif type == 'float / vec3f / vec4f':
			return None
		elif type == 'float[]':
			return None
		elif type == 'int':
			return None
		elif type == 'int32[]':
			return None
		elif type == 'string':
			return None
		elif type == 'vec2f':
			return ospSet2f
		elif type == 'vec2f[]':
			return None
		elif type == 'vec3f':
			return None
		elif type == 'vec3f(a)':
			return ospSet3f
		elif type == 'vec3f(a)[]':
			return None
		elif type == 'vec3f[]':
			return None
		elif type == 'vec3fa[] / vec4f[]':
			return None
		elif type == 'vec3i':
			return None
		elif type == 'vec3i(a)[]':
			return None
		elif type == 'vec4f[]':
			return None
		elif type == 'vec4f[] / vec3f(a)[]':
			return None
		elif type == 'vec4f[] / vec3fa[]':
			return None
		elif type == 'vec4i[]':
			return None



class Volume(ManagedObject):
	volume_type = None
	
	def get_ospray_object(self):
		return ospNewVolume(self.volume_type)
	
	voxelRange = Committer('vec2f')
	gradientShadingEnabled = Committer('bool')
	preIntegration = Committer('bool')
	singleShade = Committer('bool')
	adaptiveSampling = Committer('bool')
	adaptiveScalar = Committer('float')
	adaptiveMaxSamplingRate = Committer('float')
	samplingRate = Committer('float')
	specular = Committer('vec3f')
	volumeClippingBoxLower = Committer('vec3f')
	volumeClippingBoxUpper = Committer('vec3f')


class StructuredVolume(Volume):
	volume_type = 'shared_structure_volume'
	
	dimensions = Committer('vec3i')
	voxelType = Committer('string')
	gridOrigin = Committer('vec3f')
	gridSpacing = Committer('vec3f')


class AMRVolume(Volume):
	volume_type = 'amr_volume'
	
	gridOrigin = Committer('vec3f')
	gridSpacing = Committer('vec3f')
	amrMethod = Committer('string')
	voxelType = Committer('string')
	brickInfo = Committer('OSPData')
	brickData = Committer('OSPData')


class UnstructuredVolume(Volume):
	volume_type = 'unstructured_volume'
	
	vertices = Committer('vec3f[]')
	field = Committer('float[]')
	intices = Committer('vec4i[]')
	hexMethod = Committer('string')


class TransferFunction(ManagedObject):
	variant = None
	
	def get_ospray_object(self):
		return ospNewTransferFunction(self.variant)


class PiecewiseLinear(TransferFunction):
	variant = 'piecewise_linear'
	
	colors = Committer('vec3f[]')
	opacities = Committer('float[]')
	valueRange = Committer('vec2f')


class Geometry(ManagedObject):
	variant = None
	
	def get_ospray_object(self):
		return ospNewGeometry(self.variant)
	
	def add(self, material):
		ospSetMaterial(self._ospray_object, material._ospray_object)
	

class TriangleMesh(Geometry):
	variant = 'triangles'
	
	vertex = Committer('vec3f(a)[]')
	vertex__normal = Committer('vec3f(a)[]')
	vertex__color = Committer('vec4f[] / vec3fa[]')
	vertex__texcoord = Committer('vec2f[]')
	index = Committer('vec3i(a)[]')


class Spheres(Geometry):
	variant = 'spheres'
	
	radius = Committer('float')
	spheres = Committer('OSPData')
	bytes_per_sphere = Committer('int')
	offset_center = Committer('int')
	offset_radius = Committer('int')
	color = Committer('vec4f[] / vec3f(a)[]')
	texcoord = Committer('vec2f[]')


class Cylinders(Geometry):
	variant = 'cylinders'
	
	radius = Committer('float')
	cylinders = Committer('OSPData')
	bytes_per_cylinder = Committer('int')
	offset_v0 = Committer('int')
	offset_v1 = Committer('int')
	offset_radius = Committer('int')
	color = Committer('vec4f[] / vec3f(a)[]')
	texcoord = Committer('OSPData')


class Streamlines(Geometry):
	variant = 'streamlines'
	
	radius = Committer('float')
	smooth = Committer('bool')
	vertex = Committer('vec3fa[] / vec4f[]')
	vertex__color = Committer('vec4f[]')
	vertex__radius = Committer('float[]')
	index = Committer('int32[]')


class Isosurfaces(Geometry):
	variant = 'isosurfaces'
	
	isovalues = Committer('float[]')
	volume = Committer('OSPVolume')


class Slices(Geometry):
	variant = 'slices'
	
	planes = Committer('vec4f[]')
	volume = Committer('OSPVolume')


class Instance(Geometry):
	def __init__(self, model, transform):
		self._model = model
		self._transform = transform
	
	def get_ospray_object(self):
		return ospNewInstance(self._model, self._transform)


class Renderer(ManagedObject):
	variant = None
	
	def get_ospray_object(self):
		return ospNewRenderer(self.variant)
	
	model = Committer('OSPModel')
	camera = Committer('OSPCamera')
	lights = Committer('OSPLight[]')
	epsilon = Committer('float')
	spp = Committer('int')
	maxDepth = Committer('int')
	minContribution = Committer('float')
	varianceThreshold = Committer('float')
	
	def render(self, framebuffer, channels):
		variance = ospRenderFrame(framebuffer._ospray_object, self._ospray_object, channels)
		return variance


class SciVis(Renderer):
	variant = 'scivis'
	
	shadowsEnabled = Committer('bool')
	aoSamples = Committer('int')
	aoDistance = Committer('float')
	aoTransparencyEnabled = Committer('bool')
	oneSidedLighting = Committer('bool')
	bgColor = Committer('float / vec3f / vec4f')
	maxDepthTexture = Committer('OSPTexture2D')


class PathTracer(Renderer):
	variant = 'pathtracer'
	
	rouletteDepth = Committer('int')
	maxContribution = Committer('float')
	backplate = Committer('OSPTexture2D')


class Model(ManagedObject):
	def get_ospray_object(self):
		return ospNewModel()
	
	def add(self, obj):
		if isinstance(obj, Geometry):
			ospAddGeometry(self._ospray_object, obj._ospray_object)
		elif isinstance(obj, Volume):
			ospAddVolume(self._ospray_object, obj._ospray_object)

	def remove(self, obj):
		if isinstance(obj, Geometry):
			ospRemoveGeometry(self._ospray_object, obj._ospray_object)
		elif isinstance(obj, Volume):
			ospRemoveVolume(self._ospray_object, obj._ospray_object)
	

class Light(ManagedObject):
	variant = None

	def __init__(self, renderer):
		if isinstance(renderer, Renderer):
			renderer = renderer.variant
		
		self._renderer = renderer
	
	def get_ospray_object(self):
		return ospNewLight2(self._renderer, self.variant)
	
	color = Committer('vec3f(a)')
	intensity = Committer('float')
	isVisible = Committer('bool')


class DirectionalLight(Light):
	variant = 'distant'
	
	direction = Committer('vec3f(a)')
	angularDiameter = Committer('float')


class PointLight(Light):
	variant = 'sphere'
	
	position = Committer('vec3f(a)')
	radius = Committer('float')


class SpotLight(Light):
	variant = 'spot'
	
	position = Committer('vec3f(a)')
	direction = Committer('vec3f(a)')
	openingAngle = Committer('float')
	penumbraAngle = Committer('float')
	radius = Committer('float')


class QuadLight(Light):
	variant = 'quad'

	position = Committer('vec3f(a)')
	edge1 = Committer('vec3f(a)')
	edge2 = Committer('vec3f(a)')


class HDRILight(Light):
	variant = 'hdri'
	
	up = Committer('vec3f(a)')
	dir = Committer('vec3f(a)')
	map = Committer('OSPTexture2D')


class AmbientLight(Light):
	variant = 'ambient'


class Material(ManagedObject):
	variant = None
	
	def __init__(self, renderer):
		if isinstance(renderer, Renderer):
			renderer = renderer.variant
		
		self._renderer = renderer
	
	def get_ospray_object(self):
		return ospNewMaterial2(self._renderer, self.variant)
	
	
	# TODO: Include texture transformations


class OBJMaterial(Material):
	variant = 'OBJMaterial'

	Kd = Committer('vec3f')
	Ks = Committer('vec3f')
	Ns = Committer('float')
	d = Committer('float')
	Tf = Committer('vec3f')
	map_Bump = Committer('OSPTexture2D')


class MetalMaterial(Material):
	variant = 'Metal'
	
	ior = Committer('vec3f[]')
	eta = Committer('vec3f')
	k = Committer('vec3f')
	roughness = Committer('float')


class AlloyMaterial(Material):
	variant = 'Alloy'
	
	color = Committer('vec3f')
	edgeColor = Committer('vec3f')
	roughness = Committer('float')


class GlassMaterial(Material):
	variant = 'Glass'
	
	eta = Committer('float')
	attenuationColor = Committer('vec3f')
	attenuationDistance = Committer('float')


class ThinGlassMaterial(Material):
	variant = 'ThinGlass'
	
	eta = Committer('float')
	attenuationColor = Committer('vec3f')
	attenuationDistance = Committer('float')
	thickness = Committer('float')


class MetallicPaintMaterial(Material):
	variant = 'MetallicPaint'
	
	baseColor = Committer('vec3f')
	flakeAmount = Committer('float')
	flakeColor = Committer('vec3f')
	flakeSpread = Committer('float')
	eta = Committer('float')


class LuminousMaterial(Material):
	variant = 'Luminous'


class Texture(ManagedObject):
	def __init__(self, size, format, source, flags):
		self._size = size
		self._format = format
		self._source = source
		self._flags = flags
		
	def get_ospray_object(self):
		return ospNewTexture2D(self._size, self._format, self._source, self._flags)


class Camera(ManagedObject):
	variant = None
	
	def get_ospray_object(self):
		return ospNewCamera(self.variant)
	
	pos = Committer('vec3f(a)')
	dir = Committer('vec3f(a)')
	up = Committer('vec3f(a)')
	nearClip = Committer('float')
	imageStart = Committer('vec2f')
	imageEnd = Committer('vec2f')
	
	def pick(self, renderer, screenPos):
		# TODO: Fix ospPick in SWIG configuration
		raise NotImplementedError


class PerspectiveCamera(Camera):
	variant = 'perspective'
	
	fovy = Committer('float')
	aspect = Committer('float')
	apertureRadius = Committer('float')
	focusDistance = Committer('float')
	architectural = Committer('bool')
	stereoMode = Committer('int')
	interpupillaryDistance = Committer('float')


class OrthographicCamera(Camera):
	variant = 'orthographic'
	
	height = Committer('float')
	aspect = Committer('float')


class PanoramicCamera(Camera):
	variant = 'panoramic'


class FrameBuffer(ManagedObject):
	def __init__(self, size, format, channels):
		self._size = size
		self._format = format
		self._channels = channels
	
	def get_ospray_object(self):
		return ospNewFrameBuffer(self._size, self._format, self._channels)
	
	# TODO: Add map, unmap, and pixel op


class PixelOp(ManagedObject):
	variant = None
	
	def get_ospray_object(self):
		return ospNewPixelOp(self.variant)


class ToneMapper(PixelOp):
	variant = 'tonemapper'
	
	contrast = Committer('float')
	shoulder = Committer('float')
	midIn = Committer('float')
	midOut = Committer('float')
	hdrMax = Committer('float')


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
	
	camera = PanoramicCamera()
	camera.aspect = WIDTH / HEIGHT
	camera.pos = (0, 0, 0)
	camera.dir = (0.1, 0, 0.1)
	camera.up = (0, 1, 0)
	camera.commit()
	
	mesh = ospNewGeometry("triangles")
	data = ospNewData(OSP_FLOAT3A, [
		-1.0, -1.0, 3.0, 0.0,
		-1.0, 1.0, 3.0, 0.0,
		1.0, -1.0, 3.0, 0.0,
		0.1, 0.1, 0.3, 0.0,
	], 0)
	ospCommit(data)
	ospSetData(mesh, "vertex", data)
	ospRelease(data)
	
	data = ospNewData(OSP_FLOAT4, [
		0.9, 0.5, 0.5, 1.0,
		0.8, 0.8, 0.8, 1.0,
		0.8, 0.8, 0.8, 1.0,
		0.5, 0.9, 0.5, 1.0,
	], 0)
	ospCommit(data)
	ospSetData(mesh, "vertex.color", data)
	ospRelease(data)
	
	data = ospNewData(OSP_INT3, [
		0, 1, 2,
		1, 2, 3,
	], 0)
	ospCommit(data)
	ospSetData(mesh, "index", data)
	ospRelease(data)
	
	ospCommit(mesh)
	
	world = ospNewModel()
	ospAddGeometry(world, mesh)
	ospRelease(mesh)
	ospCommit(world)
	
	renderer = ospNewRenderer("scivis")
	
	light = ospNewLight2("scivis", "ambient")
	ospCommit(light)
	lights = ospNewData(OSP_LIGHT, [
		light,
	], 0)
	ospCommit(lights)

	ospSet1i(renderer, "spp", 4)
	ospSet1f(renderer, "bgColor", 1.0)
	ospSetObject(renderer, "model", world)
	ospSetObject(renderer, "camera", camera._ospray_object)
	ospSetObject(renderer, "lights", lights)
	ospCommit(renderer)
	
	size = osp_vec2i()
	size.x = WIDTH
	size.y = HEIGHT
	
	framebuffer = ospNewFrameBuffer(size, OSP_FB_SRGBA, OSP_FB_COLOR | OSP_FB_ACCUM)
	ospFrameBufferClear(framebuffer, OSP_FB_COLOR | OSP_FB_ACCUM)
	
	ospCommit(world)
	ospRenderFrame(framebuffer, renderer, OSP_FB_COLOR | OSP_FB_ACCUM)
	
	ospWritePPM('out.ppm', size, framebuffer)
	
	print('all good')


def cli():
	import argparse
	
	parser = argparse.ArgumentParser()
	args = parser.parse_args()
	
	main(**vars(args))


if __name__ == '__main__':
	cli()
