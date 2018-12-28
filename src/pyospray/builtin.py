"""

"""

from pkg_resources import resource_filename
from pathlib import Path


__all__ = [
	'load_colormaps', 'load_opacitymaps',
]


def tokenize(lines):
	"""Tokenize a data file, yielding token and content tuples.
	
	The expected data format is::
	
	  [header]
	  1.23 4.543
	  3.12 3.34 5.6 9.8
	  
	  [header2]
	  1.23
	
	In other words, it is a header in square brackets followed by
	any number of floats.
	
	"""
	for line in lines:
		if line == '':
			continue
		
		if line.startswith('#'):
			continue

		if line.startswith('[') and line.endswith(']'):
			yield ('key', line[1:-1])
			continue
		
		values = tuple(map(float, line.split(' ')))
		yield ('values', values)
		continue


def load_builtin_data(name):
	"""Load data stored in the package by name.
	
	The returned data is a dictionary mapping header names (as keys)
	to lists of floats (as values).
	
	"""
	
	path = Path(resource_filename('pyospray', f'data/{name}.txt'))
	ret = {}
	values = None
	with path.open('r') as f:
		lines = (line.rstrip('\n') for line in f)
		for token, content in tokenize(lines):
			if token == 'key':
				values = []
				ret[content] = values
			
			elif token == 'values':
				values.extend(content)
			
			else:
				raise NotImplementedError
	
	return ret


def load_colormaps():
	"""Return the provided colormaps."""
	return load_builtin_data('colormaps')


def load_opacitymaps():
	"""Return the provided opacity maps."""
	return load_builtin_data('opacitymaps')
