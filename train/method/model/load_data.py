import numpy as np
from tensorflow.keras import preprocessing
import cv2
import pandas as pd
from postprocessing import *
import os
import Augmentor


def load_datasets(filepath, sample_list, label_list, mark, a4c_or_a2c, m):
    """
    filepath : File storage directory.
    sample_list : the ones separate  for train and test.
    label_list : the list of golden_label correspond to sample_list.
    label[-1] is start_mark.
    mark is 1 --> load_train set and restore file into train set else 0 ---> test set.
    a2c_or_a4c is num 2 or 4
    """
    if mark:
        n = 4000
    else:
        n = 4000
    dst_pair1 = np.zeros(shape=(n, m, m, 1), dtype=np.float32)
    dst_pair2 = np.zeros(shape=(n, m, m, 1), dtype=np.float32)

    dst_label = np.zeros(shape=(n,), dtype=np.int32)
    k = 0
    label_list_copy = copy.deepcopy(label_list)
    for number in range(len(sample_list)):
            label = label_list_copy[sample_list[number]-1]   # o--->up   1--->down
            start_mark = label.pop()
           
            for i in (label):
                position = label.index(i)
                if position == len(label)-1:
                    break
                j = label[position+1]
                for t in range(i,j):
                    #  load imgs: from number i to number j-1-->pair1
                    #                        i+1            j-->pair2
                    img_p1 = cv2.imread(filepath+"Patient"+("000"+str(sample_list[number]))[-4:] +
                                        "\\a"+str(a4c_or_a2c)+"c\\"+str(t)+'.png', 0)
                
                    img_p2 = cv2.imread(filepath+"Patient"+("000"+str(sample_list[number]))[-4:] +
                                        "\\a"+str(a4c_or_a2c)+"c\\"+str(t+1)+'.png', 0)
 
                    # cut and unsamping use cv2.resize
                    dst_pair1[k, :, :, 0] = cv2.resize(img_p1[80:592, 176:688].reshape(512, -1, 1), (m, m))/255.0
                    dst_pair2[k, :, :, 0] = cv2.resize(img_p2[80:592, 176:688].reshape(512, -1, 1), (m, m))/255.0
                    if start_mark == 0:   # up
                        dst_label[k] = 0
                        
                    else:
                        dst_label[k] = 1
                        
                    k += 1
                    
                if start_mark == 0:
                    start_mark = 1
                else:
                    start_mark = 0
    if mark == 1:
        pathname = 'train'
    elif mark == 0:
        pathname = 'test'
    else:
        pathname = "val"

    os.mkdir('../'+pathname+'p1/')  # 保存的路径
    os.mkdir('../'+pathname+'p2/')

    K = 0
    for i in (dst_pair1[:k]):
        preprocessing.image.save_img('../'+pathname+'p1/'+str(K)+'.png', i)
        K += 1
    K = 0
    for i in (dst_pair2[:k]):
        preprocessing.image.save_img('../'+pathname+'p2/'+str(K)+'.png', i)
        K += 1
    return dst_pair1[:k], dst_pair2[:k], dst_label[:k]
                
        
def augment():
    """
    a pipeline of augment
    no params input
    """
    print("augmenting......")
    path1 = '../trainp1/'
    path2 = '../trainp2/'
    # 确定原始图像存储路径以及掩码文件存储路径
    p = Augmentor.Pipeline(path1)  # pair1
    p.ground_truth(path2)  # pair2
    # 图像旋转： 按照概率0.3执行，最大左旋角度10，最大右旋角度10
    p.rotate(probability=0.3, max_left_rotation=3, max_right_rotation=3) 
    # 图像左右互换： 按照概率0.2执行
    p.flip_left_right(probability=0.2) 
    # 弹性形变
    p.random_distortion(0.5, 2, 2, 2)
    # 缩放
    p.zoom(probability=0.5, min_factor=0.95, max_factor=1.05)
    # 所有概率全为1
    p.process()


def load_aug_data(path, m):
    """
    m: img_shape,e.g.64  128  256
    return matrix of shape (n,m,m,1)
    """
    aug_path = path+'output/'
    p1 = np.zeros(shape=(int(len(os.listdir(aug_path))/2), m, m, 1), dtype=np.float32)
    p2 = np.zeros(shape=(int(len(os.listdir(aug_path))/2), m, m, 1), dtype=np.float32)
    for filename in (os.listdir(aug_path)):
        img = preprocessing.image.load_img(aug_path+filename, color_mode="grayscale")
        if filename[:2] == 'tr':  # pair1
            index = filename.index('.')
            i = int(filename[17:index])
            
            p1[i] = preprocessing.image.img_to_array(img)/255.0
        else:
            index = filename.index('.')
            i = int(filename[25:index])

            p2[i] = preprocessing.image.img_to_array(img)/255.0
    print('aug_data is loaded!')
    return p1, p2


def get_label(path):  # get ED ES label
    """
    return a list of label
    """
    label_csv = pd.read_csv(path)
    label_list = []
    trans_list = list(np.array(label_csv).astype(np.int32))
    for i in trans_list:
        temp = []
        for j in i:
            if j >= 0:
                temp.append(j)
        label_list.append(temp)
    return label_list    
        
