#!/usr/bin/env python3.6

from distutils.core import setup, Extension
from pathlib import Path


pyospray_module = Extension(
	'_pyospray',
	sources=['pyospray/pyospray.i'],
	swig_opts=['-I/usr/include/ospray'],
	libraries=['ospray'],
)


setup(
	name='pyospray',
	packages=['pyospray'],
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
