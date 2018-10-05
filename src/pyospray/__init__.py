"""

"""

from contextlib import contextmanager
from .pyospray import *


@contextmanager
def committing(obj):
	yield obj
	obj.commit()


@contextmanager
def releasing(obj):
	yield obj
	obj.release()


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
	
	def release(self):
		ospRelease(self._ospray_object)


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
		self.name = Committer.normalize_name(name)
	
	@staticmethod
	def normalize_name(name):
		return name.replace('__', '.').encode('ascii')
	
	@staticmethod
	def get_ospray_setter(type):
		def setData(obj, name, value):
			ospSetData(obj, name, value._ospray_object)
		
		def setObject(obj, name, value):
			ospSetObject(obj, name, value._ospray_object)
			
		if type == 'OSPCamera':
			return setObject
		elif type == 'OSPData':
			return setData
		elif type == 'OSPLight[]':
			return setData
		elif type == 'OSPModel':
			return setObject
		elif type == 'OSPTexture2D':
			return setObject
		elif type == 'OSPVolume':
			return setObject
		elif type == 'bool':
			return ospSet1i
		elif type == 'float':
			return ospSet1f
		elif type == 'float / vec3f / vec4f':
			def setter(obj, name, *args):
				func_map = { 1: ospSet1f, 3: ospSet3f, 4: ospSet4f }
				func = func_map[len(args)]
				func(obj, name, *args)
			return setter
		elif type == 'float[]':
			return setData
		elif type == 'int':
			return ospSet1i
		elif type == 'int32[]':
			return setData
		elif type == 'string':
			return None
		elif type == 'vec2f':
			return ospSet2f
		elif type == 'vec2f[]':
			return setData
		elif type == 'vec3f':
			return ospSet3f
		elif type == 'vec3f(a)':
			return ospSet3f
		elif type == 'vec3f(a)[]':
			return setData
		elif type == 'vec3f[]':
			return setData
		elif type == 'vec3fa[] / vec4f[]':
			return setData
		elif type == 'vec3i':
			return None
		elif type == 'vec3i(a)[]':
			return setData
		elif type == 'vec4f[]':
			return setData
		elif type == 'vec4f[] / vec3f(a)[]':
			return setData
		elif type == 'vec4f[] / vec3fa[]':
			return setData
		elif type == 'vec4i[]':
			return setData



class Volume(ManagedObject):
	variant = None
	
	def get_ospray_object(self):
		return ospNewVolume(self.variant)
	
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
	variant = b'shared_structure_volume'
	
	dimensions = Committer('vec3i')
	voxelType = Committer('string')
	gridOrigin = Committer('vec3f')
	gridSpacing = Committer('vec3f')
	voxelData = Committer('OSPData')


class AMRVolume(Volume):
	variant = b'amr_volume'
	
	gridOrigin = Committer('vec3f')
	gridSpacing = Committer('vec3f')
	amrMethod = Committer('string')
	voxelType = Committer('string')
	brickInfo = Committer('OSPData')
	brickData = Committer('OSPData')


class UnstructuredVolume(Volume):
	variant = b'unstructured_volume'
	
	vertices = Committer('vec3f[]')
	field = Committer('float[]')
	intices = Committer('vec4i[]')
	hexMethod = Committer('string')


class TransferFunction(ManagedObject):
	variant = None
	
	def get_ospray_object(self):
		return ospNewTransferFunction(self.variant)


class PiecewiseLinear(TransferFunction):
	variant = b'piecewise_linear'
	
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
	variant = b'triangles'
	
	vertex = Committer('vec3f(a)[]')
	vertex__normal = Committer('vec3f(a)[]')
	vertex__color = Committer('vec4f[] / vec3fa[]')
	vertex__texcoord = Committer('vec2f[]')
	index = Committer('vec3i(a)[]')


class Spheres(Geometry):
	variant = b'spheres'
	
	radius = Committer('float')
	spheres = Committer('OSPData')
	bytes_per_sphere = Committer('int')
	offset_center = Committer('int')
	offset_radius = Committer('int')
	color = Committer('vec4f[] / vec3f(a)[]')
	texcoord = Committer('vec2f[]')


class Cylinders(Geometry):
	variant = b'cylinders'
	
	radius = Committer('float')
	cylinders = Committer('OSPData')
	bytes_per_cylinder = Committer('int')
	offset_v0 = Committer('int')
	offset_v1 = Committer('int')
	offset_radius = Committer('int')
	color = Committer('vec4f[] / vec3f(a)[]')
	texcoord = Committer('OSPData')


class Streamlines(Geometry):
	variant = b'streamlines'
	
	radius = Committer('float')
	smooth = Committer('bool')
	vertex = Committer('vec3fa[] / vec4f[]')
	vertex__color = Committer('vec4f[]')
	vertex__radius = Committer('float[]')
	index = Committer('int32[]')


class Isosurfaces(Geometry):
	variant = b'isosurfaces'
	
	isovalues = Committer('float[]')
	volume = Committer('OSPVolume')


class Slices(Geometry):
	variant = b'slices'
	
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
	variant = b'scivis'
	
	shadowsEnabled = Committer('bool')
	aoSamples = Committer('int')
	aoDistance = Committer('float')
	aoTransparencyEnabled = Committer('bool')
	oneSidedLighting = Committer('bool')
	bgColor = Committer('float / vec3f / vec4f')
	maxDepthTexture = Committer('OSPTexture2D')


class PathTracer(Renderer):
	variant = b'pathtracer'
	
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
	variant = b'distant'
	
	direction = Committer('vec3f(a)')
	angularDiameter = Committer('float')


class PointLight(Light):
	variant = b'sphere'
	
	position = Committer('vec3f(a)')
	radius = Committer('float')


class SpotLight(Light):
	variant = b'spot'
	
	position = Committer('vec3f(a)')
	direction = Committer('vec3f(a)')
	openingAngle = Committer('float')
	penumbraAngle = Committer('float')
	radius = Committer('float')


class QuadLight(Light):
	variant = b'quad'

	position = Committer('vec3f(a)')
	edge1 = Committer('vec3f(a)')
	edge2 = Committer('vec3f(a)')


class HDRILight(Light):
	variant = b'hdri'
	
	up = Committer('vec3f(a)')
	dir = Committer('vec3f(a)')
	map = Committer('OSPTexture2D')


class AmbientLight(Light):
	variant = b'ambient'


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
	variant = b'OBJMaterial'

	Kd = Committer('vec3f')
	Ks = Committer('vec3f')
	Ns = Committer('float')
	d = Committer('float')
	Tf = Committer('vec3f')
	map_Bump = Committer('OSPTexture2D')


class MetalMaterial(Material):
	variant = b'Metal'
	
	ior = Committer('vec3f[]')
	eta = Committer('vec3f')
	k = Committer('vec3f')
	roughness = Committer('float')


class AlloyMaterial(Material):
	variant = b'Alloy'
	
	color = Committer('vec3f')
	edgeColor = Committer('vec3f')
	roughness = Committer('float')


class GlassMaterial(Material):
	variant = b'Glass'
	
	eta = Committer('float')
	attenuationColor = Committer('vec3f')
	attenuationDistance = Committer('float')


class ThinGlassMaterial(Material):
	variant = b'ThinGlass'
	
	eta = Committer('float')
	attenuationColor = Committer('vec3f')
	attenuationDistance = Committer('float')
	thickness = Committer('float')


class MetallicPaintMaterial(Material):
	variant = b'MetallicPaint'
	
	baseColor = Committer('vec3f')
	flakeAmount = Committer('float')
	flakeColor = Committer('vec3f')
	flakeSpread = Committer('float')
	eta = Committer('float')


class LuminousMaterial(Material):
	variant = b'Luminous'


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
	variant = b'perspective'
	
	fovy = Committer('float')
	aspect = Committer('float')
	apertureRadius = Committer('float')
	focusDistance = Committer('float')
	architectural = Committer('bool')
	stereoMode = Committer('int')
	interpupillaryDistance = Committer('float')


class OrthographicCamera(Camera):
	variant = b'orthographic'
	
	height = Committer('float')
	aspect = Committer('float')


class PanoramicCamera(Camera):
	variant = b'panoramic'


class FrameBuffer(ManagedObject):
	def __init__(self, size, format, channels):
		self._size = size
		self._format = format
		self._channels = channels
	
	def get_ospray_object(self):
		return ospNewFrameBuffer(self._size, self._format, self._channels)
	
	def writePPM(self, filename):
		ospWritePPM(filename, self._size, self._ospray_object)
	
	def clear(self, channels):
		ospFrameBufferClear(self._ospray_object, channels)
	
	# TODO: Add map, unmap, and pixel op


class PixelOp(ManagedObject):
	variant = None
	
	def get_ospray_object(self):
		return ospNewPixelOp(self.variant)


class ToneMapper(PixelOp):
	variant = b'tonemapper'
	
	contrast = Committer('float')
	shoulder = Committer('float')
	midIn = Committer('float')
	midOut = Committer('float')
	hdrMax = Committer('float')


class Data(ManagedObject):
	def __init__(self, type, data, flags):
		self._type = type
		if any(hasattr(d, '_ospray_object') for d in data):
			data = [x._ospray_object for x in data]
		self._data = data
		self._flags = flags
	
	def get_ospray_object(self):
		return ospNewData((self._type, self._data, self._flags))
