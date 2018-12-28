"""
Python wrapper around the OSPRay rendering library

The main utility of this project is around creating and using the
objects that OSPRay works with. This includes setting up Renderers,
Models, Geometries, and Materials.

Instead of the functional structure that OSPRay uses, this project uses
a more Pythonic object-oriented interface. In essence, this means using
`obj.attr = value` instead of `set(obj, 'attr', value)`.

For more information on OSPRay and its capabilities, go to `its
website`__.

__ https://www.ospray.org/documentation.html

"""

from contextlib import contextmanager
from .pyospray import *
from .builtin import *
import logging


_logger = None

def get_logger():
	global _logger
	if _logger is None:
		_logger = logging.getLogger(__name__)
	return _logger


@contextmanager
def committing(obj):
	"""Commit the object after the context manager block."""
	yield obj
	obj.commit()


@contextmanager
def releasing(obj):
	"""Release the object after the context manager block."""
	yield obj
	obj.release()


# Thanks https://stackoverflow.com/a/6849299
class lazy_property(object):
	"""
	meant to be used for lazy evaluation of an object attribute.
	property should represent non-mutable data, as it replaces itself.
	"""

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
	"""Metaclass reserved for future use."""
	pass


class ManagedObject(metaclass=ManagedObjectMeta):
	"""Base class for all OSPRay objects
	
	Subclasses should override or extend the
	:meth:`~.ManagedObject._make_ospray_object` method and return
	an appropriate OSPRay object (e.g. `ospNewGeometry(...)`).

	Any attributes that can be set (e.g. with `ospSet3f(...)` or
	similar methods) can use the :class:`~.Committer` descriptor
	in their class definition to automatically have getters/setters
	with the appropriate types.
	
	"""
	
	@lazy_property
	def _logger(self):
		"""Return the appropriate logger."""
		return get_logger()
	
	@lazy_property
	def _ospray_object(self):
		"""Return the OSPRay object instance."""
		self._logger.debug('new %s', self.__class__.__name__)
		obj = self._make_ospray_object()
		assert obj is not None
		return obj
	
	def _make_ospray_object(self, *args, **kwargs):
		"""Make the low-level OSPRay object and return it."""
		raise NotImplementedError

	def commit(self):
		"""Commit any changes to OSPRay."""
		self._logger.debug('ospCommit(%s)', self.__class__.__name__)
		ospCommit(self._ospray_object)
	
	def release(self):
		self._logger.debug('ospRelease(%s)', self.__class__.__name__)
		ospRelease(self._ospray_object)


class Committer(object):
	"""Automatical type-correct setters for managed objects.
	
	Intended to be used like this::
	
	  class Foo(ManagedObject):
	      myattr = Committer('vec2f')
	  
	  foo = Foo()
	  foo.myattr = (1.0, 2.0)
	
	Which will function like the low level OSPRay code::
	
	  foo = ospNewFoo()
	  setVec2f(foo, 'myattr', 1.0, 2.0)
	
	Note: In the future, this may also set a dirty flag on the object
	so that commits aren't missed.
	
	"""
	
	@lazy_property
	def _logger(self):
		"""Return the module logger."""
		return get_logger()
		
	def __init__(self, type):
		"""Create the committer with the right type.
		
		`type` should be a string that matches one of the data
		types in the :meth:`~.Committer.get_ospray_setter`
		method, which should also match the types used in the
		official documentation.
		
		"""
		self.setter = Committer.get_ospray_setter(type)
		self.name = None

	def __get__(self, obj, objtype=None):
		"""Return the attributes value.
		
		Note: Not currently implemented, but it may be in
		the future.
		
		"""
		raise NotImplementedError()
	
	def __set__(self, obj, value):
		"""Call the low-level OSPRay method to set the attribute."""
		ospray_object = obj._ospray_object
		if isinstance(value, tuple):
			args = value
		else:
			args = (value,)
		self._logger.debug('set %s.%s = %r using %s', obj.__class__.__name__, self.name, args, self.setter.__name__)
		self.setter(ospray_object, self.name, *args)
	
	def __set_name__(self, owner, name):
		"""Remember the name of the attribute.
		
		This is part of the descriptor specification and saves
		us from repeating the name of each attribute.

		Note: The name is normalized according to
		:meth:`~.Committer.normalize_name` to get Pythonic names
		instead of the ones from OSPRay.

		"""
		self.name = Committer.normalize_name(name)
	
	@staticmethod
	def normalize_name(name):
		"""Map Pythonic attribute names to OSPRay names."""
		return name.replace('__', '.').encode('ascii')
	
	@staticmethod
	def get_ospray_setter(type):
		"""Return the appropriate low-level setter function."""
		
		# Note: this function is written intentionally verbosely
		# to make it easier to add special cases when needed
		# (e.g. with float / vec3f / vec4f).
		
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
		elif type == 'OSPTransferFunction':
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
			return ospSetString
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
			return ospSet3i
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
		elif type == 'int32[]':
			return setData
		else:
			raise NotImplementedError


class Volume(ManagedObject):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#volumes
	
	"""
	
	variant = None

	def _make_ospray_object(self):
		return ospNewVolume(self.variant)

	transferFunction = Committer('OSPTransferFunction')
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
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#structured-volume
	
	"""
	
	variant = b'shared_structured_volume'
	
	dimensions = Committer('vec3i')
	voxelType = Committer('string')
	gridOrigin = Committer('vec3f')
	gridSpacing = Committer('vec3f')
	voxelData = Committer('OSPData')


class AMRVolume(Volume):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#adaptive-mesh-refinement-amr-volume
	
	"""
	variant = b'amr_volume'
	
	gridOrigin = Committer('vec3f')
	gridSpacing = Committer('vec3f')
	amrMethod = Committer('string')
	voxelType = Committer('string')
	brickInfo = Committer('OSPData')
	brickData = Committer('OSPData')


class UnstructuredVolume(Volume):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#unstructured-volumes
	
	"""
	
	variant = b'unstructured_volume'
	
	vertices = Committer('vec3f[]')
	field = Committer('float[]')
	intices = Committer('vec4i[]')
	hexMethod = Committer('string')


class TransferFunction(ManagedObject):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#transfer-function
	
	"""
	
	variant = None
	
	def _make_ospray_object(self):
		return ospNewTransferFunction(self.variant)


class PiecewiseLinear(TransferFunction):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#transfer-function
	
	"""
	
	variant = b'piecewise_linear'
	
	colors = Committer('vec3f[]')
	opacities = Committer('float[]')
	valueRange = Committer('vec2f')


class Geometry(ManagedObject):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#geometries
	
	"""
	
	variant = None
	
	def _make_ospray_object(self):
		return ospNewGeometry(self.variant)
	
	def add(self, material):
		ospSetMaterial(self._ospray_object, material._ospray_object)
	

class TriangleMesh(Geometry):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#triangle-mesh
	
	"""
	
	variant = b'triangles'
	
	vertex = Committer('vec3f(a)[]')
	vertex__normal = Committer('vec3f(a)[]')
	vertex__color = Committer('vec4f[] / vec3fa[]')
	vertex__texcoord = Committer('vec2f[]')
	index = Committer('vec3i(a)[]')


class QuadMesh(Geometry):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#quad-mesh
	
	"""
	
	variant = b'quads'
	
	vertex = Committer('vec3f(a)[]')
	vertex__normal = Committer('vec3f(a)[]')
	vertex__color = Committer('vec4f[] / vec3fa[]')
	vertex__texcoord = Committer('vec2f[]')
	index = Committer('vec4i[]')


class Spheres(Geometry):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#spheres
	
	"""
	
	variant = b'spheres'
	
	radius = Committer('float')
	spheres = Committer('OSPData')
	bytes_per_sphere = Committer('int')
	offset_center = Committer('int')
	offset_radius = Committer('int')
	color = Committer('vec4f[] / vec3f(a)[]')
	texcoord = Committer('vec2f[]')


class Cylinders(Geometry):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#cylinders
	
	"""
	
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
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#streamlines
	
	"""
	
	variant = b'streamlines'
	
	radius = Committer('float')
	smooth = Committer('bool')
	vertex = Committer('vec3fa[] / vec4f[]')
	vertex__color = Committer('vec4f[]')
	vertex__radius = Committer('float[]')
	index = Committer('int32[]')


class Curves(Geometry):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#curves
	
	"""
	
	variant = b'curves'
	
	curveType = Committer('string')
	curveBasis = Committer('string')
	vertex = Committer('vec4f[]')
	index = Committer('int32[]')
	vertex__normal = Committer('vec3f[]')
	vertex__tangent = Committer('vec3f[]')


class Isosurfaces(Geometry):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#isosurfaces
	
	"""
	
	variant = b'isosurfaces'
	
	isovalues = Committer('float[]')
	volume = Committer('OSPVolume')


class Slice(Geometry):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#slices
	
	"""
	
	variant = b'slices'
	
	planes = Committer('vec4f[]')
	volume = Committer('OSPVolume')


class Instance(Geometry):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#instances
	
	"""
	
	def __init__(self, model, transform):
		self._model = model
		self._transform = transform
	
	def _make_ospray_object(self):
		return ospNewInstance(self._model, self._transform)


class Renderer(ManagedObject):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#renderer
	
	"""
	
	variant = None
	
	def _make_ospray_object(self):
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
		"""Render to the given framebuffer and return variance."""
		variance = ospRenderFrame(framebuffer._ospray_object, self._ospray_object, channels)
		return variance
	
	# TODO: Add ospPick support


class SciVis(Renderer):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#scivis-renderer
	
	"""
	
	variant = b'scivis'
	
	shadowsEnabled = Committer('bool')
	aoSamples = Committer('int')
	aoDistance = Committer('float')
	aoTransparencyEnabled = Committer('bool')
	oneSidedLighting = Committer('bool')
	bgColor = Committer('float / vec3f / vec4f')
	maxDepthTexture = Committer('OSPTexture2D')


class PathTracer(Renderer):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#path-tracer
	
	"""
	
	variant = b'pathtracer'
	
	rouletteDepth = Committer('int')
	maxContribution = Committer('float')
	backplate = Committer('OSPTexture2D')


class Model(ManagedObject):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#model
	
	"""
	
	def _make_ospray_object(self):
		return ospNewModel()
	
	def add(self, obj):
		"""Add an object to the model.
		
		This is either a :class:`~.Geometry` or a
		:class:`~.Volume`.
		
		"""
		if isinstance(obj, Geometry):
			ospAddGeometry(self._ospray_object, obj._ospray_object)
		elif isinstance(obj, Volume):
			ospAddVolume(self._ospray_object, obj._ospray_object)

	def remove(self, obj):
		"""Remove an object from the model.
		
		This is either a :class:`~.Geometry` or a
		:class:`~.Volume`.
		
		"""
		if isinstance(obj, Geometry):
			ospRemoveGeometry(self._ospray_object, obj._ospray_object)
		elif isinstance(obj, Volume):
			ospRemoveVolume(self._ospray_object, obj._ospray_object)
	

class Light(ManagedObject):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#lights
	
	"""
	
	variant = None

	def __init__(self, renderer=None):
		if renderer is not None:
			raise ValueError("renderer parameter no longer needed")
	def _make_ospray_object(self):
		return ospNewLight3(self.variant)
	
	color = Committer('vec3f(a)')
	intensity = Committer('float')
	isVisible = Committer('bool')


class DirectionalLight(Light):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#directional-light-distant-light
	
	"""
	
	variant = b'distant'
	
	direction = Committer('vec3f(a)')
	angularDiameter = Committer('float')


class PointLight(Light):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#point-light-sphere-light
	
	"""
	
	variant = b'sphere'
	
	position = Committer('vec3f(a)')
	radius = Committer('float')


class SpotLight(Light):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#spot-light
	
	"""
	
	variant = b'spot'
	
	position = Committer('vec3f(a)')
	direction = Committer('vec3f(a)')
	openingAngle = Committer('float')
	penumbraAngle = Committer('float')
	radius = Committer('float')


class QuadLight(Light):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#quad-light
	
	"""
	
	variant = b'quad'

	position = Committer('vec3f(a)')
	edge1 = Committer('vec3f(a)')
	edge2 = Committer('vec3f(a)')


class HDRILight(Light):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#hdri-light
	
	"""
	
	variant = b'hdri'
	
	up = Committer('vec3f(a)')
	dir = Committer('vec3f(a)')
	map = Committer('OSPTexture2D')


class AmbientLight(Light):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#ambient-light
	
	"""
	
	variant = b'ambient'


class Material(ManagedObject):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#materials
	
	"""
	
	variant = None
	
	def __init__(self, renderer):
		if isinstance(renderer, Renderer):
			renderer = renderer.variant
		
		self._renderer = renderer
	
	def _make_ospray_object(self):
		return ospNewMaterial2(self._renderer, self.variant)
	
	# TODO: Include texture transformations


class OBJMaterial(Material):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#obj-material
	
	"""
	
	variant = b'OBJMaterial'

	Kd = Committer('vec3f')
	Ks = Committer('vec3f')
	Ns = Committer('float')
	d = Committer('float')
	Tf = Committer('vec3f')
	map_Bump = Committer('OSPTexture2D')


class PrincipledMaterial(Material):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#principled
	
	"""
	
	variant = b'Principled'
	
	baseColor = Committer('vec3f')
	edgeColor = Committer('vec3f')
	metallic = Committer('float')
	diffuse = Committer('float')
	specular = Committer('float')
	ior = Committer('float')
	transmission = Committer('float')
	transmissionColor = Committer('vec3f')
	transmissionDepth = Committer('float')
	roughness = Committer('float')
	anisotropy = Committer('float')
	rotation = Committer('float')
	normal = Committer('float')
	baseNormal = Committer('float')
	thin = Committer('bool')
	thickness = Committer('float')
	backlight = Committer('float')
	coat = Committer('float')
	coatIor = Committer('float')
	coatColor = Committer('vec3f')
	coatThickness = Committer('float')
	coatRoughness = Committer('float')
	coatNormal = Committer('float')
	sheen = Committer('float')
	sheenColor = Committer('vec3f')
	sheenTint = Committer('float')
	sheenRoughness = Committer('float')
	opacity = Committer('float')


class CarPaintMaterial(Material):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#carpaint
	
	"""
	
	variant = b'CarPaint'
	
	baseColor = Committer('vec3f')
	roughness = Committer('float')
	normal = Committer('float')
	flakeDensity = Committer('float')
	flakeScale = Committer('float')
	flakeSpread = Committer('float')
	flakeJitter = Committer('float')
	flakeRoughness = Committer('float')
	coat = Committer('float')
	coatIor = Committer('float')
	coatColor = Committer('vec3f')
	coatThickness = Committer('float')
	coatRoughness = Committer('float')
	coatNormal = Committer('float')
	flipflopColor = Committer('vec3f')
	flipflopFalloff = Committer('float')


class MetalMaterial(Material):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#metal
	
	"""
	
	variant = b'Metal'
	
	ior = Committer('vec3f[]')
	eta = Committer('vec3f')
	k = Committer('vec3f')
	roughness = Committer('float')


class AlloyMaterial(Material):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#alloy
	
	"""
	
	variant = b'Alloy'
	
	color = Committer('vec3f')
	edgeColor = Committer('vec3f')
	roughness = Committer('float')


class GlassMaterial(Material):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#glass
	
	"""
	
	variant = b'Glass'
	
	eta = Committer('float')
	attenuationColor = Committer('vec3f')
	attenuationDistance = Committer('float')


class ThinGlassMaterial(Material):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#thinglass
	
	"""
	
	variant = b'ThinGlass'
	
	eta = Committer('float')
	attenuationColor = Committer('vec3f')
	attenuationDistance = Committer('float')
	thickness = Committer('float')


class MetallicPaintMaterial(Material):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#metallicpaint
	
	"""
	
	variant = b'MetallicPaint'
	
	baseColor = Committer('vec3f')
	flakeAmount = Committer('float')
	flakeColor = Committer('vec3f')
	flakeSpread = Committer('float')
	eta = Committer('float')


class LuminousMaterial(Material):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#luminous
	
	"""
	
	variant = b'Luminous'


class Texture(ManagedObject):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#texture
	
	"""
	
	variant = None
	
	def __init__(self, size=None, format=None, source=None, flags=None):
		if any(x is None for x in (size, format, source, flags)):
			warn('Texture should not be used directly. See Texture2D', DeprecationWarning, stacklevel=2)
			self.variant = Texture2D.variant
			self.size = size
			self.format = format
			self.flags = flags
			self.data = data
		
	def _make_ospray_object(self):
		return ospNewTexture(self.variant)
	
class Texture2D(Texture):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#texture2d
	
	"""
	
	variant = b'texture2D'
	
	size = Committer('vec2f')
	type = Committer('int')
	flags = Committer('int')
	data = Committer('OSPData')
	
	RGBA8 = OSP_TEXTURE_RGBA8
	SRGBA = OSP_TEXTURE_SRGBA
	RGBA32F = OSP_TEXTURE_RGBA32F
	RGB8 = OSP_TEXTURE_RGB8
	SRGB = OSP_TEXTURE_SRGB
	RGB32F = OSP_TEXTURE_RGB32F
	R8 = OSP_TEXTURE_R8
	R32F = OSP_TEXTURE_R32F
	
	NONE = 0
	NEAREST = OSP_TEXTURE_FILTER_NEAREST


class TextureVolume(Texture):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#texturevolume
	
	"""
	
	variant = b'volume'
	
	volume = Committer('OSPVolume')


class Camera(ManagedObject):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#cameras
	
	"""
	
	variant = None
	
	def _make_ospray_object(self):
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
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#perspective-camera
	
	"""
	
	variant = b'perspective'
	
	fovy = Committer('float')
	aspect = Committer('float')
	apertureRadius = Committer('float')
	focusDistance = Committer('float')
	architectural = Committer('bool')
	stereoMode = Committer('int')
	interpupillaryDistance = Committer('float')


class OrthographicCamera(Camera):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#orthographic-camera
	
	"""
	
	variant = b'orthographic'
	
	height = Committer('float')
	aspect = Committer('float')


class PanoramicCamera(Camera):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#panoramic-camera
	
	"""
	
	variant = b'panoramic'


class FrameBuffer(ManagedObject):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#framebuffer
	
	"""
	
	NONE = OSP_FB_NONE
	RGBA8 = OSP_FB_RGBA8
	SRGBA = OSP_FB_SRGBA
	RGBA32F = OSP_FB_RGBA32F
	
	COLOR = OSP_FB_COLOR
	DEPTH = OSP_FB_DEPTH
	ACCUM = OSP_FB_ACCUM
	VARIANCE = OSP_FB_VARIANCE
	NORMAL = OSP_FB_NORMAL
	ALBEDO = OSP_FB_ALBEDO

	def __init__(self, size, format, channels):
		self._size = size
		self._format = format
		self._channels = channels
	
	def _make_ospray_object(self):
		return ospNewFrameBuffer(self._size, self._format, self._channels)
	
	def writePPM(self, filename):
		ospWritePPM(filename, self._size, self._ospray_object)
	
	def clear(self, channels):
		ospFrameBufferClear(self._ospray_object, channels)
	
	# TODO: Add map, unmap, and pixel op


class PixelOp(ManagedObject):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#pixel-operation
	
	"""
	
	variant = None
	
	def _make_ospray_object(self):
		return ospNewPixelOp(self.variant)


class ToneMapper(PixelOp):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#tone-mapper
	
	"""
	
	variant = b'tonemapper'
	
	contrast = Committer('float')
	shoulder = Committer('float')
	midIn = Committer('float')
	midOut = Committer('float')
	hdrMax = Committer('float')


class Data(ManagedObject):
	"""See `the documentation`__.
	
	__ https://www.ospray.org/documentation.html#data
	
	"""
	
	DEVICE = OSP_DEVICE
	VOID_PTR = OSP_VOID_PTR
	DATA = OSP_DATA
	OBJECT = OSP_OBJECT
	CAMERA = OSP_CAMERA
	FRAMEBUFFER = OSP_FRAMEBUFFER
	LIGHT = OSP_LIGHT
	MATERIAL = OSP_MATERIAL
	TEXTURE = OSP_TEXTURE
	RENDERER = OSP_RENDERER
	MODEL = OSP_MODEL
	GEOMETRY = OSP_GEOMETRY
	VOLUME = OSP_VOLUME
	TRANSFER_FUNCTION = OSP_TRANSFER_FUNCTION
	PIXEL_OP = OSP_PIXEL_OP
	STRING = OSP_STRING
	CHAR = OSP_CHAR
	UCHAR = OSP_UCHAR
	UCHAR2 = OSP_UCHAR2
	UCHAR3 = OSP_UCHAR3
	UCHAR4 = OSP_UCHAR4
	USHORT = OSP_USHORT
	INT = OSP_INT
	INT2 = OSP_INT2
	INT3 = OSP_INT3
	INT4 = OSP_INT4
	UINT = OSP_UINT
	UINT2 = OSP_UINT2
	UINT3 = OSP_UINT3
	UINT4 = OSP_UINT4
	LONG = OSP_LONG
	LONG2 = OSP_LONG2
	LONG3 = OSP_LONG3
	LONG4 = OSP_LONG4
	ULONG = OSP_ULONG
	ULONG2 = OSP_ULONG2
	ULONG3 = OSP_ULONG3
	ULONG4 = OSP_ULONG4
	FLOAT = OSP_FLOAT
	FLOAT2 = OSP_FLOAT2
	FLOAT3 = OSP_FLOAT3
	FLOAT4 = OSP_FLOAT4
	FLOAT3A = OSP_FLOAT3A
	DOUBLE = OSP_DOUBLE
	
	NONE = 0
	SHARED_BUFFER = OSP_DATA_SHARED_BUFFER
	
	def __init__(self, type, data, flags):
		self._type = type
		self._data = data
		self._flags = flags
	
	def _make_ospray_object(self):
		return ospNewData((self._type, self._data), self._flags)


class _Builtin:
	"""Expose provided color and opacity maps.
	
	Intended to be used like::
	
	  colormap = builtin.colormaps['coolToWarm']
	  data = Data(Data.FLOAT, np.array(colormap), Data.NONE)
	  
	  opacity = builtin.opacitymaps['ramp']
	  data = Data(Data.FLOAT, np.array(opacity), Data.NONE)
	
	"""
	
	@lazy_property
	def colormaps(self):
		"""Return a dictionary of colormaps."""
		return load_colormaps()
	
	@lazy_property
	def opacitymaps(self):
		"""Return a dictionary of opacity maps."""
		return load_opacitymaps()


builtin = _Builtin()
