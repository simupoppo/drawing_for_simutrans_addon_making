import numpy as np
from PIL import Image
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import os

class change_paksize():
    def __init__(self, input_file, output_file, beforesize, aftersize):
        self.input=input_file
        self.output=output_file
        self.before=int(beforesize)
        self.after=int(aftersize)
    def flag(self):
        if os.path.isfile(self.input)==False:
            return 0
        else:
            imge = Image.open(self.input)
            print(imge.mode)
            im = np.array(imge)
            print(im.shape)
            imX = im.shape[0]
            imY = im.shape[1]
            if imge.mode == "RGBA":
                #f=open("img.txt","w")
                #for i in range(self.before):
                #    f.write("[")
                #    for j in range(self.before):
                #        f.write(str(im[i,j])+",")
                #    f.write("]\n")
                #f.close()
                #return 2
                modemode=2
            elif imge.mode=="RGB":
                modemode=0
            else:
                return 2
            #if imge.mode=="P":
            #    modemode=1
            print(im[0,0])
            if imX % self.before == 0 and imY % self.before == 0 and self.before>0 and self.after>0:
                output=Image.fromarray(change_paksize_program(im,self.before,self.after,modemode))
                output.save(self.output)
                return 1
            else: 
                return 2

def change_paksize_program(inimg,beforesize,aftersize,mode):
    def search_icon(inimg,beforesize):
        imX=inimg.shape[0]
        imY=inimg.shape[1]
        intX=imX//beforesize
        intY=imY//beforesize
        returnlist=[]
        for i in range(intX):
            for j in range(intY):
                temp_int=1
                for k in range(32):
                    for l in range(32):
                        if set(inimg[i*beforesize+k,j*beforesize+l])==set(bgcolor):
                            temp_int=0  
                for k in range(33):
                    if set(inimg[i*beforesize+k,j*beforesize+32])!=set(bgcolor):
                        temp_int=0
                for k in range(33):
                    if set(inimg[i*beforesize+32,j*beforesize+k])!=set(bgcolor):
                        temp_int=0
                if temp_int==1:
                    returnlist.append([i,j])
        return returnlist
    def def_bg_color(mode):
        if mode == 0:
            return np.array([231,255,255])
        elif mode == 2:
            return np.array([231,255,255,255])
        elif mode == 3:
            return np.array([0,0,0,0])
    bgcolor=def_bg_color(mode)
    def change_size(inimg,beforesize,aftersize):
        imX = inimg.shape[0]
        imY = inimg.shape[1]
        ratioX = imX//beforesize
        ratioY = imY//beforesize
        print(bgcolor)
        if beforesize==aftersize:
            return inimg
        else:
            if beforesize<aftersize:
                results=np.zeros(ratioX*aftersize*ratioY*aftersize*len(bgcolor)).reshape(ratioX*aftersize,ratioY*aftersize,len(bgcolor))
                if beforesize>31 and aftersize>31: 
                    iconlist=search_icon(inimg,beforesize)
                else:
                    iconlist=[]
                for i in range(ratioX*aftersize):
                    for j in range(ratioY*aftersize):
                        ratioi=i%aftersize-(aftersize-beforesize)//2
                        ratioj=j%aftersize-(aftersize-beforesize)//2
                        coli=i//aftersize
                        colj=j//aftersize
                        if [coli,colj]in iconlist:
                            if 0<=i-coli*aftersize<32 and 0<=j-colj*aftersize<32:
                                results[i,j]=inimg[i-coli*aftersize+coli*beforesize,j-colj*aftersize+colj*beforesize]
                            else:
                                results[i,j]=bgcolor                        
                        elif 0<=ratioi<beforesize:
                            if 0<=ratioj<beforesize:
                                results[i,j]=inimg[coli*beforesize+ratioi,colj*beforesize+ratioj]
                            else:
                                results[i,j]=bgcolor
                        else:
                            results[i,j]=bgcolor
                return results
            else:
                changeratio=beforesize//aftersize+1
                results=np.zeros(ratioX*aftersize*ratioY*aftersize*changeratio**2).reshape(ratioX*aftersize*changeratio,changeratio*ratioY*aftersize)
                for i in range(ratioX):
                    for j in range(ratioY):
                        ratioi=i%aftersize
                        ratioj=j&aftersize
                        coli=i//aftersize
                        colj=j//aftersize
    outimg=change_size(inimg,beforesize,aftersize)     
    outimg=outimg.astype(np.uint8)
    print(outimg)
    print(outimg.shape)
    return outimg




def make_window():
    def ask_files():
        path=filedialog.askopenfilename()
        file_path.set(path)

    def app():
        beforesize=(input_pak_box.get())
        aftersize=(output_pak_box.get())
        input_file = file_path.get()
        output_file = filedialog.asksaveasfilename(
            filetype=[("PNG Image Files","*.png")],defaultextension=".png"
        )
        print(output_file)
        if not input_file or not output_file or not beforesize or not aftersize:
            return
        if (int(beforesize)-int(aftersize))%2!=0:
            messagebox.showinfo("エラー","偶数値を指定してください")
            return
        elif int(beforesize)>int(aftersize):
            messagebox.showinfo("エラー","TILECUTTERをご利用ください")
            return
        afterfile = change_paksize(input_file,output_file,beforesize,aftersize)
        if afterfile.flag() ==0:
            messagebox.showinfo("エラー","画像がありません")
        elif afterfile.flag() ==1:
            messagebox.showinfo("完了","完了しました。")
        elif afterfile.flag() ==2:
            messagebox.showinfo("エラー","画像サイズが正しくありません")
    main_win = tk.Tk()
    main_win.title("change_image_paksize")
    main_win.geometry("500x200")
    main_frm = ttk.Frame(main_win)
    main_frm.grid(column=0, row=0, sticky=tk.NSEW, padx=5, pady=10)
    file_path=tk.StringVar()
    folder_label = ttk.Label(main_frm, text="ファイルを選択")
    folder_box = ttk.Entry(main_frm,textvariable=file_path)
    folder_btn = ttk.Button(main_frm, text="選択",command=ask_files)
    input_pak_label = ttk.Label(main_frm, text="元画像のpakサイズ")
    input_pak_box = ttk.Entry(main_frm)
    output_pak_label = ttk.Label(main_frm, text="生成するpakサイズ")
    output_pak_box = ttk.Entry(main_frm)
    app_btn=ttk.Button(main_frm, text="変換を実行",command=app)
    folder_label.grid(column=0,row=0,pady=10)
    folder_box.grid(column=1,row=0,sticky=tk.EW, padx=5)
    folder_btn.grid(column=2,row=0)
    input_pak_box.grid(column=1,row=1,sticky=tk.EW, padx=5)
    input_pak_label.grid(column=0,row=1)
    output_pak_box.grid(column=1,row=2,sticky=tk.EW, padx=5)
    output_pak_label.grid(column=0,row=2)
    app_btn.grid(column=1,row=4)
    #main_win.columnconfigure(0, wieght=1)
    #main_win.rowconfigure(0, wieght=1)
    #main_frm.columnconfigure(1, wieght=1)
    main_win.mainloop()
    
if __name__ == "__main__":
    make_window()