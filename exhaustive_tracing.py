import numpy as np
import numpy.linalg
import math
import time
from utils.io import *
from node import *
from scipy.spatial.distance import euclidean
from scipy.fftpack import fftn, ifftn, ifft
from scipy.special import jv
from new_hp import *


givals = [
    22026.5, 20368, 18840.3, 17432.5, 16134.8, 14938.4, 13834.9, 12816.8,
    11877.4, 11010.2, 10209.4, 9469.8, 8786.47, 8154.96, 7571.17, 7031.33,
    6531.99, 6069.98, 5642.39, 5246.52, 4879.94, 4540.36, 4225.71, 3934.08,
    3663.7, 3412.95, 3180.34, 2964.5, 2764.16, 2578.14, 2405.39, 2244.9,
    2095.77, 1957.14, 1828.24, 1708.36, 1596.83, 1493.05, 1396.43, 1306.47,
    1222.68, 1144.62, 1071.87, 1004.06, 940.819, 881.837, 826.806, 775.448,
    727.504, 682.734, 640.916, 601.845, 565.329, 531.193, 499.271, 469.412,
    441.474, 415.327, 390.848, 367.926, 346.454, 326.336, 307.481, 289.804,
    273.227, 257.678, 243.089, 229.396, 216.541, 204.469, 193.129, 182.475,
    172.461, 163.047, 154.195, 145.868, 138.033, 130.659, 123.717, 117.179,
    111.022, 105.22, 99.7524, 94.5979, 89.7372, 85.1526, 80.827, 76.7447,
    72.891, 69.2522, 65.8152, 62.5681, 59.4994, 56.5987, 53.856, 51.2619,
    48.8078, 46.4854, 44.2872, 42.2059, 40.2348, 38.3676, 36.5982, 34.9212,
    33.3313, 31.8236, 30.3934, 29.0364, 27.7485, 26.526, 25.365, 24.2624,
    23.2148, 22.2193, 21.273, 20.3733, 19.5176, 18.7037, 17.9292, 17.192,
    16.4902, 15.822, 15.1855, 14.579, 14.0011, 13.4503, 12.9251, 12.4242,
    11.9464, 11.4905, 11.0554, 10.6401, 10.2435, 9.86473, 9.50289, 9.15713,
    8.82667, 8.51075, 8.20867, 7.91974, 7.64333, 7.37884, 7.12569, 6.88334,
    6.65128, 6.42902, 6.2161, 6.01209, 5.81655, 5.62911, 5.44938, 5.27701,
    5.11167, 4.95303, 4.80079, 4.65467, 4.51437, 4.37966, 4.25027, 4.12597,
    4.00654, 3.89176, 3.78144, 3.67537, 3.57337, 3.47528, 3.38092, 3.29013,
    3.20276, 3.11868, 3.03773, 2.9598, 2.88475, 2.81247, 2.74285, 2.67577,
    2.61113, 2.54884, 2.48881, 2.43093, 2.37513, 2.32132, 2.26944, 2.21939,
    2.17111, 2.12454, 2.07961, 2.03625, 1.99441, 1.95403, 1.91506, 1.87744,
    1.84113, 1.80608, 1.77223, 1.73956, 1.70802, 1.67756, 1.64815, 1.61976,
    1.59234, 1.56587, 1.54032, 1.51564, 1.49182, 1.46883, 1.44664, 1.42522,
    1.40455, 1.3846, 1.36536, 1.3468, 1.3289, 1.31164, 1.29501, 1.27898,
    1.26353, 1.24866, 1.23434, 1.22056, 1.2073, 1.19456, 1.18231, 1.17055,
    1.15927, 1.14844, 1.13807, 1.12814, 1.11864, 1.10956, 1.10089, 1.09262,
    1.08475, 1.07727, 1.07017, 1.06345, 1.05709, 1.05109, 1.04545, 1.04015,
    1.03521, 1.0306, 1.02633, 1.02239, 1.01878, 1.0155, 1.01253, 1.00989,
    1.00756, 1.00555, 1.00385, 1.00246, 1.00139, 1.00062, 1.00015, 1
]

def GI(w,h,d, img, max_intensity, min_intensity):
    index = (int)((img[w][h][d] - min_intensity)/max_intensity * 255)
    if index > 255:
        index = 255
    return givals[index]

"""
Exhaustive Tracing

"""
def exhaustive_tracing(img, bimg, dt_result, timemap, size, seed, max_intensity,threshold,out_path,r_iter,coverage_ratio):
    # state 0 for FAR, state 1 for TRAIL, state 2 for ALIVE
    state = np.zeros((size[0], size[1], size[2]))
    result = []

    # initialize 
    tbimg = np.copy(bimg)
    phi = np.empty((size[0], size[1], size[2]), dtype=np.float32)
    parent = np.empty((size[0], size[1], size[2]), dtype=np.int32)
    prev = np.empty((size[0], size[1], size[2]), dtype=np.int32)
    swc_index = np.empty((size[0], size[1], size[2]), dtype=np.int32)

    for i in range(size[0]):
        phi[i,:,:] = np.inf

    current_index = 0
    # put seed into ALIVE set
    state[seed[0],seed[1],seed[2]] = 2
    phi[seed[0],seed[1],seed[2]] = 0.0
    swc_index[seed[0],seed[1],seed[2]] = 1
    prev[seed[0],seed[1],seed[2]] = 1

    # trail set structure[phi,w,h,d,par_id]
    trail_set = np.asarray([[0,seed[0],seed[1],seed[2]]],dtype=np.float32)

    # alive set structure: [id,radius,w,h,d,1,par_id]
    alive_set = None
    starttime = time.time()
    totaltime = 0
    counter = 0
    while (trail_set.size != 0):
        counter+=1
        min_ind = trail_set[0,:]

        trail_set = np.delete(trail_set, (0), axis=0)
        i,j,k = min_ind[1:4]
        i = int(i)
        j = int(j)
        k = int(k)
        prev_ind = prev[i,j,k]
        parent[i,j,k] = prev_ind

        state[i][j][k] = 2
        swc_index[i][j][k] = current_index
        # print(alive_set.shape)
        if alive_set is None:
            alive_set = np.asarray([[current_index,3,i,j,k,1,0]],dtype=np.int32)
        else:
            alive_set = np.vstack((alive_set,[current_index,3,i,j,k,1,prev_ind]))
        # print('alive:',alive_set)

        tbimg[i][j][k] = 2
        current_index += 1

        neighbor_ind = get_neighbor_ind(img.shape,i-1,i+2,j-1,j+2,k-1,k+2)

        for ind in neighbor_ind:
            factor = 1
            if ind[3] == 2:
                factor = 1.414214

            w,h,d = ind[0:3]

            if (img[w,h,d] <= threshold and
                img[i,j,k] <= threshold):
                continue

            if (state[w][h][d] != 2):
                # min_intensity set as 0
                new_dist = phi[w][h][d] + (GI(
                    w,h,d, img, max_intensity, 0.0) + GI(
                    i,j,k, img, max_intensity, 0.0)) * factor * 0.5
                        
                prev_ind = swc_index[i][j][k]

                if (state[w,h,d] == 0):
                    phi[w,h,d] = new_dist
                    # insert into trail set
                    if trail_set.shape[0] == 0:
                        trail_set = np.asarray([[new_dist,w,h,d]],dtype=np.float32)
                    else:
                        trail_set = np.vstack((trail_set,[new_dist,w,h,d]))
                        trail_set = trail_set[np.argsort(trail_set[:,0])]

                    prev[w][h][d] = prev_ind
                    state[w][h][d] = 1

                elif (state[w][h][d] == 1):
                    if (phi[w][h][d] > new_dist):
                        phi[w][h][d] = new_dist
                        temp_ind = np.argwhere((trail_set[:,1] == w) & (trail_set[:,2] == h) & (trail_set[:,3] == d))[0]
                        trail_set[temp_ind][0] = new_dist
                        trail_set = trail_set[np.argsort(trail_set[:,0])]
                        sort_time = time.time()
                        prev[w][h][d] = prev_ind

    print('alive size:',alive_set.shape)
    ini = alive_set.copy()
    swc_x = ini[:, 2].copy()
    swc_y = ini[:, 3].copy()
    ini[:, 2] = swc_y
    ini[:, 3] = swc_x
    saveswc(out_path + 'ini.swc',ini) 
    bb = np.zeros(img.shape) 
    hp_result,bb = hp(img,bimg,size,alive_set,out_path,threshold,bb,1,bimg,coverage_ratio)
    result = hp_result
    print(result.shape)

    if r_iter == 0:
        swc_x = result[:, 2].copy()
        swc_y = result[:, 3].copy()
        result[:, 2] = swc_y
        result[:, 3] = swc_x
        saveswc(out_path + str(r_iter) + 'result.swc',result)
        return

    # enhanced iteration
    far = np.argwhere(bimg == 1)
    if far.shape[0] != 0:
        no_iteration = 0
        # current_index += 1
        far_timemap = np.array([[]])
        for f in far:
            # if (bimg[f[0]][f[1]][f[2]]] == 1):
            if far_timemap.shape[1] == 0:
                far_timemap = np.asarray([[f[0],f[1],f[2],timemap[f[0]][f[1]][f[2]]]])
            else:
                far_timemap = np.vstack((far_timemap,[f[0],f[1],f[2],timemap[f[0]][f[1]][f[2]]]))
        sort_timemap = far_timemap[np.argsort(far_timemap[:,3])]
        sort_timemap = sort_timemap[::-1]

        alive_loc = alive_set[2:5]

        
    while (far.size > 0 and sort_timemap.size > 0):
        # alive_set = []
        padding_index = current_index

        if(no_iteration >= r_iter):
            break

        #UPDATE 
        trail_set = np.asarray([[0,sort_timemap[0][0],sort_timemap[0][1],sort_timemap[0][2]]])

        new_alive = np.asarray([[]])

        while (trail_set.size != 0):
            min_ind = trail_set[0,:]

            trail_set = np.delete(trail_set, (0), axis=0)
            i = int(min_ind[1])
            j = int(min_ind[2])
            k = int(min_ind[3])
            if state[i][j][k] != 3:
                print(state[i][j][k])

            prev_ind = prev[i][j][k]
            parent[i][j][k] = prev_ind

            state[i][j][k] = 4
            swc_index[i][j][k] = current_index

            if(new_alive.shape[1] == 0):
                new_alive = np.asarray([[0,3,i,j,k,1,-1]])
                alive_set = np.vstack((alive_set,[current_index,3,i,j,k,1,-1]))
            else:
                p_ind = prev_ind-padding_index
                new_alive = np.vstack((new_alive,[current_index-padding_index,3,i,j,k,1,p_ind]))
                alive_set = np.vstack((alive_set,[current_index,3,i,j,k,1,prev_ind]))
            tbimg[i][j][k] = 2
            current_index += 1
            totaltime+=(time.time()-starttime)

            neighbor_ind = get_neighbor_ind(img.shape,i-1,i+2,j-1,j+2,k-1,k+2)

            for ind in neighbor_ind:

                w,h,d = ind[0:3]
                factor = 1
                if ind[3] == 2:
                    factor = 1.414214

                if (img[w][h][d] <= threshold):
                    continue

                if (state[w][h][d] == 1 or state[w][h][d] == 2):
                    break

                if (state[w][h][d] != 4):
                # min_intensity set as 0
                    new_dist = phi[w][h][d] + (GI(
                        w,h,d, img, max_intensity, 0.0) + GI(
                            i,j,k, img, max_intensity, 0.0)
                                           ) * factor * 0.5
                    prev_ind = swc_index[i][j][k]

                    if (state[w][h][d] == 0):
                        phi[w][h][d] = new_dist
                        # insert into trail set
                        if trail_set.shape[1] == 0:
                            trail_set = np.vstack((trail_set,[new_dist,w,h,d]))
                        else:
                            sort_time = time.time()
                            trail_set = np.vstack((trail_set,[new_dist,w,h,d]))
                            trail_set = trail_set[np.argsort(trail_set[:,0])]

                        prev[w][h][d] = prev_ind
                        # 3 for reinforce trail
                        state[w][h][d] = 3

                    elif (state[w][h][d] == 3):
                        if (phi[w][h][d] > new_dist):
                            phi[w][h][d] = new_dist
                            temp_ind = np.argwhere((trail_set[:,1] == w) & (trail_set[:,2] == h) & (trail_set[:,3] == d))[0]
                            trail_set[temp_ind][0] = new_dist
                            trail_set = trail_set[np.argsort(trail_set[:,0])]
                            sort_time = time.time()
                            prev[w][h][d] = prev_ind   
        if(new_alive.size == 0):
            no_iteration += 1
            continue
        # print('new_alive shape',new_alive.shape)
        new = new_alive.copy()
        swc_x = new[:, 2].copy()
        swc_y = new[:, 3].copy()
        new[:, 2] = swc_y
        new[:, 3] = swc_x

        hp_result,bb = hp(img,bimg,size,new_alive,out_path,threshold,bb,2,bimg,coverage_ratio)

        # print('no of enhanced iteration: ',no_iteration)
        if(hp_result is None or hp_result.shape[1] == 0):
            no_iteration += 1
            continue

        # print('padding index', padding_index)
        hp_result[:,0] += padding_index
        hp_result[:,6] += padding_index
        hp_result[:,5] = 1
        result = np.vstack((result,hp_result))
        sort_timemap = np.delete(sort_timemap,0)
        no_iteration += 1
        
    print('--Enhanced tracing finished')
    print('--Enhanced iteration: %.2f sec.' % (time.time() - starttime))
    r = alive_set

    swc_x = alive_set[:, 2].copy()
    swc_y = alive_set[:, 3].copy()
    alive_set[:, 2] = swc_y
    alive_set[:, 3] = swc_x

    swc_x = result[:, 2].copy()
    swc_y = result[:, 3].copy()
    result[:, 2] = swc_y
    result[:, 3] = swc_x
    saveswc(out_path + '_ini.swc',alive_set)
    saveswc(out_path + '_result.swc',result)

    return r

def get_neighbor_ind(size,i_min,i_max,j_min,j_max,k_min,k_max):
    result = []
    i = i_min + 1
    j = j_min + 1
    k = k_min + 1
    if i-1 < 0:
        i_min = i
    if i+1 >= size[0]:
        i_max = i+1
    if j-1 < 0:
        j_min = j
    if j+1 >= size[1]:
        j_max = j+1
    if k-1 < 0:
        k_min = k
    if k+1 >= size[2]:
        k_max = k+1

    for kk in range(k_min,k_max):
        for jj in range(j_min,j_max):
            for ii in range(i_min,i_max):
                offset = abs(k-kk) + abs(j-jj) + abs(i-ii)
                if offset <= 2 and offset != 0:
                    result.append([ii,jj,kk,offset])

    return np.asarray(result)


def crop(img,spatial1,spatial2):
    """Crop a 3D block with value > thr"""
    minx = int(np.minimum(spatial1[0],spatial2[0]))
    maxx = int(np.maximum(spatial1[0],spatial2[0]))
    miny = int(np.minimum(spatial1[1],spatial2[1]))
    maxy = int(np.maximum(spatial1[1],spatial2[1]))
    minz = int(np.minimum(spatial1[2],spatial2[2]))
    maxz = int(np.maximum(spatial1[2],spatial2[2]))
    return img[minx:maxx, miny:maxy, minz:maxz]

def enhance(img,spatial1,spatial2,img2):
    minx = int(np.minimum(spatial1[0],spatial2[0]))
    maxx = int(np.maximum(spatial1[0],spatial2[0]))
    miny = int(np.minimum(spatial1[1],spatial2[1]))
    maxy = int(np.maximum(spatial1[1],spatial2[1]))
    minz = int(np.minimum(spatial1[2],spatial2[2]))
    maxz = int(np.maximum(spatial1[2],spatial2[2]))
    img[minx:maxx, miny:maxy, minz:maxz] = img2
    return img


def response(img, radii,rsptype='oof'):
    eps = 1e-12
    rsp = np.zeros(img.shape)
    # bar = progressbar.ProgressBar(max_value=kwargs['radii'].size)
    # bar.update(0)

    W = np.zeros((img.shape[0], img.shape[1], img.shape[2], 3)) # Eigen values to save
    V = np.zeros((img.shape[0], img.shape[1], img.shape[2], 3, 3)) # Eigen vectors to save

    if rsptype == 'oof' :
        rsptensor = ooftensor(img, radii)

    # pbar = tqdm(total=len(radii))
    for i, tensorfield in enumerate(rsptensor):
        # Make the tensor from tensorfield
        f11, f12, f13, f22, f23, f33 = tensorfield
        tensor = np.stack((f11, f12, f13, f12, f22, f23, f13, f23, f33), axis=-1)
        del f11
        del f12
        del f13
        del f22
        del f23
        del f33
        tensor = tensor.reshape(img.shape[0], img.shape[1], img.shape[2], 3, 3)
        w, v = np.linalg.eigh(tensor)
        del tensor
        sume = w.sum(axis=-1)
        nvox = img.shape[0] * img.shape[1] * img.shape[2]
        sortidx = np.argsort(np.abs(w), axis=-1)
        sortidx = sortidx.reshape((nvox, 3))

        # Sort eigenvalues according to their abs
        w = w.reshape((nvox, 3))
        for j, (idx, value) in enumerate(zip(sortidx, w)):
            w[j,:] = value[idx]
        w = w.reshape(img.shape[0], img.shape[1], img.shape[2], 3)

        # Sort eigenvectors according to their abs
        v = v.reshape((nvox, 3, 3))
        for j, (idx, vec) in enumerate(zip(sortidx, v)):
            v[j,:,:] = vec[:, idx]
        del sortidx
        v = v.reshape(img.shape[0], img.shape[1], img.shape[2], 3, 3)

        mine = w[:,:,:, 0]
        mide = w[:,:,:, 1]
        maxe = w[:,:,:, 2]

        if rsptype == 'oof':
            feat = maxe
        elif rsptype == 'bg':
            feat = -mide / maxe * (mide + maxe) # Medialness measure response
            cond = sume >= 0
            feat[cond] = 0 # Filter the non-anisotropic voxels

        del mine
        del maxe
        del mide
        del sume

        cond = np.abs(feat) > np.abs(rsp)
        W[cond, :] = w[cond, :]
        V[cond, :, :] = v[cond, :, :]
        rsp[cond] = feat[cond]
        del v
        del w
        del tensorfield
        del feat
        del cond
        # pbar.update(1)
        # print('rsp value',np.max(rsp),np.min(rsp))

    return rsp, V, W



def ooftensor(img, radii, memory_save=True):
    '''
    type: oof, bg
    '''
    # sigma = 1 # TODO: Pixel spacing
    eps = 1e-12
    # ntype = 1 # The type of normalisation
    fimg = fftn(img, overwrite_x=True)
    shiftmat = ifftshiftedcoormatrix(fimg.shape)
    x, y, z = shiftmat
    x = x / fimg.shape[0]
    y = y / fimg.shape[1]
    z = z / fimg.shape[2]
    kernel_radius = np.sqrt(x ** 2 + y ** 2 + z ** 2) + eps # The distance from origin

    for r in radii:
        # Make the fourier convolutional kernel
        jvbuffer = oofftkernel(kernel_radius, r) * fimg

        if memory_save:
            # F11
            buffer = ifftshiftedcoordinate(img.shape, 0) ** 2 * x * x * jvbuffer
            buffer = ifft(buffer, axis=0)
            buffer = ifft(buffer, axis=1)
            buffer = ifft(buffer, axis=2)
            f11 = buffer.copy()

            # F12
            buffer = ifftshiftedcoordinate(img.shape, 0) * ifftshiftedcoordinate(img.shape, 1) * x * y * jvbuffer
            buffer = ifft(buffer, axis=0)
            buffer = ifft(buffer, axis=1)
            buffer = ifft(buffer, axis=2)
            f12 = buffer.copy()

            # F13
            buffer = ifftshiftedcoordinate(img.shape, 0) * ifftshiftedcoordinate(img.shape, 2) * x * z * jvbuffer
            buffer = ifft(buffer, axis=0)
            buffer = ifft(buffer, axis=1)
            buffer = ifft(buffer, axis=2)
            f13 = buffer.copy()

            # F22
            buffer = ifftshiftedcoordinate(img.shape, 1) ** 2 * y ** 2 * jvbuffer
            buffer = ifft(buffer, axis=0)
            buffer = ifft(buffer, axis=1)
            buffer = ifft(buffer, axis=2)
            f22 = buffer.copy()

            # F23
            buffer = ifftshiftedcoordinate(img.shape, 1) * ifftshiftedcoordinate(img.shape, 2) * y * z * jvbuffer
            buffer = ifft(buffer, axis=0)
            buffer = ifft(buffer, axis=1)
            buffer = ifft(buffer, axis=2)
            f23 = buffer.copy()

            # F33
            buffer = ifftshiftedcoordinate(img.shape, 2) * ifftshiftedcoordinate(img.shape, 2) * z * z * jvbuffer
            buffer = ifft(buffer, axis=0)
            buffer = ifft(buffer, axis=1)
            buffer = ifft(buffer, axis=2)
            f33 = buffer.copy()
        else:
            f11 = np.real(ifftn(x * x * jvbuffer))
            f12 = np.real(ifftn(x * y * jvbuffer))
            f13 = np.real(ifftn(x * z * jvbuffer))
            f22 = np.real(ifftn(y * y * jvbuffer))
            f23 = np.real(ifftn(y * z * jvbuffer))
            f33 = np.real(ifftn(z * z * jvbuffer))
        yield [f11, f12, f13, f22, f23, f33]

def ifftshiftedcoormatrix(shape):
    shape = np.asarray(shape)
    p = np.floor(np.asarray(shape) / 2).astype('int')
    coord = []
    for i in range(shape.size):
        a = np.hstack((np.arange(p[i], shape[i]), np.arange(0, p[i]))) - p[i] - 1.
        repmatpara = np.ones((shape.size,)).astype('int')
        repmatpara[i] = shape[i]
        A = a.reshape(repmatpara)
        repmatpara = shape.copy()
        repmatpara[i] = 1
        coord.append(np.tile(A, repmatpara))

    return coord


def ifftshiftedcoordinate(shape, axis):
    shape = np.asarray(shape)
    p = np.floor(np.asarray(shape) / 2).astype('int')
    a = (np.hstack((np.arange(p[axis], shape[axis]), np.arange(0, p[axis]))) - p[axis] - 1.).astype('float')
    a /= shape[axis].astype('float')
    reshapepara = np.ones((shape.size,)).astype('int');
    reshapepara[axis] = shape[axis];
    A = a.reshape(reshapepara);
    repmatpara = shape.copy();
    repmatpara[axis] = 1;
    return np.tile(A, repmatpara)

def oofftkernel(kernel_radius, r, sigma=1, ntype=1):
    eps = 1e-12
    normalisation = 4/3 * np.pi * r**3 / (jv(1.5, 2*np.pi*r*eps) / eps ** (3/2)) / r**2 *  \
                    (r / np.sqrt(2.*r*sigma - sigma**2)) ** ntype
    jvbuffer = normalisation * np.exp( (-2 * sigma**2 * np.pi**2 * kernel_radius**2) / (kernel_radius**(3/2) ))
    return (np.sin(2 * np.pi * r * kernel_radius) / (2 * np.pi * r * kernel_radius) - np.cos(2 * np.pi * r * kernel_radius)) * \
               jvbuffer * np.sqrt( 1./ (np.pi**2 * r *kernel_radius ))

