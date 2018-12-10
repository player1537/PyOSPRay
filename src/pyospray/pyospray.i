%module pyospray
%{
#define SWIG_FILE_WITH_INIT
#define SWIG_PYTHON_STRICT_BYTE_CHAR
#include <ospray/ospray.h>

%}

%typemap(in) (int *argc, const char **argv) {
  /* Check if is a list */
  if (PyList_Check($input)) {
    int i;
    $1 = malloc(sizeof(int));
    *$1 = PyList_Size($input);
    $2 = (char **) malloc(*($1+1)*sizeof(char *));
    for (i = 0; i < *$1; i++) {
      PyObject *o = PyList_GetItem($input, i);
      if (PyString_Check(o)) {
        $2[i] = PyString_AsString(PyList_GetItem($input, i));
      } else {
        free($2);
        free($1);
        PyErr_SetString(PyExc_TypeError, "list must contain strings");
        SWIG_fail;
      }
    }
    $2[i] = 0;
  } else {
    PyErr_SetString(PyExc_TypeError, "not a list");
    SWIG_fail;
  }
}

%typemap(freearg) (int *argc, const char **argv) {
  free((int *) $1);
  free((char *) $2);
}

%typemap(in) uint32_t {
	$1 = (uint32_t)PyInt_AsLong($input);
}

%typemap(in) int32_t {
	$1 = (int32_t)PyInt_AsLong($input);
}

%typemap(in) (size_t numItems, OSPDataType, const void *source, const uint32_t dataCreationFlags) {
	PyObject *pyType, *pySource, *pyFlags, *o;
	SwigPyObject *sobj;
	int i, len;

	if (!PyTuple_Check($input)) {
		PyErr_SetString(PyExc_TypeError, "not a list");
		SWIG_fail;
	}
	
	if (PyTuple_Size($input) != 3) {
		PyErr_SetString(PyExc_TypeError, "not exactly 3 arguments");
		SWIG_fail;
	}
	
	pyType = PyTuple_GetItem($input, 0);
	pySource = PyTuple_GetItem($input, 1);
	pyFlags = PyTuple_GetItem($input, 2);
	
	if (!PyInt_Check(pyType)) {
		PyErr_SetString(PyExc_TypeError, "type not an int");
		SWIG_fail;
	}
	$2 = ($2_ltype)PyInt_AsLong(pyType);
	
	if (!PyInt_Check(pyFlags)) {
		PyErr_SetString(PyExc_TypeError, "flags not an int");
		SWIG_fail;
	}
	$4 = ($4_ltype)PyInt_AsLong(pyType);
	
	if (!PyList_Check(pySource)) {
		PyErr_SetString(PyExc_TypeError, "source not a list");
		SWIG_fail;
	}
	
	len = PyList_Size(pySource);
	if ($4 == OSP_FLOAT3A) {
		$1 = len / 4;
		$3 = ($3_ltype)malloc($1 * 4 * sizeof(float));
		
	} else if ($4 == OSP_LIGHT) {
		$1 = len;
		$3 = ($3_ltype)malloc($1 * sizeof(OSPLight *));
	
	} else if ($4 == OSP_FLOAT4) {
		$1 = len / 4;
		$3 = ($3_ltype)malloc($1 * 4 * sizeof(float));
	
	} else if ($4 == OSP_INT3) {
		$1 = len / 3;
		$3 = ($3_ltype)malloc($1 * 3 * sizeof(int));
		
	} else {
		PyErr_SetString(PyExc_TypeError, "unknown OSPDataType");
		SWIG_fail;
	}
	
	for (i = 0; i < len; i++) {
		o = PyList_GetItem(pySource, i);
		if ($4 == OSP_FLOAT3A || $4 == OSP_FLOAT4) {
			if (!PyFloat_Check(o)) {
				free($3);
				PyErr_SetString(PyExc_TypeError, "list must contain floats");
				SWIG_fail;
			}
			
			*((float *)$3 + i) = (float)PyFloat_AsDouble(o);
		
		} else if ($4 == OSP_INT3) {
			if (!PyInt_Check(o)) {
				free($3);
				PyErr_SetString(PyExc_TypeError, "list must contain ints");
				SWIG_fail;
			}
			
			*((int *)$3 + i) = (int)PyInt_AsLong(o);
			
		} else if ($4 == OSP_LIGHT) {
			if (!SwigPyObject_Check(o)) {
				free($3);
				PyErr_SetString(PyExc_TypeError, "list must contain swig objects");
				SWIG_fail;
			}
			
			sobj = SWIG_Python_GetSwigThis(o);
			
			*((OSPLight **)$3 + i) = sobj->ptr;
		
		} else {
			free($3);
			PyErr_SetString(PyExc_TypeError, "unknown OSPDataType (2)");
			SWIG_fail;
		}
	}
}

%include "ospray.h"
%include "OSPDataType.h"


%{
void
ospWritePPM(const char *filename,
            const osp_vec2i *size,
            const OSPFrameBuffer framebuffer) {
  const uint32_t *pixel = (uint32_t *)ospMapFrameBuffer(framebuffer, OSP_FB_COLOR);
  
  FILE *file = fopen(filename, "wb");
  if (!file) {
    fprintf(stderr, "fopen('%s', 'wb') failed: %d", filename, errno);
    ospUnmapFrameBuffer(pixel, framebuffer);
    return;
  }
  fprintf(file, "P6\n%i %i\n255\n", size->x, size->y);
  unsigned char *out = (unsigned char *)alloca(3*size->x);
  for (int y = 0; y < size->y; y++) {
    const unsigned char *in = (const unsigned char *)&pixel[(size->y-1-y)*size->x];
    for (int x = 0; x < size->x; x++) {
      out[3*x + 0] = in[4*x + 0];
      out[3*x + 1] = in[4*x + 1];
      out[3*x + 2] = in[4*x + 2];
    }
    fwrite(out, 3*size->x, sizeof(char), file);
  }
  fprintf(file, "\n");
  fclose(file);
  ospUnmapFrameBuffer(pixel, framebuffer);
}
%}

void
ospWritePPM(const char *filename,
            const osp_vec2i *size,
            const OSPFrameBuffer framebuffer);

%{
void
ospToPixels(const char *format,
            const osp_vec2i *size,
            const OSPFrameBuffer framebuffer,
            char **buffer,
            int *buflen) {
  int is_rgb, is_rgba;
  size_t index;
  
  is_rgb = strcmp(format, "rgb") == 0;
  is_rgba = strcmp(format, "rgba") == 0;
  
  if (is_rgb) {
  	*buflen = size->x * size->y * 3;
  } else if (is_rgba) {
  	*buflen = size->x * size->y * 4;
  }
  
  *buffer = malloc(*buflen);
  
  const uint32_t *pixel = (uint32_t *)ospMapFrameBuffer(framebuffer, OSP_FB_COLOR);
  
  index = 0;
  for (int y = 0; y < size->y; y++) {
    const unsigned char *in = (const unsigned char *)&pixel[(size->y-1-y)*size->x];
    for (int x = 0; x < size->x; x++) {
      if (is_rgb || is_rgba) {
        buffer[0][index++] = in[4*x + 0];
        buffer[0][index++] = in[4*x + 1];
        buffer[0][index++] = in[4*x + 2];
      }
      if (is_rgba) {
        buffer[0][index++] = in[4*x + 3];
      }
    }
  }
  ospUnmapFrameBuffer(pixel, framebuffer);
}
%}

%include "cstring.i"
%cstring_output_allocate_size(char **buffer, int *buflen, free(*$1));
void
ospToPixels(const char *format,
            const osp_vec2i *size,
            const OSPFrameBuffer framebuffer,
            char **buffer, int *buflen);

%include "carrays.i"
%include "cdata.i"
%array_class(unsigned char, ospByteBuffer)
