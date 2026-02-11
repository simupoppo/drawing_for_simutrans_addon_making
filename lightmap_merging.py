import numpy as np

def lightmap_merge_program(intexture,x,y,inimg,paksize,mode):
    def def_bg_color(mode):
        if mode == 0:
            return np.array([231,255,255])
        elif mode == 1:
            return np.array([0,0,0,0])
    def resize_color(input,mode):
        if mode==0 or mode==3:
            return input
        elif mode == 2:
            return np.append(input,128)
        else:
            return np.delete(input,3)
    bgcolor=def_bg_color(mode%2)
    imX=inimg.shape[0]
    imY=inimg.shape[1]
    temp_list=np.zeros((imX,imY,(3+mode//2)))
    def change_size():
        for i in range(imX):
            for j in range(imY):
                if np.array_equal(inimg[i,j],bgcolor)or np.array_equal(inimg[i,j],np.zeros(3+mode%2)):
                    # print(i,j,inimg[i,j])
                    temp_list[i,j]=def_bg_color(mode//2)
                elif (-x<imX<intexture.shape[0]-x) or (-y<imY<intexture.shape[0]-y):  
                    temp_list[i,j]=intexture[i-x,i-y]*resize_color(inimg[i,j],mode)/128                  
                else:
                    temp_list[i,j]=def_bg_color(mode//2)
    change_size()
    temp_list[temp_list>255]=255
    outimg=temp_list.astype(np.uint8)
    # print(outimg)
    # print(outimg.shape)
    return outimg


