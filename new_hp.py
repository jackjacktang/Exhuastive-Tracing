import numpy as np
import math
from node import *
from utils.io import *
from random import randint

"""
hierarchical pruning based on the initial tree reconstrucionn by fast marching
"""
def hp(img,bimg,size,alive,out,threshold,bb,phase,rsp,coverage_ratio):

    # alive = loadswc('test/2000-1/new_fm_ini.swc')
    filter_segs = swc2topo_segs(img,size,alive,out,threshold,phase)
    # filter_segs.shape[0] <=10 ???
    if (filter_segs.size == 0 or filter_segs.shape[0] <= 1):
        return None,bb
    print('filter shape',filter_segs.shape)
    
    # calculate radius for every node
    # store filter_segs [leaf_index,root_index,parent_index,length,level]
    print('--calculating radius for every node')

    for seg in filter_segs:
        leaf_marker = seg[0]
        root_marker = seg[1]
        p = int(leaf_marker)
        while(1):
            # real_threshold = 40
            # if (real_threshold < threshold):
            #     real_threshold = threshold
            alive[p][5] = getradius(bimg,alive[p][2],alive[p][3],alive[p][4],rsp)
            if (p == root_marker):
                break
            p = int(alive[p][6])


    print('--Hierarchical Pruning')
    result_segs,bb = hierchical_coverage_prune(alive,filter_segs,img,out,bb,phase,coverage_ratio)
    return result_segs,bb

"""
build segments based on the swc from the initial reconstruction
"""
def swc2topo_segs(img,size,alive,out,threshold,phase):
    tol_num = alive.shape[0]

    leaf_nodes = np.array([])
    child_no = np.zeros(tol_num, dtype=int)

    for i in alive[1:tol_num-1:,0]:
        child_no[int(alive[int(i)][6])] += 1
        

    child_index = np.where(child_no == 0)
    leaf_nodes = alive[child_index]


    topo_dists = np.zeros(tol_num)
    topo_leafs = np.empty(tol_num)


    for leaf in leaf_nodes:
        child_node = leaf
        parent_node = alive[int(child_node[6])]
        cid = int(child_node[0])
        topo_leafs[cid] = leaf[0]
        topo_dists[cid] = img[leaf[2]][leaf[3]][leaf[4]]/255.0
        while parent_node[0] != 0:
            pid = int(parent_node[0])
            tmp_dst = img[int(parent_node[2])][int(parent_node[3])][int(parent_node[4])]/255.0 + topo_dists[cid]

            if (tmp_dst >= topo_dists[pid]):
                topo_dists[pid] = tmp_dst
                topo_leafs[pid] = topo_leafs[cid]
            else:
                break
            child_node = parent_node
            cid = pid
            parent_node = alive[int(parent_node[6])]

    fp = np.argmax(topo_dists)
    fn = topo_leafs[fp]
    topo_segs = np.array([[]])

    
    # store filter_segs [leaf_index,root_index,parent_index,length,level]
    for leaf in leaf_nodes:
        root_marker = leaf
        root_parent = alive[int(root_marker[6])]
        level = 1

        while (root_parent[0] != 0 and topo_leafs[int(root_parent[0])] == leaf[0]):
            if child_no[int(root_marker[0])] >= 2:
                level += 1
            root_marker = root_parent
            root_parent = alive[int(root_marker[6])]
            # print('bingo')
        dst = topo_dists[int(root_marker[0])]

        parent_index = topo_leafs[int(root_parent[0])]

        if topo_segs.size == 0:
            topo_segs = np.asarray([[leaf[0],root_marker[0],parent_index,dst,level]])
        else:
            topo_segs = np.vstack((topo_segs,[leaf[0],root_marker[0],parent_index,dst,level]))

    if phase == 1:
        filter_segs = topo_segs[np.argwhere(topo_segs[:,3] > 2)]
        filter_segs = np.squeeze(filter_segs, axis=(1,))
    else:
        filter_segs = topo_segs
    # print(filter_segs)
    # print('filter_segs',filter_segs.shape)
    return filter_segs

"""
hierchical coverage pruning based on the segment reconstruction.
segments with coverage ratio less than threshold will be pruned
"""
def hierchical_coverage_prune(alive,filter_segs,img,out,bb,phase,coverage_ratio):
    bb = np.zeros(img.shape)
    sort_segs = filter_segs[np.argsort(filter_segs[:,3])]
    sort_segs = sort_segs[::-1]
    result_segs = np.array([[]])

    index = 0
    # store filter_segs [leaf_index,root_index,parent_index,length,level]
    size = sort_segs.shape
    for seg in sort_segs:
        # seg = sort_segs[index]
        current = int(seg[0])
        root = int(seg[1])
        overlap = 0
        non_overlap = 0
        tol_num = 0 # Total number of the covered area 
        
        if phase == 2 and size[0] == 1:
            break

        while (current != root):
            r = math.ceil(alive[int(current)][5] * 1.5)
            w = alive[current][2]
            h = alive[current][3]
            d = alive[current][4]
            x, y, z = np.meshgrid(
                    constrain_range(w - r, w + r + 1, 0, img.shape[0]),
                    constrain_range(h - r, h + r + 1, 0, img.shape[1]),
                    constrain_range(d - r, d + r + 1, 0, img.shape[2]))
            overlap += bb[x, y, z].sum()
            tol_num += x.shape[0] * x.shape[1] * x.shape[2] 
            current = int(alive[current][6])
        if tol_num == 0:
            continue
        coverage = overlap / tol_num

        if (coverage < coverage_ratio):
            current = int(seg[0])
            while (1):
                if result_segs.size == 0:
                    result_segs = np.array(alive[current])
                else:
                    result_segs = np.vstack((result_segs,alive[current]))
                if current == seg[1]:
                    break
                else:
                    current = alive[current][6]

            current = int(seg[0])
            root = int(seg[1])
            overlap = 0
            non_overlap = 0

            while (current != root):
                x,y,z = np.meshgrid(
                   constrain_range(w - r, w + r + 1, 0, img.shape[0]),
                    constrain_range(h - r, h + r + 1, 0, img.shape[1]),
                    constrain_range(d - r, d + r + 1, 0, img.shape[2]))            
                bb[x, y, z] = 1
                current = int(alive[current][6])

    return result_segs,bb
   

"""
make sure the mask area is in the bound of the image
"""
def constrain_range(min, max, minlimit, maxlimit):
    return list(
        range(min if min > minlimit else minlimit, max
              if max < maxlimit else maxlimit))


"""
estimate the radius for each node (PHC)
"""
def markerRadius(img,size,p,threshold):
    max_r = min(size[0]/2,size[1]/2,size[2]/2)

    for ir in range(1,int(max_r+1),1):
        total_num = background_num = 0
        
        for dz in range(-ir, ir+1,1):
            for dy in range(-ir, ir+1,1):
                for dx in range(-ir,ir+1,1):
                    total_num+=1
                    r = math.sqrt(dx*dx + dy*dy + dz*dz)
                    if (r > ir-1 and r<=ir):
                        i = p.w+dx
                        if (i<0 or i>=size[0]):
                            return ir
                        j = p.h+dy
                        if (j<0 or j>=size[1]):
                            return ir
                        k = p.d+dz
                        if (k<0 or k>=size[2]):
                            return ir 

                        if (img[i][j][k] <= threshold):
                            background_num+=1
                            if (background_num/total_num > 0.001):
                                return ir
    return ir

"""
estimate the radius for each node (Siqi)
"""
def getradius(bimg, x, y, z, rsp):
    r = 0
    x = math.floor(x)
    y = math.floor(y)
    z = math.floor(z)

    while True:
        r += 1
        try:
            if rsp[max(x - r, 0):min(x + r + 1, bimg.shape[0]), max(y - r, 0):
                    min(y + r + 1, bimg.shape[1]), max(z - r, 0):min(
                        z + r + 1, bimg.shape[2])].sum() / (2 * r + 1)**3 < .6:
                break
        except IndexError:
            break

    return r


"""
test method for store the longest segment

"""
def longest_segment(alive,start):
    longest = np.array([[]])
    current = int(start[0])
    root = int(start[1])

    while (current != root):
        if longest.size == 0:
            longest = np.asarray(alive[current])
        else:
            longest = np.vstack((longest,alive[current]))

        current = int(alive[current][6])

    swc_x = longest[:, 2].copy()
    swc_y = longest[:, 3].copy()
    longest[:, 2] = swc_y
    longest[:, 3] = swc_x

    return longest
