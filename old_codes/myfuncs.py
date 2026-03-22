def findDatcomIdx(fileName):
    test005r = open('for005.dat', 'r')
    test005r_lines = test005r.readlines()
    test005r_words = []

    for i in range (0, len(test005r_lines)):
       test005r_words.append(test005r_lines[i].split())
 
    i1r=[]
    i1c=[]
    i2r=[]
    i2c=[]
    i3r=[]
    i3c=[]
    i4r=[]
    i4c=[]
    i5r=[]
    i5c=[]
    i6r=[]
    i6c=[]
    i7r=[]
    i7c=[]
    i8r=[]
    i8c=[]
    i9r=[]
    i9c=[]
    i10r=[]
    i10c=[]
    i11r=[]
    i11c=[]
    iTotalr = []
    iTotalc = []
    iTotalHeader = []
    for i_row in range(0, len(test005r_words)):
        for i_col in range(0, len(test005r_words[i_row])):

            if test005r_words[i_row][i_col][:6] == "ALSCHD" :
                iAlr=i_row
                iAlc=i_col
                iTotalr.append(iAlr)
                iTotalc.append(iAlc)
                iTotalHeader.append("iAl")
            if test005r_words[i_row][i_col][:2] == "XV" :
                ixVTr=i_row
                ixVTc=i_col
                iTotalr.append(ixVTr)
                iTotalc.append(ixVTc)
                iTotalHeader.append("ixVT")
            if test005r_words[i_row][i_col][:2] == "ZV" :
                izVTr=i_row
                izVTc=i_col
                iTotalr.append(izVTr)
                iTotalc.append(izVTc)
                iTotalHeader.append("izVT")
            if test005r_words[i_row][i_col][:2] == "XH" :
                ixHTr=i_row
                ixHTc=i_col
                iTotalr.append(ixHTr)
                iTotalc.append(ixHTc)
                iTotalHeader.append("ixHT")
            if test005r_words[i_row][i_col][:2] == "ZH" :
                izHTr=i_row
                izHTc=i_col
                iTotalr.append(izHTr)
                iTotalc.append(izHTc)
                iTotalHeader.append("izHT")
            if test005r_words[i_row][i_col][:5] == "SAVSI" :
                i1r.append(i_row)
                i1c.append(i_col)
            if test005r_words[i_row][i_col][:5] == "SAVSO" :
                i2r.append(i_row)
                i2c.append(i_col)
            if test005r_words[i_row][i_col][:5] == "SSPN=" :
                i3r.append(i_row)
                i3c.append(i_col)
            if test005r_words[i_row][i_col][:6] == "SSPNOP" :
                i4r.append(i_row)
                i4c.append(i_col)
            if test005r_words[i_row][i_col][:5] == "SSPNE" :
                i5r.append(i_row)
                i5c.append(i_col)
            if test005r_words[i_row][i_col][:6] == "DHDADI" :
                i6r.append(i_row)
                i6c.append(i_col)
            if test005r_words[i_row][i_col][:6] == "DHDADO" :
                i7r.append(i_row)
                i7c.append(i_col)
            if test005r_words[i_row][i_col][:6] == "TWISTA" :
                i8r.append(i_row)
                i8c.append(i_col)
            if test005r_words[i_row][i_col][:5] == "CHRDR" :
                i9r.append(i_row)
                i9c.append(i_col)
            if test005r_words[i_row][i_col][:6] == "CHRDBP" :
                i10r.append(i_row)
                i10c.append(i_col)
            if test005r_words[i_row][i_col][:6] == "CHRDTP" :
                i11r.append(i_row)
                i11c.append(i_col)
            if test005r_words[i_row][i_col][:4] == "SREF" :
                iSR_row=i_row
                iSR_col=i_col
                iTotalr.append(iSR_row)
                iTotalc.append(iSR_col)
                iTotalHeader.append("iSR")

    index1=test005r_words[izVTr][izVTc].index("=")+1
    index2=test005r_words[izVTr][izVTc].index(",")
    ZV=float(test005r_words[izVTr][izVTc][index1:index2])

    for i_row in range(0, len(test005r_words)):
        for i_col in range(0, len(test005r_words[i_row])):
            if test005r_words[i_row][i_col][:2] == "WT" :
                iWr=i_row
                iWc=i_col  

    index=test005r_words[iWr][iWc].index("=")+1
    test005r_words[iWr][iWc]=test005r_words[iWr][iWc][index:]
    index=test005r_words[iWr][iWc].index(",")
    test005r_words[iWr][iWc]=test005r_words[iWr][iWc][:index]
    weight=float(test005r_words[iWr][iWc])

    for i_total in range(1,12):
        varName = f"i{i_total}"
        varValueRow = locals()[varName+"r"]
        varValueCol = locals()[varName+"c"]
        iTotalr.append(varValueRow)
        iTotalc.append(varValueCol)
        iTotalHeader.append(varName) 
    return ZV, iTotalHeader, iTotalc, iTotalr, test005r_words, test005r_lines, weight

def createBounds(ZV):
    inp=[]

    # Wing Parameters
    inp.append((0.04))      #INP[1]=SAVSI   - Inner sweep angle
    inp.append((0.04))     #INP[2]=SAVSO   - Outer sweep angle
    inp.append((0.04572))    #INP[3]=SSPN    - Span
    inp.append((0.032258))    #INP[4]=SSPNOP  - Breakpoint span
    inp.append((0.0))      #INP[5]=DHDADI  - Inner dihedral angle
    inp.append((0.0))      #INP[6]=DHDADO  - Outer dihedral angle
    inp.append((-0.032))      #INP[7]=TWISTA  - Twist angle
    inp.append((0.04965))      #INP[8]=CHRDR   - Root chord
    inp.append((0.0129))      #INP[9]=CHRDBP  - Breakpoint chord
    inp.append((0.0129))     #INP[10]=CHRDBP - Tip chord

    #Vertical Tail Parameters
    inp.append((0.0475))       #INP[11]=SAVSI  - Inner sweep angle
    inp.append((0.0475))       #INP[12]=SAVSO  - Outer sweep angle
    inp.append((0.0319))    #INP[13]=SSPN   - Span
    inp.append((0.0256))    #INP[14]=SSPNOP - Breakpoint span
    inp.append((0.00))      #INP[15]=DHDADI - Inner dihedral angle
    inp.append((0.00))      #INP[16]=DHDADO - Outer dihedral angle
    inp.append((0.00))      #INP[17]=TWISTA - Twist angle
    inp.append((0.0308))    #INP[18]=CHRDR  - Root chord
    inp.append((0.0120))     #INP[19]=CHRDBP - Breakpoint chord
    inp.append((0.0120))    #INP[20]=CHRDBP - Tip chord

    # Horizontal Tail Parameters
    inp.append((0.04))       #INP[21]=SAVSI  - Inner sweep angle
    inp.append((0.04))       #INP[22]=SAVSO  - Outer sweep angle
    inp.append((0.02808))       #INP[23]=SSPN   - Span
    inp.append((0.01768))       #INP[24]=SSPNOP - Breakpoint span
    inp.append((-0.01))      #INP[25]=DHDADI - Inner dihedral angle
    inp.append((-0.01))      #INP[26]=DHDADO - Outer dihedral angle
    inp.append((0.00))       #INP[27]=TWISTA - Twist angle
    inp.append((0.0332))     #INP[28]=CHRDR  - Root chord
    inp.append((0.009497))      #INP[29]=CHRDBP - Breakpoint chord
    inp.append((0.009497))      #INP[30]=CHRDBP - Tip chord
    inp.append((0.00366))     #INP[31]=ZH - Horizontal tail Z-Coordinate

    b=[]

    # Wing parameters
    b.append((0.03,0.05))   #Inner sweep angle
    b.append((0.03,0.05))   #Outer sweep angle
    b.append((0.040,0.055))   #Span
    b.append((0.032,0.033)) #Breakpoint span
    b.append((0.0,0.06))    #Inner dihedral angle
    b.append((0.0,0.05))    #Outer dihedral angle
    b.append((-0.04,0.03))  #Twist angle
    b.append((0.046,0.051))   #Root chord
    b.append((inp[10],inp[8]))   #Breakpoint chord
    b.append((0.01,0.02))   #Tip chord

    #Vertical Tail Parameters
    b.append((0.055,0.055))   #Inner sweep angle
    b.append((0.03,0.058))   #Outer sweep angle
    b.append((0.03,0.04))   #Span
    b.append((0.017,0.018))   #Breakpoint span
    b.append((0.0,0.001))    #Inner dihedral angle
    b.append((0.0,0.001))    #Outer dihedral angle
    b.append((-0.04,0.04))  #Twist angle
    b.append((0.03,0.04))   #Root chord
    b.append((inp[20],inp[18]))   #Breakpoint chord
    b.append((0.01,0.02))   #Tip chord

    # Horizontal Tail Parameters
    b.append((0.03,0.05))   #Inner sweep angle
    b.append((0.03,0.05))   #Outer sweep angle
    b.append((0.025,0.032))   #Span
    b.append((0.0176,0.0178))   #Breakpoint span
    b.append((-0.04,0.00))    #Inner dihedral angle
    b.append((-0.04,0.00))    #Outer dihedral angle
    b.append((-0.02,0.02))  #Twist angle
    b.append((0.03,0.04))   #Root chord
    b.append((inp[30],inp[28]))   #Breakpoint chord
    b.append((0.008,0.015))   #Tip chord
    b.append((0.00365,0.00367))   #ZH-Horizontal tail Z-Coordinate
    return inp, b

def optimization(i_inp, inp, b, ZV, iTotalHeader, iTotalc, iTotalr, test005r_words, test005r_lines, weight, opt_scores):
    def main_opt(inp):
        score = wing_optimization(inp, iTotalHeader, iTotalc, iTotalr, ZV, test005r_words, test005r_lines, weight, opt_scores)
        return score
    from scipy.optimize import fmin_slsqp
    if i_inp==0:
        opt_values=fmin_slsqp(main_opt,inp, bounds=b,epsilon=0.001) #!
    if i_inp==1:
        new_inp=[]
        new_inp.append(inp[0])
        for i in range(1,len(inp)):
            b_step=(b[i][1]-b[i][0])/5
            #print(float(str(b_step)[:6]))
            new_inp.append(float(str(b[i][0]+float(str(b_step)[:6]))[:5]))
        inp=new_inp
        opt_values=fmin_slsqp(main_opt,inp, bounds=b,epsilon=0.001) #!

    if i_inp==2:
        new_inp=[]
        new_inp.append(inp[0])
        for i in range(1,len(inp)):
            b_step=(b[i][1]-b[i][0])/5
            #print(float(str(b_step)[:6]))
            new_inp.append(float(str(b[i][0]+2*float(str(b_step)[:6]))[:5]))
        inp=new_inp
        opt_values=fmin_slsqp(main_opt, inp, bounds=b,epsilon=0.001) #!

    if i_inp==3:
        new_inp=[]
        new_inp.append(inp[0])
        for i in range(1,len(inp)):
            b_step=(b[i][1]-b[i][0])/5
            #print(float(str(b_step)[:6]))
            new_inp.append(float(str(b[i][0]+3*float(str(b_step)[:6]))[:5]))
        inp=new_inp
        opt_values=fmin_slsqp(main_opt, inp, bounds=b,epsilon=0.001) #!

    if i_inp==4:
        new_inp=[]
        new_inp.append((inp[0]))
        for i in range(1,len(inp)):
            b_step=(b[i][1]-b[i][0])/5
            #print(float(str(b_step)[:6]))
            new_inp.append(float(str(b[i][0]+4*float(str(b_step)[:6]))[:5]))
        inp=new_inp
        opt_values=fmin_slsqp(main_opt, inp, bounds=b,epsilon=0.001) #!

    if i_inp==5:
        new_inp=[]
        new_inp.append(inp[0])
        for i in range(1,len(inp)):
            b_step=(b[i][1]-b[i][0])/5
            #print(float(str(b_step)[:6]))
            new_inp.append(float(str(b[i][0]+4.5*float(str(b_step)[:6]))[:5]))
        inp=new_inp
        opt_values=fmin_slsqp(main_opt, inp, bounds=b,epsilon=0.001) #!

    return opt_values

def wing_optimization(inp, iTotalHeader, iTotalc, iTotalr, ZV, test005r_words, test005r_lines, weight, opt_scores):
        import math
        import subprocess
        from time import sleep
        global rCL
        global lift_coef
        global drag_coef
        global m_coef
        global wing_area
        global density
        global velocity
        global temperature

        for i_idx in range(0,len(iTotalHeader)):
            tempName = iTotalHeader[i_idx]
            tempResult = indexFinder(tempName, iTotalHeader, iTotalr, iTotalc)
            globals()[tempName +"r"] = tempResult[0]
            globals()[tempName +"c"] = tempResult[1]
        
        
        iAl=inp[0]*10
        iAl1=float(iAl)
        index=test005r_words[iAlr][iAlc].index("=")+1
        test005r_words[iAlr][iAlc]=test005r_words[iAlr][iAlc][:index]+str(iAl1)[:6]+","
        #print(test005r_words[8][2][:index])
        print(test005r_words[iAlr][iAlc])
        #breakpoint()
        newline= ' '.join(test005r_words[iAlr])+ '\n'
        test005r_lines[iAlr]=" "+newline

        for i in range(0,len(inp)):
           if inp[i]<0.001 and inp[i]>-0.001:
                 inp[i]=int(0)
           else:
                 inp[i]==inp[i]
                 
        for j in range(0,3):

           
           if j==0:
              s=str(inp[1]*1000)
              index=test005r_words[i1r[j]][i1c[j]].index("=")+1
              test005r_words[i1r[j]][i1c[j]]=test005r_words[i1r[j]][i1c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i1r[j]][i1c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i1r[j]])+ '\n'
              test005r_lines[i1r[j]]=" "+newline

              s=str(inp[2]*1000)
              index=test005r_words[i2r[j]][i2c[j]].index("=")+1
              test005r_words[i2r[j]][i2c[j]]=test005r_words[i2r[j]][i2c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i2r[j]][i2c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i2r[j]])+ '\n'
              test005r_lines[i2r[j]]=" "+newline

              s=str(inp[3]*100)
              index=test005r_words[i3r[j]][i3c[j]].index("=")+1
              test005r_words[i3r[j]][i3c[j]]=test005r_words[i3r[j]][i3c[j]][:index]+s[:5]+", "
              #print(test005r_words[8][2][:index])
              print(test005r_words[i3r[j]][i3c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i3r[j]])+ '\n'
              test005r_lines[i3r[j]]=" "+newline

              s=str(inp[4]*100)
              index=test005r_words[i4r[j]][i4c[j]].index("=")+1
              test005r_words[i4r[j]][i4c[j]]=test005r_words[i4r[j]][i4c[j]][:index]+s[:5]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i4r[j]][i4c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i4r[j]])+ '\n'
              test005r_lines[i4r[j]]=" "+newline   

    #SSPNE girdisi SSPN'den kanadın bulunduğu konumdaki gövdenin yarıçapından çıkarılarak elde edilir. 

              s=str((inp[3]*100)-1.3462)
              index=test005r_words[i5r[j]][i5c[j]].index("=")+1
              test005r_words[i5r[j]][i5c[j]]=test005r_words[i5r[j]][i5c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i5r[j]][i5c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i5r[j]])+ '\n'
              test005r_lines[i5r[j]]=" "+newline

              s=str(inp[5]*100)
              index=test005r_words[i6r[j]][i6c[j]].index("=")+1
              test005r_words[i6r[j]][i6c[j]]=test005r_words[i6r[j]][i6c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i6r[j]][i6c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i6r[j]])+ '\n'
              test005r_lines[i6r[j]]=" "+newline

              s=str(inp[6]*100)
              index=test005r_words[i7r[j]][i7c[j]].index("=")+1
              test005r_words[i7r[j]][i7c[j]]=test005r_words[i7r[j]][i7c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i7r[j]][i7c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i7r[j]])+ '\n'
              test005r_lines[i7r[j]]=" "+newline

              s=str(inp[7]*100)
              index=test005r_words[i8r[j]][i8c[j]].index("=")+1
              test005r_words[i8r[j]][i8c[j]]=test005r_words[i8r[j]][i8c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i8r[j]][i8c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i8r[j]])+ '\n'
              test005r_lines[i8r[j]]=" "+newline

              s=str(inp[8]*100)
              index=test005r_words[i9r[j]][i9c[j]].index("=")+1
              test005r_words[i9r[j]][i9c[j]]=test005r_words[i9r[j]][i9c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i9r[j]][i9c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i9r[j]])+ '\n'
              test005r_lines[i9r[j]]=" "+newline

              s=str(inp[9]*100)
              index=test005r_words[i10r[j]][i10c[j]].index("=")+1
              test005r_words[i10r[j]][i10c[j]]=test005r_words[i10r[j]][i10c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i10r[j]][i10c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i10r[j]])+ '\n'
              test005r_lines[i10r[j]]=" "+newline

              s=str(inp[10]*100)
              index=test005r_words[i11r[j]][i11c[j]].index("=")+1
              test005r_words[i11r[j]][i11c[j]]=test005r_words[i11r[j]][i11c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i11r[j]][i11c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i11r[j]])+ '\n'
              test005r_lines[i11r[j]]=" "+newline

           if j==1:
           
              s=str(inp[11]*1000)
              index=test005r_words[i1r[j]][i1c[j]].index("=")+1
              test005r_words[i1r[j]][i1c[j]]=test005r_words[i1r[j]][i1c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i1r[j]][i1c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i1r[j]])+ '\n'
              test005r_lines[i1r[j]]=" "+newline
              index1=test005r_words[ixVTr][ixVTc].index("=")+1
              index2=test005r_words[ixVTr][ixVTc].index(",")
              index3=test005r_words[ixHTr][ixHTc].index("=")+1
              index4=test005r_words[ixHTr][ixHTc].index(",")
              vertical_angle=inp[11]*1000*math.pi/180
              new_XH=str((math.tan(vertical_angle)*((inp[31]*100)-ZV))+float(test005r_words[ixVTr][ixVTc][index1:index2]))
              
              test005r_words[ixHTr][ixHTc]=test005r_words[ixHTr][ixHTc][:index3]+new_XH[:6]+","
              newline= ' '.join(test005r_words[ixHTr])+ '\n'
              test005r_lines[ixHTr]=" "+newline

              s=str(inp[12]*1000)
              index=test005r_words[i2r[j]][i2c[j]].index("=")+1
              test005r_words[i2r[j]][i2c[j]]=test005r_words[i2r[j]][i2c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i2r[j]][i2c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i2r[j]])+ '\n'
              test005r_lines[i2r[j]]=" "+newline

              s=str(inp[13]*100)
              index=test005r_words[i3r[j]][i3c[j]].index("=")+1
              test005r_words[i3r[j]][i3c[j]]=test005r_words[i3r[j]][i3c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i3r[j]][i3c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i3r[j]])+ '\n'
              test005r_lines[i3r[j]]=" "+newline

              s=str(inp[14]*100)
              index=test005r_words[i4r[j]][i4c[j]].index("=")+1
              test005r_words[i4r[j]][i4c[j]]=test005r_words[i4r[j]][i4c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i4r[j]][i4c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i4r[j]])+ '\n'
              test005r_lines[i4r[j]]=" "+newline

    #SSPNE girdisi SSPN'den kuyruğun bulunduğu konumdaki gövdenin yarıçapından çıkarılarak elde edilir. 

              s=str((inp[13]*100)-0.6638)
              index=test005r_words[i5r[j]][i5c[j]].index("=")+1
              test005r_words[i5r[j]][i5c[j]]=test005r_words[i5r[j]][i5c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i5r[j]][i5c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i5r[j]])+ '\n'
              test005r_lines[i5r[j]]=" "+newline

              s=str(inp[15]*100)
              index=test005r_words[i6r[j]][i6c[j]].index("=")+1
              test005r_words[i6r[j]][i6c[j]]=test005r_words[i6r[j]][i6c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i6r[j]][i6c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i6r[j]])+ '\n'
              test005r_lines[i6r[j]]=" "+newline

              s=str(inp[16]*100)
              index=test005r_words[i7r[j]][i7c[j]].index("=")+1
              test005r_words[i7r[j]][i7c[j]]=test005r_words[i7r[j]][i7c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i7r[j]][i7c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i7r[j]])+ '\n'
              test005r_lines[i7r[j]]=" "+newline

              s=str(inp[17]*100)
              index=test005r_words[i8r[j]][i8c[j]].index("=")+1
              test005r_words[i8r[j]][i8c[j]]=test005r_words[i8r[j]][i8c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i8r[j]][i8c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i8r[j]])+ '\n'
              test005r_lines[i8r[j]]=" "+newline

              s=str(inp[18]*100)
              index=test005r_words[i9r[j]][i9c[j]].index("=")+1
              test005r_words[i9r[j]][i9c[j]]=test005r_words[i9r[j]][i9c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i9r[j]][i9c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i9r[j]])+ '\n'
              test005r_lines[i9r[j]]=" "+newline

              s=str(inp[19]*100)
              index=test005r_words[i10r[j]][i10c[j]].index("=")+1
              test005r_words[i10r[j]][i10c[j]]=test005r_words[i10r[j]][i10c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i10r[j]][i10c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i10r[j]])+ '\n'
              test005r_lines[i10r[j]]=" "+newline
              
              s=str(inp[20]*100)
              index=test005r_words[i11r[j]][i11c[j]].index("=")+1
              test005r_words[i11r[j]][i11c[j]]=test005r_words[i11r[j]][i11c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i11r[j]][i11c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i11r[j]])+ '\n'
              test005r_lines[i11r[j]]=" "+newline

           if j==2:

              s=str(inp[21]*1000)
              index=test005r_words[i1r[j]][i1c[j]].index("=")+1
              test005r_words[i1r[j]][i1c[j]]=test005r_words[i1r[j]][i1c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i1r[j]][i1c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i1r[j]])+ '\n'
              test005r_lines[i1r[j]]=" "+newline       

              s=str(inp[22]*1000)
              index=test005r_words[i2r[j]][i2c[j]].index("=")+1
              test005r_words[i2r[j]][i2c[j]]=test005r_words[i2r[j]][i2c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i2r[j]][i2c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i2r[j]])+ '\n'
              test005r_lines[i2r[j]]=" "+newline

              s=str(inp[23]*100)
              index=test005r_words[i3r[j]][i3c[j]].index("=")+1
              test005r_words[i3r[j]][i3c[j]]=test005r_words[i3r[j]][i3c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i3r[j]][i3c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i3r[j]])+ '\n'
              test005r_lines[i3r[j]]=" "+newline

              s=str(inp[24]*100)
              index=test005r_words[i4r[j]][i4c[j]].index("=")+1
              test005r_words[i4r[j]][i4c[j]]=test005r_words[i4r[j]][i4c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i4r[j]][i4c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i4r[j]])+ '\n'
              test005r_lines[i4r[j]]=" "+newline

    #SSPNE girdisi SSPN'den kuyruğun bulunduğu konumdaki gövdenin yarıçapından çıkarılarak elde edilir. 

              s=str((inp[23]*100)-0.9102)
              index=test005r_words[i5r[j]][i5c[j]].index("=")+1
              test005r_words[i5r[j]][i5c[j]]=test005r_words[i5r[j]][i5c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i5r[j]][i5c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i5r[j]])+ '\n'
              test005r_lines[i5r[j]]=" "+newline

              s=str(inp[25]*100)
              index=test005r_words[i6r[j]][i6c[j]].index("=")+1
              test005r_words[i6r[j]][i6c[j]]=test005r_words[i6r[j]][i6c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i6r[j]][i6c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i6r[j]])+ '\n'
              test005r_lines[i6r[j]]=" "+newline

              s=str(inp[26]*100)
              index=test005r_words[i7r[j]][i7c[j]].index("=")+1
              test005r_words[i7r[j]][i7c[j]]=test005r_words[i7r[j]][i7c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i7r[j]][i7c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i7r[j]])+ '\n'
              test005r_lines[i7r[j]]=" "+newline

              s=str(inp[27]*100)
              index=test005r_words[i8r[j]][i8c[j]].index("=")+1
              test005r_words[i8r[j]][i8c[j]]=test005r_words[i8r[j]][i8c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i8r[j]][i8c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i8r[j]])+ '\n'
              test005r_lines[i8r[j]]=" "+newline

              s=str(inp[28]*100)
              index=test005r_words[i9r[j]][i9c[j]].index("=")+1
              test005r_words[i9r[j]][i9c[j]]=test005r_words[i9r[j]][i9c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i9r[j]][i9c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i9r[j]])+ '\n'
              test005r_lines[i9r[j]]=" "+newline

              s=str(inp[29]*100)
              index=test005r_words[i10r[j]][i10c[j]].index("=")+1
              test005r_words[i10r[j]][i10c[j]]=test005r_words[i10r[j]][i10c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i10r[j]][i10c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i10r[j]])+ '\n'
              test005r_lines[i10r[j]]=" "+newline
              
              s=str(inp[30]*100)
              index=test005r_words[i11r[j]][i11c[j]].index("=")+1
              test005r_words[i11r[j]][i11c[j]]=test005r_words[i11r[j]][i11c[j]][:index]+s[:6]+","
              #print(test005r_words[8][2][:index])
              print(test005r_words[i11r[j]][i11c[j]])
              #breakpoint()
              newline= ' '.join(test005r_words[i11r[j]])+ '\n'
              test005r_lines[i11r[j]]=" "+newline

              index1=test005r_words[izVTr][izVTc].index("=")+1
              index2=test005r_words[izVTr][izVTc].index(",")
              index3=test005r_words[izHTr][izHTc].index("=")+1
              index4=test005r_words[izHTr][izHTc].index(",")
              new_ZH=str(inp[31]*100)
              test005r_words[izHTr][izHTc]=test005r_words[izHTr][izHTc][:index3]+new_ZH[:6]+",$"
              newline= ' '.join(test005r_words[izHTr])+ '\n'
              test005r_lines[izHTr]=" "+newline

              
        with open('for005.dat', 'w') as test005:
          test005.writelines(test005r_lines)

        test005.close()

        cmnd = "digital_DATCOM.exe"
        startupinfo=subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        subprocess.Popen(cmnd, startupinfo=startupinfo)
        sleep(0.25)

        with open('datcom.out', 'r') as results:
         results_lines = results.readlines()
         results_words = []
         results.close() 
         for i in range (0, len(results_lines)):
          results_words.append(results_lines[i].split())

         iSr=[]
         iSc=[]
         for i_row in range(0, len(results_words)):
          for i_col in range(0, len(results_words[i_row])):
            if results_words[i_row][i_col][:11] == "THEORITICAL" :
                iSr.append(i_row)
                iSc.append(i_col)

         wing_area=float(results_words[iSr[0]+1][iSc[0]])

         for i_row in range(0, len(results_words)):
          for i_col in range(0, len(results_words[i_row])):
            if results_words[i_row][i_col][:8] == "VELOCITY" :
                iVr=i_row
                iVc=i_col
         velocity=float(results_words[iVr+3][iVc+1])
         pressure=float(results_words[iVr+3][iVc+2])
         temperature=float(results_words[iVr+3][iVc+3])
         density=float(pressure/(287.058*temperature))

         rCL=float(2*weight/(wing_area*density*velocity**2))
         
         for iR_row in range(0, len(results_words)):
          for iR_col in range(0, len(results_words[iR_row])):
            
             if results_words[iR_row][iR_col] == "CL" :
                iR1r=iR_row
                iR1c=iR_col
                lift_coef=float(results_words[iR1r+2][iR1c-1])*10/wing_area
                
            
             if results_words[iR_row][iR_col] == "CD" :
                iR2r=iR_row
                iR2c=iR_col
                drag_coef=float(results_words[iR2r+2][iR2c-1])*10/wing_area

##             if results_words[iR_row][iR_col] == "CMQ" :
##                iR3r=iR_row
##                iR3c=iR_col
##                m_coef=float(results_words[iR3r+2][iR3c-1])*1/wing_area
##
   
        iSR_row = iSRr
        iSR_col = iSRc
        s=str(1000.0)
        index=test005r_words[iSR_row][iSR_col].index("=")+1
        test005r_words[iSR_row][iSR_col]=test005r_words[iSR_row][iSR_col][:index]+s+",$"
        newline= ' '.join(test005r_words[iSR_row])+ '\n'
        test005r_lines[iSR_row]=" "+newline

        print("-------------")
        print(test005r_words[iSR_row][iSR_col])
        print("-------------")
        
        with open('for005.dat', 'w') as test005:
          test005.writelines(test005r_lines)

        test005.close()

        cmnd = "digital_DATCOM.exe"
        startupinfo=subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        subprocess.Popen(cmnd, startupinfo=startupinfo)
        sleep(0.25)

        with open('datcom.out', 'r') as results:
         results_lines = results.readlines()
         results_words = []
         results.close() 
         for i in range (0, len(results_lines)):
          results_words.append(results_lines[i].split())

         for iR_row in range(0, len(results_words)):
          for iR_col in range(0, len(results_words[iR_row])):
            
             if results_words[iR_row][iR_col] == "CM" :
                iR1r=iR_row
                iR1c=iR_col
                m_coef=float(results_words[iR1r+2][iR1c-1])*1000/wing_area
                print(m_coef)
        s=str(10.0)
        index=test005r_words[iSR_row][iSR_col].index("=")+1
        test005r_words[iSR_row][iSR_col]=test005r_words[iSR_row][iSR_col][:index]+s+",$"
        newline= ' '.join(test005r_words[iSR_row])+ '\n'
        test005r_lines[iSR_row]=" "+newline

        with open('for005.dat', 'w') as test005:
          test005.writelines(test005r_lines)

        test005.close()
        print("-------------")
        print(test005r_words[iSR_row][iSR_col])
        print("-------------")
        print("rCL="+str(rCL))
        if rCL<=lift_coef:                      
          score=((lift_coef+(5*drag_coef)+rCL+abs(m_coef)+(wing_area/1000)))
          print("Score="+str(score))
          opt_scores.append(score)
        else: 
          score=1000000
          opt_scores.append(score)
          print("Score="+str(score))
        return score

def indexFinder(word, iTotalHeader, iTotalr, iTotalc):
    indeks   = iTotalHeader.index(word)
    row = iTotalr[indeks]
    col = iTotalc[indeks]
    return row, col
