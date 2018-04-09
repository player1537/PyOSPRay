#!/usr/bin/env python3.6

from distutils.core import setup, Extension
from pathlib import Path


ospray_module = Extension(
	'_ospray',
	sources=['ospray_wrap.c'],
	library_dirs=['/usr/local/lib'],
	libraries=['ospray'],
	runtime_library_dirs=['/usr/local/lib'],
)


setup(
	name='vision',
	version='1.0',
	description="The Shepherd's Vision: OSPRay Scene Manager",
	author='Tanner Hobson',
	author_email='thobson2@vols.utk.edu',
	packages=[],
	install_requires=[
	],
	ext_modules=[
		ospray_module,
	],
	py_modules=[
		'ospray',
	],
	entry_points={
		'console_scripts': [
		],
	},
)
