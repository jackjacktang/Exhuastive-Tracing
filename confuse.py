
# from utils.io import *
import argparse
import numpy as np
from scipy.spatial.distance import cdist

def main():
	parser = argparse.ArgumentParser(description='Arguments for app2_py.')
	parser.add_argument('-f', type=str, default=None, required=True, help='The path of compared swc')
	parser.add_argument('-g', type=str, default=None, required=True, help='The path of ground truth')
	args = parser.parse_args()
	result = loadswc(args.f)
	ground_truth = loadswc(args.g)
	precision_recall(result,ground_truth,4,4)

def loadswc(filepath):
    swc = []
    with open(filepath) as f:
        lines = f.read().split('\n')
        for l in lines:
            if not l.startswith('#'):
                cells = l.split(' ')
                if len(cells) ==7:
                    cells = [float(c) for c in cells]
                    cells[2:5] = [c-1 for c in cells[2:5]]
                    swc.append(cells)
    return np.array(swc)

def precision_recall(swc1, swc2, dist1=4, dist2=4):
    '''
    Calculate the precision, recall and F1 score between swc1 and swc2 (ground truth)
    It generates a new swc file with node types indicating the agreement between two input swc files
    In the output swc file: node type - 1. the node is in both swc1 agree with swc2
                                                        - 2. the node is in swc1, not in swc2 (over-traced)
                                                        - 3. the node is in swc2, not in swc1 (under-traced)
    target: The swc from the tracing method
    gt: The swc from the ground truth
    dist1: The distance to consider for precision
    dist2: The distance to consider for recall
    '''

    TPCOLOUR, FPCOLOUR, FNCOLOUR  = 3, 2, 180 # COLOUR is the SWC node type defined for visualising in V3D

    d = cdist(swc1[:, 2:5], swc2[:, 2:5])
    mindist1 = d.min(axis=1)
    tp = (mindist1 < dist1).sum()
    fp = swc1.shape[0] - tp

    mindist2 = d.min(axis=0)
    fn = (mindist2 > dist2).sum()
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1 = 2 * precision * recall / (precision + recall)

    # Make the swc for visual comparison
    swc1[mindist1 <= dist1, 1] = TPCOLOUR
    swc1[mindist1 > dist1, 1] = FPCOLOUR
    swc2_fn = swc2[mindist2 > dist2, :]
    swc2_fn[:, 0] = swc2_fn[:, 0] + 100000
    swc2_fn[:, -1] = swc2_fn[:, -1] + 100000
    swc2_fn[:, 1] = FNCOLOUR
    swc_compare = np.vstack((swc1, swc2_fn))
    swc_compare[:, -2]  = 1
    print('precision: ', precision)
    print('recall', recall)
    print('f1', f1)

    return (precision, recall, f1), swc_compare

def loadtiff3d(filepath):
    """Load a tiff file into 3D numpy array"""
    from libtiff import TIFFfile, TIFF
    tiff = TIFF.open(filepath, mode='r')
    stack = []
    for sample in tiff.iter_images():
        stack.append(np.flipud(sample))

    out = np.dstack(stack)
    tiff.close()

    return out


def writetiff3d(filepath, block):
    from libtiff import TIFFfile, TIFF
    try:
        os.remove(filepath)
    except OSError:
        pass

    tiff = TIFF.open(filepath, mode='w')
    block = np.flipud(block)
    
    for z in range(block.shape[2]):
        tiff.write_image(block[:,:,z], compression=None)
    tiff.close()

if __name__ == "__main__":
    main()