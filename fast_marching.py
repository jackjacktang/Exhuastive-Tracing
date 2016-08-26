import numpy as np
import numpy.linalg
import math


class vertex():
	def __init__(self,_ind,_x,_y,_z,_dt,_intensity,_state):
		self.ind = _ind
		self.x = _x
		self.y = _y
		self.z = _z
		self.dt= _dt
		self.intensity = _intensity
		self.state = _state
		self.neighbours = []

	def add_neighbours(vertex_a,vertex_b):
		vertex_a.neighbours.append(vertex_b)
		vertex_b.neighbours.append(vertex_a)

	def euc_distance(self,vertex_a,vertex_b):
		distance = np.linalg.norm(vertex_a-vertex_b)
		return distance

	def geodesic_distance(self,intensity_max,_vertex):
		# this 10 can be set up as a parameter
		return math.exp(10 * ((1-_vertex.intensity/intensity_max) ** 2))


def initailize(self,vertices,size,bimg):
	index = 0
	for i in range (size[0]):
		for j in range (size[1]):
			for k in range (size[2]):
				flag = 'FAR'
				if bimg[i][j][k] == 1:
					flag = 'ALIVE'
				element = vertex(index, i, j, k, dtimg[i][j][k], img[i][j][k], flag)
				vertices.append(element)

	for i in np.where(bimg == 1):
		print('--soma location')
		print(i)
			
	return vertices

def get_neighbours(self,_vertex,size):
	neighbours = []
	x = _vertex.x
	y = _vertex.y
	z = _vertex.z


def set_trial_set(self,vertices):
	for i in vertices:
		if i.state == 'ALIVE':
			pass