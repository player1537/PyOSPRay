#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include <errno.h>
#include <ospray/ospray.h>


struct State {
	uint32_t length;
	osp_vec3f *vertex;
	osp_vec3f *normal;
	osp_vec3i *index;
	OSPGeometry geometry;
	OSPData vertex_data;
	OSPData normal_data;
	OSPData index_data;
	OSPLight light;
	OSPData light_data;
	OSPMaterial material;
	OSPModel model;
	OSPCamera camera;
	OSPRenderer renderer;
	OSPFrameBuffer framebuffer;
	osp_vec2i size;
	const uint32_t *pixels;
};


// helper function to write the rendered image as PPM file
static
void
writePPM(const char *fileName, const osp_vec2i *size, const uint32_t *pixel)
{
	FILE *file = fopen(fileName, "wb");
	if (!file) {
		fprintf(stderr, "fopen('%s', 'wb') failed: %d", fileName, errno);
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
}

static
void
error(OSPError err, const char *detail) {
	fprintf(stderr, "OSPRay error: %d\n", (int)err);
	fprintf(stderr, "  %s\n", detail);
}


const int width = 512;
const int height = 512;

extern
int
main(int argc_, char **argv_) {
	OSPError err;
	FILE *f;
	char buffer[80];
	size_t i;
	float xmin, xmax, ymin, ymax, zmin, zmax;
	struct State *state;
	int argc;
	const char *argv[1];
	
	static int initialized;
	
	if (!initialized) {
		argc = 0;
		argv[0] = NULL;
		
		err = ospInit(&argc, argv);
		if (err != OSP_NO_ERROR) {
			fprintf(stderr, "ospInit: %s\n", ospDeviceGetLastErrorMsg(ospGetCurrentDevice()));
			return 1;
		}
		
		ospDeviceSetErrorFunc(ospGetCurrentDevice(), error);
		
		initialized = 1;
	}
	
	state = calloc(1, sizeof(*state));
	
	f = fopen("teapot.raw", "rb");
	if (!f) {
		perror("fopen");
		return 1;
	}
	
	fseek(f, 0, SEEK_END);
	long fsize = ftell(f);
	fseek(f, 0, SEEK_SET);
	
	float *data = malloc(fsize);
	fread(data, fsize, 1, f);
	fclose(f);
	
	long data_size = fsize / sizeof(float);
	
	xmin = xmax = data[0];
	for (i=1; i<data_size; ++i) {
		if (data[i] < xmin) xmin = data[i];
		if (data[i] > xmax) xmax = data[i];
	}
	
	printf("[%f, %f]\n", xmin, xmax);
	
	OSPData data_data = ospNewData(fsize, OSP_FLOAT, data, OSP_DATA_SHARED_BUFFER);
	ospCommit(data_data);
	
	osp_vec3f color[2] = { { 0.2, 0.0, 0.0 }, { 0.8, 0.0, 0.0 } };
	OSPData color_data = ospNewData(2, OSP_FLOAT3, color, 0);
	ospCommit(color_data);
	
	float opacity[2] = { 0.2, 0.8 };
	OSPData opacity_data = ospNewData(2, OSP_FLOAT, opacity, 0);
	ospCommit(opacity_data);
	
	OSPTransferFunction transfer = ospNewTransferFunction("piecewise_linear");
	ospSetData(transfer, "colors", color_data);
	ospSetData(transfer, "opacities", opacity_data);
	ospSet2f(transfer, "valueRange", xmin, xmax);
	ospCommit(transfer);
	
	OSPVolume volume = ospNewVolume("shared_structured_volume");
	ospSetData(volume, "voxelData", data_data);
	ospSetObject(volume, "transferFunction", transfer);
	ospSet2f(volume, "voxelRange", xmin, xmax);
	ospSet3i(volume, "dimensions", 256, 256, 178);
	ospSetString(volume, "voxelType", "float");
	ospCommit(volume);
	
	state->model = ospNewModel();
	ospAddVolume(state->model, volume);
	ospCommit(state->model);
	
	state->camera = ospNewCamera("orthographic");
	ospSet3f(state->camera, "pos", -30.0, 0.0, 0.0);
	ospSet3f(state->camera, "dir", 1.0, 0.0, 0.0);
	ospSet3f(state->camera, "up", 0.0, 1.0, 0);
	ospSet1f(state->camera, "height", 2);
	ospSet1f(state->camera, "aspect", 1);
	ospCommit(state->camera);
	
	state->light = ospNewLight2("raytracer", "ambient");
	ospCommit(state->light);
	
	state->light_data = ospNewData(1, OSP_LIGHT, &state->light, 0);
	ospCommit(state->light_data);
	
	state->renderer = ospNewRenderer("raytracer");
	ospSetObject(state->renderer, "model", state->model);
	ospSetObject(state->renderer, "camera", state->camera);
	ospSetData(state->renderer, "lights", state->light_data);
	ospSet1i(state->renderer, "oneSidedLighting", 0);
	ospSet1f(state->renderer, "bgColor", 0.6);
	ospCommit(state->renderer);
	
	state->size.x = width;
	state->size.y = height;
	state->framebuffer = ospNewFrameBuffer(&state->size, OSP_FB_RGBA8, OSP_FB_COLOR);
	
	ospRenderFrame(state->framebuffer, state->renderer, OSP_FB_COLOR);
	
	state->pixels = ospMapFrameBuffer(state->framebuffer, OSP_FB_COLOR);
	
	writePPM("out.ppm", &state->size, state->pixels);
}
