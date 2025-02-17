#-*- coding: utf-8 -*-
"""
@author:MD.Nazmuddoha Ansary
"""
from __future__ import print_function
#---------------------------------------------------------------
# imports
#---------------------------------------------------------------
from termcolor import colored
import os 
import numpy as np
import cv2
import random
import string
#---------------------------------------------------------------
# common utils
#---------------------------------------------------------------
def LOG_INFO(msg,mcolor='blue'):
    '''
        prints a msg/ logs an update
        args:
            msg     =   message to print
            mcolor  =   color of the msg    
    '''
    print(colored("#LOG     :",'green')+colored(msg,mcolor))
#---------------------------------------------------------------
def create_dir(base,ext):
    '''
        creates a directory extending base
        args:
            base    =   base path 
            ext     =   the folder to create
    '''
    _path=os.path.join(base,ext)
    if not os.path.exists(_path):
        os.mkdir(_path)
    return _path
#---------------------------------------------------------------
# image utils
#---------------------------------------------------------------
def stripPads(arr,val):
  '''
      strip specific values
  '''
  arr=arr[~np.all(arr == val, axis=1)]
  arr=arr[:, ~np.all(arr == val, axis=0)]
  return arr
#---------------------------------------------------------------

def padToFixedHeightWidth(img,h_max,w_max):
    '''
        pads an image to fixed height and width
    '''
    # shape
    h,w=img.shape
    if w<w_max:
        # pad widths
        left_pad_width =(w_max-w)//2
        # print(left_pad_width)
        right_pad_width=w_max-w-left_pad_width
        # pads
        left_pad =np.zeros((h,left_pad_width))
        right_pad=np.zeros((h,right_pad_width))
        # pad
        img =np.concatenate([left_pad,img,right_pad],axis=1)
    elif w>w_max: # reduce height
        h_new=int(w_max*h/w)
        img = cv2.resize(img, (w_max,h_new), fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
    # shape
    h,w=img.shape
    if h<h_max:    
        # pad heights
        top_pad_height =(h_max-h)//2
        bot_pad_height=h_max-h-top_pad_height
        # pads
        top_pad =np.zeros((top_pad_height,w))
        bot_pad=np.zeros((bot_pad_height,w))
        # pad
        img =np.concatenate([top_pad,img,bot_pad],axis=0)
    elif h>h_max:
        w_new=int(h_max*w/h)
        img = cv2.resize(img, (w_new,h_max), fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
    img = cv2.resize(img, (w_max,h_max), fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
    return img

def padAllAround(img,pad_dim):
    '''
        pads all around the image
    '''
    h,w=img.shape
    # pads
    left_pad =np.zeros((h,pad_dim))
    right_pad=np.zeros((h,pad_dim))
    # pad
    img =np.concatenate([left_pad,img,right_pad],axis=1)
    # shape
    h,w=img.shape
    top_pad =np.zeros((pad_dim,w))
    bot_pad=np.zeros((pad_dim,w))
    # pad
    img =np.concatenate([top_pad,img,bot_pad],axis=0)
    return img

#---------------------------------------------------------------
def placeWordOnMask(word,labeled_img,region_value,mask_ref,ext_reg=False,fill=False,ext=(0,10)):
    '''
        @author
        places a specific image on a given background at a specific location
        args:
            word               :   greyscale image to place
            labeled_img        :   labeled image to place the image
            region_value       :   the specific value of the labled region
            mask               :   placement mask
            ext_reg            :   extend the region to place
            fill
        return:
            mak :   mask image after placing 'img'
    '''
    mask=np.zeros_like(mask_ref)
    idx=np.where(labeled_img==region_value)
    # region
    y_min,y_max,x_min,x_max = np.min(idx[0]), np.max(idx[0]), np.min(idx[1]), np.max(idx[1])
    if ext_reg:
        h_li,w_li=labeled_img.shape
        h_reg = abs(y_max-y_min)
        w_reg = abs(x_max-x_min)
        if type(ext)==int:
            # ext
            h_ext=int((ext*h_reg)/100)
            w_ext=int((ext*w_reg)/100)
        else:        
            # ext
            h_ext=int((random.randint(ext[0],ext[1])*h_reg)/100)
            w_ext=int((random.randint(ext[0],ext[1])*w_reg)/100)
        # region ext
        if y_min-h_ext>0:y_min-=h_ext # extend min height
        if y_max+h_ext<=h_li:y_max+=h_ext # extend max height
        if x_min-w_ext>0:x_min-=w_ext # extend min width
        if x_max+w_ext<=w_li:x_max+=w_ext # extend min width
    
    if fill:
        # resize image    
        h_max = abs(y_max-y_min)
        w_max = abs(x_max-x_min)
        word = cv2.resize(word, (w_max,h_max), fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
    
    else:# unstable NOW    
        # resize image    
        h_max = abs(y_max-y_min)
        w_max = abs(x_max-x_min)
        h,w=word.shape
        w_needed=int(h_max* w/h) 
        word = cv2.resize(word, (w_needed,h_max), fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
        # fix padding
        word=padToFixedHeightWidth(word,h_max,w_max)    
    # place on mask
    mask[y_min:y_max,x_min:x_max]=word
    return mask
#---------------------------------------------------------------
def randColor():
    '''
        generates random color
    '''
    return (random.randint(0,255),random.randint(0,255),random.randint(0,255))
#---------------------------------------------------------------
def gaussian_heatmap(size=512, distanceRatio=2):
    '''
        creates a gaussian heatmap
        This is a fixed operation to create heatmaps
    '''
    # distrivute values
    v = np.abs(np.linspace(-size / 2, size / 2, num=size))
    # create a value mesh grid
    x, y = np.meshgrid(v, v)
    # spreading heatmap
    g = np.sqrt(x**2 + y**2)
    g *= distanceRatio / (size / 2)
    g = np.exp(-(1 / 2) * (g**2))
    g *= 255
    return g.clip(0, 255).astype('uint8')
#---------------------------------------------------------------
class GraphemeParser(object):
    '''
    @author: Tahsin Reasat
    Adoptation:MD. Nazmuddoha Ansary
    '''
    def __init__(self):
        self.vds    =['া', 'ি', 'ী', 'ু', 'ূ', 'ৃ', 'ে', 'ৈ', 'ো', 'ৌ']
        self.cds    =['ঁ', 'র্', 'র্য', '্য', '্র', '্র্য', 'র্্র']
        self.roots  =['ং','ঃ','অ','আ','ই','ঈ','উ','ঊ','ঋ','এ','ঐ','ও','ঔ','ক','ক্ক','ক্ট','ক্ত','ক্ল','ক্ষ','ক্ষ্ণ',
                    'ক্ষ্ম','ক্স','খ','গ','গ্ধ','গ্ন','গ্ব','গ্ম','গ্ল','ঘ','ঘ্ন','ঙ','ঙ্ক','ঙ্ক্ত','ঙ্ক্ষ','ঙ্খ','ঙ্গ','ঙ্ঘ','চ','চ্চ',
                    'চ্ছ','চ্ছ্ব','ছ','জ','জ্জ','জ্জ্ব','জ্ঞ','জ্ব','ঝ','ঞ','ঞ্চ','ঞ্ছ','ঞ্জ','ট','ট্ট','ঠ','ড','ড্ড','ঢ','ণ',
                    'ণ্ট','ণ্ঠ','ণ্ড','ণ্ণ','ত','ত্ত','ত্ত্ব','ত্থ','ত্ন','ত্ব','ত্ম','থ','দ','দ্ঘ','দ্দ','দ্ধ','দ্ব','দ্ভ','দ্ম','ধ',
                    'ধ্ব','ন','ন্জ','ন্ট','ন্ঠ','ন্ড','ন্ত','ন্ত্ব','ন্থ','ন্দ','ন্দ্ব','ন্ধ','ন্ন','ন্ব','ন্ম','ন্স','প','প্ট','প্ত','প্ন',
                    'প্প','প্ল','প্স','ফ','ফ্ট','ফ্ফ','ফ্ল','ব','ব্জ','ব্দ','ব্ধ','ব্ব','ব্ল','ভ','ভ্ল','ম','ম্ন','ম্প','ম্ব','ম্ভ',
                    'ম্ম','ম্ল','য','র','ল','ল্ক','ল্গ','ল্ট','ল্ড','ল্প','ল্ব','ল্ম','ল্ল','শ','শ্চ','শ্ন','শ্ব','শ্ম','শ্ল','ষ',
                    'ষ্ক','ষ্ট','ষ্ঠ','ষ্ণ','ষ্প','ষ্ফ','ষ্ম','স','স্ক','স্ট','স্ত','স্থ','স্ন','স্প','স্ফ','স্ব','স্ম','স্ল','স্স','হ',
                    'হ্ন','হ্ব','হ্ম','হ্ল','ৎ','ড়','ঢ়','য়']

        self.punctuations           =   ['!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+',
                                        ',', '-', '.', '/', ':', ':-', ';', '<', '=', '>', '?', 
                                        '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~', '।', '—', '’', '√']

        self.numbers                =    ['০','১','২','৩','৪','৫','৬','৭','৮','৯']
        self.engraphemes =  list(string.ascii_lowercase)
        self.ennumbers   =  [str(i) for i in range(10)]
        
        self.ignore                 =   self.punctuations+self.numbers+self.engraphemes+self.ennumbers+[" "]


    def word2grapheme(self,word):
        graphemes = []
        grapheme = ''
        i = 0
        while i < len(word):
            if word[i] in self.ignore:
                graphemes.append(word[i])
            else:
                grapheme += (word[i])
                # print(word[i], grapheme, graphemes)
                # deciding if the grapheme has ended
                if word[i] in ['\u200d', '্']:
                    # these denote the grapheme is contnuing
                    pass
                elif word[i] == 'ঁ':  
                    # 'ঁ' always stays at the end
                    graphemes.append(grapheme)
                    grapheme = ''
                elif word[i] in list(self.roots) + ['়']:
                    # root is generally followed by the diacritics
                    # if there are trailing diacritics, don't end it
                    if i + 1 == len(word):
                        graphemes.append(grapheme)
                    elif word[i + 1] not in ['্', '\u200d', 'ঁ', '়'] + list(self.vds):
                        # if there are no trailing diacritics end it
                        graphemes.append(grapheme)
                        grapheme = ''

                elif word[i] in self.vds:
                    # if the current character is a vowel diacritic
                    # end it if there's no trailing 'ঁ' + diacritics
                    # Note: vowel diacritics are always placed after consonants
                    if i + 1 == len(word):
                        graphemes.append(grapheme)
                    elif word[i + 1] not in ['ঁ'] + list(self.vds):
                        graphemes.append(grapheme)
                        grapheme = ''

            i = i + 1
            # Note: df_cd's are constructed by df_root + '্'
            # so, df_cd is not used in the code

        return graphemes

#---------------------------------------------------------------
def rotate_image(mat, angle):
    """
        Rotates an image (angle in degrees) and expands image to avoid cropping
    """

    height, width = mat.shape[:2] # image shape has 3 dimensions
    image_center = (width/2, height/2) # getRotationMatrix2D needs coordinates in reverse order (width, height) compared to shape

    rotation_mat = cv2.getRotationMatrix2D(image_center, angle, 1.)

    # rotation calculates the cos and sin, taking absolutes of those.
    abs_cos = abs(rotation_mat[0,0]) 
    abs_sin = abs(rotation_mat[0,1])

    # find the new width and height bounds
    bound_w = int(height * abs_sin + width * abs_cos)
    bound_h = int(height * abs_cos + width * abs_sin)

    # subtract old image center (bringing image back to origo) and adding the new image center coordinates
    rotation_mat[0, 2] += bound_w/2 - image_center[0]
    rotation_mat[1, 2] += bound_h/2 - image_center[1]

    # rotate image with the new bounds and translated rotation matrix
    rotated_mat = cv2.warpAffine(mat, rotation_mat, (bound_w, bound_h),flags=cv2.INTER_NEAREST)
    return rotated_mat

#---------------------------------------------------------------
def draw_random_noise(bin_img,bin_val,img):
    '''
        draws random poly
    '''
    y_idx, x_idx = np.where(bin_img==bin_val)   
    h,w,d=img.shape
    min_dim=min(h,w)

    num_points=random.randint(min_dim//10,min_dim//5)
    rand_idx1 = random.choice(y_idx)   #randomly choose any element in the x_idx list
    x1 = x_idx[rand_idx1]
    y1 = y_idx[rand_idx1] 
    for i in range(0,num_points):
        x2 = x1+random.randint(-10,10)
        y2 = y1+random.randint(5,30)
        cv2.line(img,(x1,y1),(x2,y2),(0,0,0),random.randint(2,10))
        x1=x2
        y1=y2 
            
    return img
#---------------------------------------------------------------
def cleanImage(img,rgb=False):
    '''
    removes shadows and thresholds
    '''

    result_norm_planes = []
    # split rgb
    rgb_planes = cv2.split(img)
    # clean planes
    for plane in rgb_planes:
        # dilate
        dilated_img = cv2.dilate(plane, np.ones((7,7), np.uint8))
        # background
        bg_img = cv2.medianBlur(dilated_img, 21)
        # difference
        diff_img = 255 - cv2.absdiff(plane, bg_img)
        # normalized
        norm_img = cv2.normalize(diff_img,None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        # append
        result_norm_planes.append(norm_img)
    # merge rgb
    img = cv2.merge(result_norm_planes)
    if rgb:
        return img
    # grayscale
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # threshold
    blur = cv2.GaussianBlur(img_gray,(5,5),0)
    _,img = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    return img
