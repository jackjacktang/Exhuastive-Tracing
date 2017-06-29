from io import *
import argparse
import numpy as np 
from random import random, randrange

def main():
	parser = argparse.ArgumentParser(description='Arguments for app2_py.')
	parser.add_argument('-f', type=str, default=None, required=True, help='The path of compared swc')
	args = parser.parse_args()

	swc = []
	with open(args.f) as f:
		lines = f.read().split('\n')
		for l in lines:
			if not l.startswith('#'):
				cells = l.split(' ')
				if len(cells) ==7:
					cells = [float(c) for c in cells]
					cells[2:5] = [c-1 for c in cells[2:5]]
					swc.append(cells)
	swc = np.array(swc)
	prev = -1
	current_color = 3
	for i in swc:
		current = i[6]
		if prev == current:
			prev = i[0]
			i[1] = current_color
		else:
			prev = i[0]
			current_color = randrange(256)
			i[1] = current_color

	with open(args.f+'ran.swc', 'w') as f:
		for i in range(swc.shape[0]):
			print('%d %d %.3f %.3f %.3f %.3f %d' % tuple(swc[i, :].tolist()), file=f)

if __name__ == "__main__":
    main()
