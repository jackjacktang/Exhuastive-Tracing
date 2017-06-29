# from anfilter import *
from io import * 
import matplotlib.pyplot as plt
from scipy import io as sio
import os
import numpy as np
import skfmm


# mat = sio.loadmat('tests/data/very-small-oof.mat', )
# img = mat['img']
def main():
	from libtiff import TIFFfile, TIFF
	tiff = TIFF.open('6.tif', mode='r')
	stack = []
	for sample in tiff.iter_images():
		stack.append(np.flipud(sample))

	out = np.dstack(stack)
	tiff.close()
	img=out

	bimg = (img > 19).astype('int')

	from libtiff import TIFFfile, TIFF
	try:
		os.remove('6_binary.tif')
	except OSError:
		pass

	tiff = TIFF.open('6_binary.tif', mode='w')
	bimg = np.flipud(bimg)
	
	for z in range(bimg.shape[2]):
		tiff.write_image(bimg[:,:,z], compression=None)
	tiff.close()



if __name__ == "__main__":
	main()

