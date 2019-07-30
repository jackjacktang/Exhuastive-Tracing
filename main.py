import argparse
from scipy import ndimage	
import time
import numpy as np
import scipy.misc
from utils.io import *
from new_fm import *
from new_hp import *
# from hierarchy_prune import *
import skfmm
np.set_printoptions(threshold=np.inf)

def main():
	parser = argparse.ArgumentParser(description='Arguments for Exhuastive Tracing.')
	parser.add_argument('--file', type=str, default=None, required=True, help='The path of input file')
	parser.add_argument('--out', type=str, default=None, required=True, help='The out path of output swc')
	parser.add_argument('--threshold', type=float, default=0, help='threshold to distinguish the foreground and background; works on filtered image if --filter is enabled')
	parser.add_argument('--soma_threshold', type=float, default=-1, help='The threshold on the original image to get soma radius')
	parser.add_argument('--coverage_ratio', type=float, default=0.9, help='Coverage ratio used for hierarchical pruning.')

	# Argument for tracing
	parser.add_argument('--allow_gap', dest='allow_gap', action='store_true', help='allow gap during tracing')
	parser.add_argument('--no-allow_gap', dest='allow_gap', action='store_false', help='allow no gap during tracing')
	parser.set_defaults(allow_gap=True)

	parser.add_argument('--trace', dest='trace', action='store_true', help='Run tracing with APP2')
	parser.add_argument('--no-trace', dest='trace', action='store_false', help='Skip the tracing with APP2')
	parser.set_defaults(trace=True)

	parser.add_argument('--dt', dest='trace', action='store_true', help='Perform dt when fast marching')
	parser.add_argument('--no-dt', dest='trace', action='store_false', help='Skip dt')
	parser.set_defaults(dt=True)

	# enhanced iteration number
	parser.add_argument('--iter', type=int, default=0, help='Enhanced iteration number')
	# MISC
	parser.add_argument('--silence', dest='silence', action='store_true')
	parser.add_argument('--no-silence', dest='silence', action='store_false')
	parser.set_defaults(silence=False)

	args = parser.parse_args()

	starttime = time.time()
	print('--load image')
	img = loadimg(args.file)

	print('--crop image')
	img = crop(img,args.threshold)[0]
	print('--save crop image')
	writetiff3d(args.out+'crop.tif',img)
	size = img.shape
	print('--input image size: ', size)

    # Distance Transform
	if args.trace:
		print('--DT to find soma location')
		print('--Started: %.2f sec.' % (time.time() - starttime))
		bimg = (img > args.threshold).astype('int')
		dt_result = skfmm.distance(bimg, dx=5e-2)

		# find seed location (maximum intensity node)
		max_dt = np.max(dt_result)
		seed_location = np.argwhere(dt_result==np.max(dt_result))[0]
		max_intensity = img[seed_location[0]][seed_location[1]][seed_location[2]]
		print('--seed index',max_dt,max_intensity,seed_location[0],seed_location[1],seed_location[2])
		print('--Finished: %.2f sec.' % (time.time() - starttime))

		timemap = []
		if args.iter != 0:
			dt_result[dt_result > 0.04] = 0.04
			# dt_result = max_dt-dt_result
			speed = makespeed(dt_result)
			marchmap = np.ones(bimg.shape)
			marchmap[seed_location[0]][seed_location[1]][seed_location[2]] = -1
			timemap = skfmm.travel_time(marchmap, speed, dx=5e-3)
			# print('timemap shape',timemap.shape)
			imgxy2d = timemap.min(axis=-1)

			# scipy.misc.imsave('imgxy2d_projection.tif', imgxy2d)

		print('--SKFMM: %.2f sec.' % (time.time() - starttime))
		print('--initial reconstruction by Fast Marching')
		alive = fastmarching(img,bimg,dt_result,timemap,size,seed_location[0],seed_location[1],seed_location[2],max_intensity,args.threshold,args.out,args.iter,args.coverage_ratio)
		print('--initial reconstruction finished')
		print('--FM Total: %.2f sec.' % (time.time() - starttime))

		# starttime2 = time.time()
		# print('--perform hierarchical pruning')
		# hp(img,bimg,size,alive,args.out,args.threshold)
		# print('--APP2 finished')
		# print('--Pruning: %.2f sec.' % (time.time() - starttime2))
		# print('--Finished: %.2f sec.' % (time.time() - starttime))

		

def makespeed(dt):
    '''
    Make speed image for FM from distance transform
    '''

    F = dt**4
    F[F <= 0] = 1e-10

    return F

def crop(img, thr):
    """Crop a 3D block with value > thr"""
    ind = np.argwhere(img > thr)
    x = ind[:, 0]
    y = ind[:, 1]
    z = ind[:, 2]
    xmin = max(x.min() - 10, 0)
    xmax = min(x.max() + 10, img.shape[0])
    ymin = max(y.min() - 10, 1)
    ymax = min(y.max() + 10, img.shape[1])
    zmin = max(z.min() - 10, 2)
    zmax = min(z.max() + 10, img.shape[2])

    return img[xmin:xmax, ymin:ymax, zmin:zmax], np.array(
        [[xmin, xmax], [ymin, ymax], [zmin, zmax]])


if __name__ == "__main__":
    main()