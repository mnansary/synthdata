# -*-coding: utf-8 -
'''
    @author: MD. Nazmuddoha Ansary,MD. Mobassir Hossain
'''
#--------------------
# imports
#--------------------
from numpy.core.numeric import zeros_like
import regex 
import numpy as np 
import cv2
import os
from glob import glob 
import PIL.Image,PIL.ImageDraw,PIL.ImageFont
import random
import pandas as pd 

from .utils import stripPads,GraphemeParser,gaussian_heatmap
GP=GraphemeParser()
heatmap=gaussian_heatmap(size=512,distanceRatio=1.5)
#-----------------------------------
# line image
#----------------------------------
def handleExtensions(ext,font,max_width):
    '''
        creates/ adds extensions to lines
    '''
    width = font.getsize(ext)[0]
    
    # draw
    image = PIL.Image.new(mode='L', size=font.getsize(ext))
    draw = PIL.ImageDraw.Draw(image)
    draw.text(xy=(0, 0), text=ext, fill=1, font=font)
    num_ext=max_width//width
    if num_ext>1:
        ext_img=[np.array(image) for _ in range(max_width//width)]
        ext_img=np.concatenate(ext_img,axis=1)
        return ext_img
    else:
        return None

def createPrintedLine(text,font):
    '''
        creates printed word image
        args:
            text           :       the string
            font           :       the desired font
            
        returns:
            img     :       printed line image
            char_map:       c-heatmap
            word_map:       w-heatmap
    '''
    # draw
    image = PIL.Image.new(mode='L', size=font.getsize(text))
    draw = PIL.ImageDraw.Draw(image)
    draw.text(xy=(0, 0), text=text, fill=1, font=font)
    img= np.array(image)
    img_h,img_w=img.shape
    # heatmap per component
    words=text.split()
    curr_width=0
    char_maps=[]
    word_maps=[]
    for idx,word in enumerate(words):
        width,_=font.getsize(word)
        if idx==0:
            curr_width+=width
        else:
            space_width,_=font.getsize(word+' ')
            curr_width+=space_width
            
        comps=GP.word2grapheme(word)
        char_map=np.concatenate([heatmap for _ in comps],axis=1)
        char_map=cv2.resize(char_map,(width,img_h),fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
        if len(comps)>1:
            cmh,cmw=char_map.shape
            cmwg=cmw//len(comps)
            tb_pad=np.zeros((cmh//4,cmwg))
            gheatmap=cv2.resize(heatmap,(cmwg,cmh//2),fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
            gheatmap=np.concatenate([tb_pad,gheatmap,tb_pad],axis=0)
            word_map=np.concatenate([gheatmap for _ in range(len(comps)-1)],axis=1)
            hwm,wwm=word_map.shape
            lr_pad=np.zeros((hwm,cmwg//2))
            word_map=np.concatenate([lr_pad,word_map,lr_pad],axis=1)
            word_map=cv2.resize(word_map,(width,img_h),fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
        else:
            word_map=np.zeros_like(char_map)

        
        if idx>0:
            spad=np.zeros((img_h,curr_width-width))
            char_map=np.concatenate([spad,char_map],axis=1)
            word_map=np.concatenate([spad,word_map],axis=1)
        
        char_maps.append(char_map)
        word_maps.append(word_map)
        
    _,cm_w=char_map.shape
    for idx,char_map in enumerate(char_maps[:-1]):
        pad=np.zeros((img_h,cm_w-char_map.shape[1]))
        char_map=np.concatenate([char_map,pad],axis=1)
        char_maps[idx]=char_map
        word_map=np.concatenate([word_maps[idx],pad],axis=1)
        word_maps[idx]=word_map
        
    height,width=img.shape

    char_map=sum(char_maps)
    word_map=sum(word_maps)
    char_map=cv2.resize(char_map,(width,height),fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
    word_map=cv2.resize(word_map,(width,height),fx=0,fy=0, interpolation = cv2.INTER_NEAREST)

    return img,char_map,word_map

    
#-----------------------------------
# hw image
#----------------------------------
def createHandwritenWords(df,
                         comps,
                         pad,
                         comp_dim):
    '''
        creates handwriten word image
        args:
            df      :       the dataframe that holds the file name and label
            comps   :       the list of components 
            pad     :       pad class:
                                no_pad_dim
                                single_pad_dim
                                double_pad_dim
                                top
                                botimg
            comp_dim:       component dimension 
        returns:
            img     :       image
            char_map:       c-heatmap
            word_map:       g-heatmap
            
    '''
    comps=[str(comp) for comp in comps]
    # select a height
    height=comp_dim
    # reconfigure comps
    mods=['ঁ', 'ং', 'ঃ']
    while comps[0] in mods:
        comps=comps[1:]

    # alignment of component
    ## flags
    tp=False
    bp=False
    comp_heights=["" for _ in comps]
    for idx,comp in enumerate(comps):
        if any(te.strip() in comp for te in pad.top):
            comp_heights[idx]+="t"
            tp=True
        if any(be in comp for be in pad.bot):
            comp_heights[idx]+="b"
            bp=True


    imgs=[]
    char_maps=[]
    for cidx,comp in enumerate(comps):
        c_df=df.loc[df.label==comp]
        # select a image file
        idx=random.randint(0,len(c_df)-1)
        img_path=c_df.iloc[idx,2] 
        # read image
        img=cv2.imread(img_path,0)
        h,w=img.shape
        char_map=cv2.resize(heatmap,(w,h),fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
        
        # resize
        hf=comp_heights[cidx]
        if hf=="":
            img=cv2.resize(img,pad.no_pad_dim,fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
            char_map=cv2.resize(char_map,pad.no_pad_dim,fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
            
            if tp:
                h,w=img.shape
                top=np.ones((pad.height,w))*255
                img=np.concatenate([top,img],axis=0)
                char_map=np.concatenate([np.zeros_like(top),char_map],axis=0)
                
            if bp:
                h,w=img.shape
                bot=np.ones((pad.height,w))*255
                img=np.concatenate([img,bot],axis=0)
                char_map=np.concatenate([char_map,np.zeros_like(bot)],axis=0)
                
        elif hf=="t":
            img=cv2.resize(img,pad.single_pad_dim,fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
            char_map=cv2.resize(char_map,pad.single_pad_dim,fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
            
            if bp:
                h,w=img.shape
                bot=np.ones((pad.height,w))*255
                img=np.concatenate([img,bot],axis=0)
                char_map=np.concatenate([char_map,np.zeros_like(bot)],axis=0)
            
        elif hf=="b":
            img=cv2.resize(img,pad.single_pad_dim,fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
            char_map=cv2.resize(char_map,pad.single_pad_dim,fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
            if tp:
                h,w=img.shape
                top=np.ones((pad.height,w))*255
                img=np.concatenate([top,img],axis=0)
                char_map=np.concatenate([np.zeros_like(top),char_map],axis=0)
                
                
        elif hf=="bt" or hf=="tb":
            img=cv2.resize(img,pad.double_pad_dim,fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
            char_map=cv2.resize(char_map,pad.double_pad_dim,fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
            
        
        
        
        
        # mark image
        img=255-img
        img[img>0]=1
        imgs.append(img)
        char_maps.append(char_map)
        

    img=np.concatenate(imgs,axis=1)
    char_map=np.concatenate(char_maps,axis=1)
    
    h,w=img.shape 
    width= int(height* w/h) 
    img=cv2.resize(img,(width,height),fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
    char_map=cv2.resize(char_map,(width,height),fx=0,fy=0, interpolation = cv2.INTER_NEAREST)

    if len(comps)>1:
        cmh,cmw=char_map.shape
        cmwg=cmw//len(comps)
        tb_pad=np.zeros((cmh//4,cmwg))
        gheatmap=cv2.resize(heatmap,(cmwg,cmh//2),fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
        gheatmap=np.concatenate([tb_pad,gheatmap,tb_pad],axis=0)
        word_map=np.concatenate([gheatmap for _ in range(len(comps)-1)],axis=1)
        hwm,wwm=word_map.shape
        lr_pad=np.zeros((hwm,cmwg//2))
        word_map=np.concatenate([lr_pad,word_map,lr_pad],axis=1)
    else:
        word_map=np.zeros_like(char_map)


    word_map=cv2.resize(word_map,(width,height),fx=0,fy=0, interpolation = cv2.INTER_NEAREST)
    return img,char_map,word_map