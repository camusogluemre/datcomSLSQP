import subprocess
import numpy
import scipy
import math
from time import sleep
from scipy import interpolate
import matplotlib.pyplot as plt
import importlib 
from myfuncs import findDatcomIdx, createBounds, wing_optimization, optimization, indexFinder


latest_score=[]
total_opt_values=[]

for i_inp in range(0,6):
    fileName = 'for005.dat'
    
    [ZV, iTotalHeader, iTotalc, iTotalr, test005r_words ,test005r_lines, weight] = findDatcomIdx(fileName)

    global opt_scores
    opt_scores=[]

    [inp, b] = createBounds(ZV)

    opt_values = optimization(i_inp, inp, b, ZV, iTotalHeader, iTotalc, iTotalr, test005r_words, test005r_lines, weight, opt_scores)
    #----------------------------------------------------------------------------------------- READ
    with open('datcom.out', 'r') as results:
        results_lines = results.readlines()
        results_words = []
        results.close()
        global alpha
        for i in range (0, len(results_lines)):
            results_words.append(results_lines[i].split())
            
        iSr=[]
        iSc=[]
        for iR_row in range(0, len(results_words)):
            for iR_col in range(0, len(results_words[iR_row])):
                if results_words[iR_row][iR_col][:11] == "THEORITICAL" :
                    iSr.append(iR_row)
                    iSc.append(iR_col)
        wing_area=float(results_words[iSr[0]+1][iSc[0]])
                
        for iR_row in range(0, len(results_words)):
            for iR_col in range(0, len(results_words[iR_row])):
                if results_words[iR_row][iR_col] == "CL" :
                    iR1r=iR_row
                    iR1c=iR_col
                    lift_coef=float(results_words[iR1r+2][iR1c-1])*10/wing_area
                    
                if results_words[iR_row][iR_col] == "CD" :
                    iR2r=iR_row
                    iR2c=iR_col
                    alpha=float(results_words[iR2r+2][iR2c-2])
                    drag_coef=float(results_words[iR2r+2][iR2c-1])*10/wing_area

                if results_words[iR_row][iR_col][:8] == "VELOCITY" :
                    iVr=iR_row
                    iVc=iR_col
        velocity=float(results_words[iVr+3][iVc+1])
        pressure=float(results_words[iVr+3][iVc+2])
        temperature=float(results_words[iVr+3][iVc+3])
        density=float(pressure/(287.058*temperature))

        rCL=float(2*weight/(wing_area*density*velocity**2))

    with open('for005.dat','r') as file: # ---------------------------------------------------- READ
        file_lines = file.readlines()
        file_words=[]
        file.close()
        for i in range (0, len(file_lines)):
            file_words.append(file_lines[i].split())

        for i_row in range(0, len(file_words)):
            for i_col in range(0, len(file_words[i_row])):
                if file_words[i_row][i_col][:6] == "NALPHA" :
                    i1r=i_row
                    i1c=i_col

        for i_row in range(0, len(file_words)):
            for i_col in range(0, len(file_words[i_row])):
                if file_words[i_row][i_col][:9] == "ALSCHD(1)" :
                    i2r=i_row
                    i2c=i_col

        index=file_words[i1r][i1c].index("=")+1
        file_words[i1r][i1c]=file_words[i1r][i1c][:index]+"2.0,"
        newline= ' '.join(file_words[i1r])+ '\n'
        file_lines[i1r]=" "+newline

        index=file_words[i2r][i2c].index("=")+1
        file_words[i2r][i2c]=file_words[i2r][i2c][:index]+str(alpha-1)+", "+str(alpha)+','
        newline= ' '.join(file_words[i2r])+ '\n'
        file_lines[i2r]=" "+newline

    with open('for005.dat', 'w') as file_w: # ---------------------------------------------- WRT
        file_w.writelines(file_lines)
        file_w.close()
        file.close()

    cmnd = "digital_DATCOM.exe" # ----------------------------- RUN DTCM
    startupinfo=subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    subprocess.Popen(cmnd, startupinfo=startupinfo)
    sleep(1.25)

    with open('datcom.out', 'r') as results: # ---------------- READ
        results_lines = results.readlines()
        results_words = []
        results.close()

        for i in range (0, len(results_lines)):
            results_words.append(results_lines[i].split())

        global prv_lift_coef
        global prv_drag_coef
        for iR_row in range(0, len(results_words)):
            for iR_col in range(0, len(results_words[iR_row])):
                if results_words[iR_row][iR_col] == "CL" :
                    iR1r=iR_row
                    iR1c=iR_col
                    prv_lift_coef=float(results_words[iR1r+2][iR1c-1])*10/wing_area
                    
                if results_words[iR_row][iR_col] == "CD" :
                    iR2r=iR_row
                    iR2c=iR_col
                    prv_drag_coef=float(results_words[iR2r+2][iR2c-1])*10/wing_area

    with open('for005.dat','r') as file: # ---------------- READ
        file_lines = file.readlines()
        file_words=[]
        file.close()
        for i in range (0, len(file_lines)):
            file_words.append(file_lines[i].split())

        for i_row in range(0, len(file_words)):
            for i_col in range(0, len(file_words[i_row])):
                if file_words[i_row][i_col][:6] == "NALPHA" :
                    i1r=i_row
                    i1c=i_col
                    
        for i_row in range(0, len(file_words)):
            for i_col in range(0, len(file_words[i_row])):
                if file_words[i_row][i_col][:9] == "ALSCHD(1)" :
                    i2r=i_row
                    i2c=i_col

        index=file_words[i1r][i1c].index("=")+1
        file_words[i1r][i1c]=file_words[i1r][i1c][:index]+"1.0,"
        newline= ' '.join(file_words[i1r])+ '\n'
        file_lines[i1r]=" "+newline

        index=file_words[i2r][i2c].index("=")+1
        file_words[i2r][i2c]=file_words[i2r][i2c][:index]+str(alpha)+','
        del file_words[i2r][i2c+1]
        newline= ' '.join(file_words[i2r])+ '\n'
        file_lines[i2r]=" "+newline

    with open('for005.dat', 'w') as file_w: # ---------------- WRT
        file_w.writelines(file_lines)
        file_w.close()
        file.close()
    #breakpoint()    
##    x=(prv_lift_coef, lift_coef)  # ----- WRITE RESULTS
##    y=((alpha-1),alpha)
##    f=interpolate.interp1d(x,y)
##    x1=rCL
##    y1=f(x1)
##    y=(prv_drag_coef, drag_coef)
##    f=interpolate.interp1d(x,y)
##    y2=f(x1)
##    print("Optimized CD="+str(y2)+"\n")
##    print("Optimized CL="+str(rCL))

    
    if i_inp==0:    
        y=opt_scores
        x=range(0,len(y))
    if i_inp==1:    
        y1=opt_scores
        x1=range(0,len(y1))
    if i_inp==2:    
        y2=opt_scores
        x2=range(0,len(y2)) 
    if i_inp==3:    
        y3=opt_scores
        x3=range(0,len(y3))
    if i_inp==4:    
        y4=opt_scores
        x4=range(0,len(y4))
    if i_inp==5:    
        y5=opt_scores
        x5=range(0,len(y5))

    total_opt_values.append(opt_values)
    latest_score.append(opt_scores[len(opt_scores)-1])

plt.show() 
min_index=latest_score.index(min(latest_score))
print("---------------")
print("---------------")
print("---------------")
print("---------------")
print("---------------")
print("---------------")
print("---------------")
print("---------------")
opt_values=total_opt_values[min_index]
    
print ("\n"+"Alpha="+str(opt_values[0]*10)+"\n")
print("W Inner sweep angle="+str(opt_values[1]*1000)+"\n")
##print("W Outer sweep angle="+str(opt_values[2]*1000)+"\n")
print("W Span="+str(opt_values[2]*100)+"\n")
##print("W Breakpoint Span="+str(opt_values[4]*100)+"\n")
print("W Inner dihedral angle="+str(opt_values[3]*100)+"\n")
##print("W Outer dihedral angle="+str(opt_values[6]*100)+"\n")
print("W Twist angle="+str(opt_values[4]*100)+"\n")
print("W Root chord length="+str(opt_values[5]*100)+"\n")
##print("W Breakpoint chord length="+str(opt_values[9]*100)+"\n")
print("W Tip chord length="+str(opt_values[6]*100)+"\n")

print("VT inner sweep angle="+str(opt_values[7]*1000)+"\n")
##print("VT Outer sweep angle="+str(opt_values[12]*1000)+"\n")
print("VT Span="+str(opt_values[8]*100)+"\n")
##print("VT Breakpoint Span="+str(opt_values[14]*100)+"\n")
print("VT Inner dihedral angle="+str(opt_values[9]*100)+"\n")
##print("VT Outer dihedral angle="+str(opt_values[16]*100)+"\n")
print("VT Twist angle="+str(opt_values[10]*100)+"\n")
print("VT Root chord length="+str(opt_values[11]*100)+"\n")
##print("VT Breakpoint chord length="+str(opt_values[19]*100)+"\n")
print("VT Tip chord length="+str(opt_values[12]*100)+"\n")

print("HT inner sweep angle="+str(opt_values[13]*1000)+"\n")
##print("HT Outer sweep angle="+str(opt_values[22]*1000)+"\n")
print("HT Span="+str(opt_values[14]*100)+"\n")
##print("HT Breakpoint Span="+str(opt_values[24]*100)+"\n")
print("HT Inner dihedral angle="+str(opt_values[15]*100)+"\n")
##print("HT Outer dihedral angle="+str(opt_values[26]*100)+"\n")
print("HT Twist angle="+str(opt_values[16]*100)+"\n")
print("HT Root chord length="+str(opt_values[17]*100)+"\n")
##print("HT Breakpoint chord length="+str(opt_values[29]*100)+"\n")
print("HT Tip chord length="+str(opt_values[18]*100)+"\n")



for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:6] == "ALSCHD" :
            iAr=i_row
            iAc=i_col

iA=opt_values[0]*10
iA1=float(iA)
index=test005r_words[iAr][iAc].index("=")+1
test005r_words[iAr][iAc]=test005r_words[iAr][iAc][:index]+str(iA1)[:6]+","
newline= ' '.join(test005r_words[iAr])+ '\n'
test005r_lines[iAr]=" "+newline

for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:6] == "ALSCHD" :
            iAlr=i_row
            iAlc=i_col

for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:2] == "XV" :
            ixVTr=i_row
            ixVTc=i_col

for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:2] == "ZV" :
            izVTr=i_row
            izVTc=i_col

for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:2] == "XH" :
            ixHTr=i_row
            ixHTc=i_col

for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:2] == "ZH" :
            izHTr=i_row
            izHTc=i_col


i1r=[]
i1c=[]
for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:5] == "SAVSI" :
            i1r.append(i_row)
            i1c.append(i_col)

i2r=[]
i2c=[]
for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:5] == "SAVSO" :
            i2r.append(i_row)
            i2c.append(i_col)
i3r=[]
i3c=[]
for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:5] == "SSPN=" :
            i3r.append(i_row)
            i3c.append(i_col)
i4r=[]
i4c=[]
for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:6] == "SSPNOP" :
            i4r.append(i_row)
            i4c.append(i_col)
i5r=[]
i5c=[]
for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:5] == "SSPNE" :
            i5r.append(i_row)
            i5c.append(i_col)
i6r=[]
i6c=[]
for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:6] == "DHDADI" :
            i6r.append(i_row)
            i6c.append(i_col)
i7r=[]
i7c=[]
for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:6] == "DHDADO" :
            i7r.append(i_row)
            i7c.append(i_col)
i8r=[]
i8c=[]
for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:6] == "TWISTA" :
            i8r.append(i_row)
            i8c.append(i_col)
i9r=[]
i9c=[]
for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:5] == "CHRDR" :
            i9r.append(i_row)
            i9c.append(i_col)
i10r=[]
i10c=[]
for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:6] == "CHRDBP" :
            i10r.append(i_row)
            i10c.append(i_col)
i11r=[]
i11c=[]
for i_row in range(0, len(test005r_words)):
    for i_col in range(0, len(test005r_words[i_row])):
        if test005r_words[i_row][i_col][:6] == "CHRDTP" :
            i11r.append(i_row)
            i11c.append(i_col)

for i in range(0,len(opt_values)):
    if opt_values[i]<0.001 and opt_values[i]>-0.001:
        opt_values[i]=int(0)
    else:
        opt_values[i]==opt_values[i]

for j in range(0,3): 
    if j==0:
        s=str(opt_values[1]*1000)
        index=test005r_words[i1r[j]][i1c[j]].index("=")+1
        test005r_words[i1r[j]][i1c[j]]=test005r_words[i1r[j]][i1c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i1r[j]])+ '\n'
        test005r_lines[i1r[j]]=" "+newline

        s=str(opt_values[2]*1000)
        index=test005r_words[i2r[j]][i2c[j]].index("=")+1
        test005r_words[i2r[j]][i2c[j]]=test005r_words[i2r[j]][i2c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i2r[j]])+ '\n'
        test005r_lines[i2r[j]]=" "+newline

        s=str(opt_values[3]*100)
        index=test005r_words[i3r[j]][i3c[j]].index("=")+1
        test005r_words[i3r[j]][i3c[j]]=test005r_words[i3r[j]][i3c[j]][:index]+s[:5]+", "
        newline= ' '.join(test005r_words[i3r[j]])+ '\n'
        test005r_lines[i3r[j]]=" "+newline

        s=str(opt_values[4]*100)
        index=test005r_words[i4r[j]][i4c[j]].index("=")+1
        test005r_words[i4r[j]][i4c[j]]=test005r_words[i4r[j]][i4c[j]][:index]+s[:5]+","
        newline= ' '.join(test005r_words[i4r[j]])+ '\n'
        test005r_lines[i4r[j]]=" "+newline   

        s=str((opt_values[3]*100)-1.3462)
        index=test005r_words[i5r[j]][i5c[j]].index("=")+1
        test005r_words[i5r[j]][i5c[j]]=test005r_words[i5r[j]][i5c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i5r[j]])+ '\n'
        test005r_lines[i5r[j]]=" "+newline

        s=str(opt_values[5]*100)
        index=test005r_words[i6r[j]][i6c[j]].index("=")+1
        test005r_words[i6r[j]][i6c[j]]=test005r_words[i6r[j]][i6c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i6r[j]])+ '\n'
        test005r_lines[i6r[j]]=" "+newline

        s=str(opt_values[6]*100)
        index=test005r_words[i7r[j]][i7c[j]].index("=")+1
        test005r_words[i7r[j]][i7c[j]]=test005r_words[i7r[j]][i7c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i7r[j]])+ '\n'
        test005r_lines[i7r[j]]=" "+newline

        s=str(opt_values[7]*100)
        index=test005r_words[i8r[j]][i8c[j]].index("=")+1
        test005r_words[i8r[j]][i8c[j]]=test005r_words[i8r[j]][i8c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i8r[j]])+ '\n'
        test005r_lines[i8r[j]]=" "+newline

        s=str(opt_values[8]*100)
        index=test005r_words[i9r[j]][i9c[j]].index("=")+1
        test005r_words[i9r[j]][i9c[j]]=test005r_words[i9r[j]][i9c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i9r[j]])+ '\n'
        test005r_lines[i9r[j]]=" "+newline

        s=str(opt_values[9]*100)
        index=test005r_words[i10r[j]][i10c[j]].index("=")+1
        test005r_words[i10r[j]][i10c[j]]=test005r_words[i10r[j]][i10c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i10r[j]])+ '\n'
        test005r_lines[i10r[j]]=" "+newline

        s=str(opt_values[10]*100)
        index=test005r_words[i11r[j]][i11c[j]].index("=")+1
        test005r_words[i11r[j]][i11c[j]]=test005r_words[i11r[j]][i11c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i11r[j]])+ '\n'
        test005r_lines[i11r[j]]=" "+newline

    if j==1:
           
        s=str(opt_values[11]*1000)
        index=test005r_words[i1r[j]][i1c[j]].index("=")+1
        test005r_words[i1r[j]][i1c[j]]=test005r_words[i1r[j]][i1c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i1r[j]])+ '\n'
        test005r_lines[i1r[j]]=" "+newline

        index1=test005r_words[ixVTr][ixVTc].index("=")+1
        index2=test005r_words[ixVTr][ixVTc].index(",")
        index3=test005r_words[ixHTr][ixHTc].index("=")+1
        index4=test005r_words[ixHTr][ixHTc].index(",")
        vertical_angle=opt_values[11]*1000*math.pi/180
        new_XH=str((math.tan(vertical_angle)*((opt_values[31]*100)-(ZV)))+float(test005r_words[ixVTr][ixVTc][index1:index2]))

        test005r_words[ixHTr][ixHTc]=test005r_words[ixHTr][ixHTc][:index3]+new_XH[:6]+", "
        newline= ' '.join(test005r_words[ixHTr])+ '\n'
        test005r_lines[ixHTr]=" "+newline

        s=str(opt_values[12]*1000)
        index=test005r_words[i2r[j]][i2c[j]].index("=")+1
        test005r_words[i2r[j]][i2c[j]]=test005r_words[i2r[j]][i2c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i2r[j]])+ '\n'
        test005r_lines[i2r[j]]=" "+newline

        s=str(opt_values[13]*100)
        index=test005r_words[i3r[j]][i3c[j]].index("=")+1
        test005r_words[i3r[j]][i3c[j]]=test005r_words[i3r[j]][i3c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i3r[j]])+ '\n'
        test005r_lines[i3r[j]]=" "+newline

        s=str(opt_values[14]*100)
        index=test005r_words[i4r[j]][i4c[j]].index("=")+1
        test005r_words[i4r[j]][i4c[j]]=test005r_words[i4r[j]][i4c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i4r[j]])+ '\n'
        test005r_lines[i4r[j]]=" "+newline

        s=str((opt_values[13]*100)-0.9102)
        index=test005r_words[i5r[j]][i5c[j]].index("=")+1
        test005r_words[i5r[j]][i5c[j]]=test005r_words[i5r[j]][i5c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i5r[j]])+ '\n'
        test005r_lines[i5r[j]]=" "+newline

        s=str(opt_values[15]*100)
        index=test005r_words[i6r[j]][i6c[j]].index("=")+1
        test005r_words[i6r[j]][i6c[j]]=test005r_words[i6r[j]][i6c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i6r[j]])+ '\n'
        test005r_lines[i6r[j]]=" "+newline

        s=str(opt_values[16]*100)
        index=test005r_words[i7r[j]][i7c[j]].index("=")+1
        test005r_words[i7r[j]][i7c[j]]=test005r_words[i7r[j]][i7c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i7r[j]])+ '\n'
        test005r_lines[i7r[j]]=" "+newline

        s=str(opt_values[17]*100)
        index=test005r_words[i8r[j]][i8c[j]].index("=")+1
        test005r_words[i8r[j]][i8c[j]]=test005r_words[i8r[j]][i8c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i8r[j]])+ '\n'
        test005r_lines[i8r[j]]=" "+newline

        s=str(opt_values[18]*100)
        index=test005r_words[i9r[j]][i9c[j]].index("=")+1
        test005r_words[i9r[j]][i9c[j]]=test005r_words[i9r[j]][i9c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i9r[j]])+ '\n'
        test005r_lines[i9r[j]]=" "+newline

        s=str(opt_values[19]*100)
        index=test005r_words[i10r[j]][i10c[j]].index("=")+1
        test005r_words[i10r[j]][i10c[j]]=test005r_words[i10r[j]][i10c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i10r[j]])+ '\n'
        test005r_lines[i10r[j]]=" "+newline
              
        s=str(opt_values[20]*100)
        index=test005r_words[i11r[j]][i11c[j]].index("=")+1
        test005r_words[i11r[j]][i11c[j]]=test005r_words[i11r[j]][i11c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i11r[j]])+ '\n'
        test005r_lines[i11r[j]]=" "+newline

    if j==2:

        s=str(opt_values[21]*1000)
        index=test005r_words[i1r[j]][i1c[j]].index("=")+1
        test005r_words[i1r[j]][i1c[j]]=test005r_words[i1r[j]][i1c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i1r[j]])+ '\n'
        test005r_lines[i1r[j]]=" "+newline       

        s=str(opt_values[22]*1000)
        index=test005r_words[i2r[j]][i2c[j]].index("=")+1
        test005r_words[i2r[j]][i2c[j]]=test005r_words[i2r[j]][i2c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i2r[j]])+ '\n'
        test005r_lines[i2r[j]]=" "+newline

        s=str(opt_values[23]*100)
        index=test005r_words[i3r[j]][i3c[j]].index("=")+1
        test005r_words[i3r[j]][i3c[j]]=test005r_words[i3r[j]][i3c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i3r[j]])+ '\n'
        test005r_lines[i3r[j]]=" "+newline

        s=str(opt_values[24]*100)
        index=test005r_words[i4r[j]][i4c[j]].index("=")+1
        test005r_words[i4r[j]][i4c[j]]=test005r_words[i4r[j]][i4c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i4r[j]])+ '\n'
        test005r_lines[i4r[j]]=" "+newline

        s=str((opt_values[23]*100)-0.6638)
        index=test005r_words[i5r[j]][i5c[j]].index("=")+1
        test005r_words[i5r[j]][i5c[j]]=test005r_words[i5r[j]][i5c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i5r[j]])+ '\n'
        test005r_lines[i5r[j]]=" "+newline

        s=str(opt_values[25]*100)
        index=test005r_words[i6r[j]][i6c[j]].index("=")+1
        test005r_words[i6r[j]][i6c[j]]=test005r_words[i6r[j]][i6c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i6r[j]])+ '\n'
        test005r_lines[i6r[j]]=" "+newline

        s=str(opt_values[26]*100)
        index=test005r_words[i7r[j]][i7c[j]].index("=")+1
        test005r_words[i7r[j]][i7c[j]]=test005r_words[i7r[j]][i7c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i7r[j]])+ '\n'
        test005r_lines[i7r[j]]=" "+newline

        s=str(opt_values[27]*100)
        index=test005r_words[i8r[j]][i8c[j]].index("=")+1
        test005r_words[i8r[j]][i8c[j]]=test005r_words[i8r[j]][i8c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i8r[j]])+ '\n'
        test005r_lines[i8r[j]]=" "+newline

        s=str(opt_values[28]*100)
        index=test005r_words[i9r[j]][i9c[j]].index("=")+1
        test005r_words[i9r[j]][i9c[j]]=test005r_words[i9r[j]][i9c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i9r[j]])+ '\n'
        test005r_lines[i9r[j]]=" "+newline

        s=str(opt_values[29]*100)
        index=test005r_words[i10r[j]][i10c[j]].index("=")+1
        test005r_words[i10r[j]][i10c[j]]=test005r_words[i10r[j]][i10c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i10r[j]])+ '\n'
        test005r_lines[i10r[j]]=" "+newline
              
        s=str(opt_values[30]*100)
        index=test005r_words[i11r[j]][i11c[j]].index("=")+1
        test005r_words[i11r[j]][i11c[j]]=test005r_words[i11r[j]][i11c[j]][:index]+s[:6]+","
        newline= ' '.join(test005r_words[i11r[j]])+ '\n'
        test005r_lines[i11r[j]]=" "+newline

        index1=test005r_words[izVTr][izVTc].index("=")+1
        index2=test005r_words[izVTr][izVTc].index(",")
        index3=test005r_words[izHTr][izHTc].index("=")+1
        index4=test005r_words[izHTr][izHTc].index(",")
        new_ZH=str(opt_values[31]*100)
        test005r_words[izHTr][izHTc]=test005r_words[izHTr][izHTc][:index3]+new_ZH[:6]+",$"
        newline= ' '.join(test005r_words[izHTr])+ '\n'
        test005r_lines[izHTr]=" "+newline

with open('for005.dat', 'w') as test005:
    test005.writelines(test005r_lines)
    test005.close()
