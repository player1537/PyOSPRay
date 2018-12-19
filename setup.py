#!/usr/bin/env python3.6

from distutils.core import setup, Extension
from distutils.command.build import build as _build
from pathlib import Path


# Thanks https://scipy-cookbook.readthedocs.io/items/SWIG_NumPy_examples.html
import numpy
numpy_include = numpy.get_include()


class build(_build):
	sub_commands = [
		('build_ext', _build.has_ext_modules),
		('build_py', _build.has_pure_modules),
		('build_clib', _build.has_c_libraries),
		('build_scripts', _build.has_scripts),
	]


pyospray_module = Extension(
	'_pyospray',
	sources=['src/pyospray/pyospray.i'],
	swig_opts=['-py3', '-threads', '-I/usr/include/ospray'],
	include_dirs=[numpy_include],
	libraries=['ospray'],
)


setup(
	cmdclass={'build': build},
	name='pyospray',
	packages=['pyospray'],
	package_dir={'pyospray': 'src/pyospray'},
	package_data={'pyospray': ['data/*.txt']},
	version='0.1.0',
	description="Python wrapper around the OSPRay renderer with both the native and a Pythonic API",
	author='Tanner Hobson',
	author_email='thobson2@vols.utk.edu',
	url='https://github.com/player1537/pyospray',
	keywords=[
		'path-tracer',
		'ospray',
		'ray-tracing',
		'visualization',
		'renderering',
	],
	ext_modules=[
		pyospray_module,
	],
)
