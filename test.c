#include <stdio.h>
#include <stdint.h>
#include <errno.h>
#include <alloca.h>
#include <ospray/ospray.h>


#define WIDTH 1024
#define HEIGHT 512


int
main(int argc, const char **argv) {
	OSPError err;
	OSPCamera camera;
	osp_vec2i imgSize;
	
	err = ospInit(&argc, argv);
	if (err != OSP_NO_ERROR) {
		return err;
	}
	
	camera = ospNewCamera("panoramic");
	ospSetf(camera, "aspect", WIDTH/(float)HEIGHT);
	ospSet3f(camera, "pos", 0.0f, 0.0f, 0.0f);
	ospSet3f(camera, "dir", 0.1f, 0.0f, 1.0f);
	ospSet3f(camera, "up", 0.0f, 1.0f, 0.0f);
	ospCommit(camera);
	
	
	
	printf("Hello world\n");
	
	ospRelease(camera);
	
	return 0;
}
