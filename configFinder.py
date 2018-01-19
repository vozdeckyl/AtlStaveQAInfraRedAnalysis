'''
configFinder.py

Author: William Heidorn, Iowa State University
About: This program takes a thermal image of an ATLAS Itk Stave Support, and
  finds the stave and produces 4 points that contain the stave

Requires: pyROOT, Python 2.7, OpenCV

'''

import numpy as np
import cv2
import ROOT

def FindPoints(strImageFile,strOutputFile,xPixels = 640,yPixels = 480,fltxPercentCutL=0.05,fltxPercentCutR=0.023,fltyPercentCut=0.17):
  """
  This function takes an input root stave image and finds all of the appropriate
  locations on the stave and creates a config file.
  """
  #Load in the file
  imageFile = ROOT.TFile(strImageFile,"read")
  Tree = imageFile.Get("atree")
  _temperature = np.zeros(1,dtype=float)
  Tree.SetBranchAddress("temperature",_temperature)

  #Load the image from TTree
  image = np.full((xPixels,yPixels),-999) #A tree full of -999 used as a placeholder
  for i in range(xPixels):
    for j in range(yPixels):
      Tree.GetEntry(i*yPixels + j)      #Reading from an average frame
      #!!!!Tree.GetEntry(j*xPixels + i) #Reading from a single frame
      image[i][j] = _temperature[0] 

  # Make The Canny Image
  v = np.median(image)

  sigma = 0.33
  lower = int(max(0,(1-sigma)*v))
  upper = int(min(255,(1+sigma)*v))

  laplacian = cv2.Canny(np.uint8(image),lower,upper)
  image2 = laplacian

  #Makes a Canny Image that can be checked
  histcanny = ROOT.TH2F("cannyplot","Canny Plot;xPixel;yPixel",xPixels,0,xPixels,yPixels,0,yPixels)
  orighist = ROOT.TH2F("originalplot","OriginalPlot;xPixel;yPixel",xPixels,0,xPixels,yPixels,0,yPixels)
  for i in range(xPixels):
    for j in range(yPixels):
      orighist.Fill(i,j,image[i][j])
      if image2[i][j] > 100:
        histcanny.Fill(i,j,image2[i][j])
      else:
        histcanny.Fill(i,j,0)
        image2[i][j] = 0 #Replace any small numbers with 0

  c2 = ROOT.TCanvas("c2")
  c2.cd()
  histcanny.Draw("colz")
  c2.Update()

  # Find the Four Corners of the Pipe Area

  c2.lines = []  #The lines stored in the canvas to show the buildup
  lineData = []  #This will be the four points
  HorData  = []  #The average y value of each horizontal line
  VertData = []  #The average x value of each vertical line
  ShortHorData = []

  orighist.Draw("colz")
 
#------------------------------------------------------------------------------
  try:
    #Find Long Horiz Lines
    findLongLines = cv2.HoughLinesP(image2,rho = 1,theta = 1*np.pi/1000,threshold = 100,minLineLength = 200,maxLineGap = 175)

    LengthHoriz = np.size(findLongLines)/4
    for line in range(int(LengthHoriz)):
      x1 = findLongLines[line,0][1]
      y1 = findLongLines[line,0][0]
      x2 = findLongLines[line,0][3]
      y2 = findLongLines[line,0][2]
      slope = abs((y2-y1)/(x2-x1+0.0001))
      intercept =y1-x1*(slope)

      HorData += [(y1+y2)/2]
      lineObj = ROOT.TLine(x1,y1,x2,y2)
      lineObj.SetLineColor(3)
      lineObj.SetLineWidth(3)
      c2.lines += [lineObj]
      lineObj.Draw()

    HorData = np.sort(HorData) 
    CentSep = np.amax(abs(HorData-240))
    while CentSep > 50:
      lenHor = np.size(HorData)
      if abs(HorData[0]-240)> 50:
        HorData = np.delete(HorData,0)
      else:
        HorData = np.delete(HorData,lenHor-1)
      CentSep = np.amax(abs(HorData-240))

    lineData += [np.amax(HorData)]
    lineData += [np.amin(HorData)]

    
  except:
    print("Failed to Find Long Lines")

#------------------------------------------------------------------------------   
#Find Short Vert Lines
  try:
    findShortLines = cv2.HoughLinesP(image2,rho = 1,theta = 1*np.pi/10000,threshold = 20,minLineLength = 10, maxLineGap = 5)

    LengthVert = np.size(findShortLines)/4
    for line in range(int(LengthVert)):
      x1 = findShortLines[line,0][1]
      y1 = findShortLines[line,0][0]
      x2 = findShortLines[line,0][3]
      y2 = findShortLines[line,0][2]
      slope = abs((y2-y1)/(x2-x1+0.0001))
      intercept = y1-x1*(slope)

      if slope > 1: #Since this fit will find many short line segments we want to remove all horiztal lines
        VertData += [(x1+x2)/2]
        lineObj = ROOT.TLine(x1,y1,x2,y2)
        lineObj.SetLineColor(2)
        lineObj.SetLineWidth(4)
        c2.lines += [lineObj]
        lineObj.Draw()

    VertData = np.sort(VertData)
    lineData += [np.amax(VertData)]
    
    #Check to remove finding the edge of the pipe protector
    VertSep = np.amax(VertData)-np.amin(VertData)
    if VertSep < 500:
      raise ValueError("Not all vertical lines were found!!!!")
    while VertSep > 550: #Seperation should be around 540 pixels
      VertData = np.delete(VertData,0) 
      VertSep = np.amax(VertData)-np.amin(VertData)
    lineData += [np.amin(VertData)]

    #Put the found area on the plot 
    for i in range(2):
      lineObj = ROOT.TLine(lineData[2],lineData[i],lineData[3],lineData[i])
      lineObj2 = ROOT.TLine(lineData[i+2],lineData[0],lineData[i+2],lineData[1])
      lineObj.SetLineColor(1)
      lineObj2.SetLineColor(1)
      lineObj.SetLineWidth(1)
      lineObj2.SetLineWidth(1)
      c2.lines += [lineObj]
      lineObj.Draw()
      c2.lines += [lineObj2]
      lineObj2.Draw()

    x0=lineData[3]
    x1=lineData[2]
    y0=lineData[1]
    y1=lineData[0]
    Dx = x1-x0 
    Dy = y1-y0
    
  except:
    print("Failed to find Short Vertical Lines")
    
#------------------------------------------------------------------------------
 
  #Print all of the Fit Lines
  c2.Update()
  c2.Print("AllFoundLines.png")
  c2.Print("AllFoundLines.root")

  #Get Corrected Zoomed Figure
  DxcutL = int(fltxPercentCutL*Dx)
  DxcutR = int(fltxPercentCutR*Dx)
  Dycut = int(fltyPercentCut*Dy)

  x0Cut = x0+DxcutL
  x1Cut = x1-DxcutR
  y0Cut = y0+Dycut
  y1Cut = y1-Dycut
 
  c2.Close()

  #Make the output file
  Output = open(strOutputFile,"w")
  Output.write("#\n# frame parameters used in frameanal.py\n#\n")

  #Find the EndofStaveCard
  avgStaveTemp = 0.0
  avgAboveTemp = 0.0
  avgBelowTemp = 0.0
  stavePixels = (x1Cut-x0Cut)*(y1Cut-y0Cut)
  EOSCardPixels = 300 
  for i in range(xPixels):
    for j in range(yPixels):
      if i > x0Cut and i < x1Cut:
        if j > y0Cut and j < y1Cut:
          avgStaveTemp = avgStaveTemp + image[i][j]
      if i > x0Cut and i < (x0Cut+30):
        if j > y1 and j < (y1+10):
          avgAboveTemp += image[i][j]
        if j > y0 - 10 and j < y0:
          avgBelowTemp += image[i][j] 
      
  avgStaveTemp = avgStaveTemp/stavePixels
  avgAboveTemp = avgAboveTemp/EOSCardPixels
  avgBelowTemp = avgBelowTemp/EOSCardPixels

  


  #Get Which Side from the Plot
  if avgStaveTemp > 20: 
    if avgAboveTemp > avgBelowTemp:
      intStaveSideL = 0
    else:
      intStaveSideL = 1
  else:
    if avgAboveTemp < avgBelowTemp:
      intStaveSideL = 0
    else:
      intStaveSideL = 1

  if intStaveSideL == 0:
    y0EOS = y0
    y1EOS = y1 + int((y1-y0)*0.4)
  else: 
    y0EOS = y0 - int((y1-y0)*0.4)
    y1EOS = y1 

  if intStaveSideL ==1:
    yorig = [y0EOS,y0Cut,y1EOS,y1Cut]
    y0EOS = abs(yorig[2] - yPixels) 
    y0Cut = abs(yorig[3] - yPixels)
    y1EOS = abs(yorig[0] - yPixels)
    y1Cut = abs(yorig[1] - yPixels)

  #Put in the stave parameters
  Output.write("StavePixelX0 "+str(x0)+"\n")
  Output.write("StavePixelY0 "+str(y0EOS)+"\n")
  Output.write("StavePixelX1 "+str(x1)+"\n")
  Output.write("StavePixelY1 "+str(y1EOS)+"\n")

  #Put in the pipe area parameters
  Output.write("PipePixelX0 "+str(x0Cut)+"\n")
  Output.write("PipePixelY0 "+str(y0Cut)+"\n")
  Output.write("PipePixelX1 "+str(x1Cut)+"\n")
  Output.write("PipePixelY1 "+str(y1Cut)+"\n")

  #Put in the Other Constants
  Output.write("CMperPixel 0.23272727\n")
  Output.write("StaveSideL "+str(intStaveSideL)+"\n")    
  
  #State Whether it is hot or cold
  if avgStaveTemp > 20.:
    intLowTValue = 0
    #Assuming Run at 50C
    intMaxPlotTemp  = 50
    intMinPlotTemp  = 10
    intMaxStaveTemp = 50
    intMinStaveTemp = 25
    intMaxPipeTemp  = 50
    intMinPipeTemp  = 40

  else:
    intLowTValue = 1
    #Assuming Run at -55C
    intMaxPlotTemp  = 20
    intMinPlotTemp  = -40
    intMaxStaveTemp = -10
    intMinStaveTemp = -40
    intMaxPipeTemp  = -20
    intMinPipeTemp  = -40
  Output.write("LiquidTLow "+str(intLowTValue)+"\n")

  #From Temp Values
  Output.write("FrameTmax "+str(intMaxPlotTemp)+"\n")
  Output.write("FrameTmin "+str(intMinPlotTemp)+"\n")
  Output.write("StaveTmax "+str(intMaxStaveTemp)+"\n")
  Output.write("StaveTmin "+str(intMinStaveTemp)+"\n")
  Output.write("PipeTmax "+str(intMaxPipeTemp)+"\n")
  Output.write("PipeTmin "+str(intMinPipeTemp)+"\n")

  Output.close()

'''
if __name__ == '__main__':
  FindPoints("roo/frame_average.root","configure") 

'''





