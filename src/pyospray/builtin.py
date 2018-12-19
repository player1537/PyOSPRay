"""

"""

from pkg_resources import resource_filename
from pathlib import Path


__all__ = [
	'load_colormaps', 'load_opacitymaps',
]


def tokenize(lines):
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
	return load_builtin_data('colormaps')


def load_opacitymaps():
	return load_builtin_data('opacitymaps')
