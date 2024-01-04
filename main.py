import cv2
import numpy as np
import ezdxf 
import os
import sys
import pyemf3 as pyemf
import tk_tools as tk
import tkinter.filedialog as fd


class Outliner: 
    def __init__(self, filePath) :
        self.filePath = filePath 
       
        
    def importImage(self):
        image = cv2.imread(self.filePath)
        return image

            
    def getFileName(self):
        fileName = os.path.basename(self.filePath)
        names = fileName.split(".")
        fileName = names[0]
        return fileName

    def removeBackground(self, image):
       # image= cv2.imread(self.filePath)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret,baseline = cv2.threshold(gray,127,255,cv2.THRESH_TRUNC)
        im_floodfill = baseline.copy()
        h,w = baseline.shape[:2]
        mask = np.zeros((h+2 , w+2), np.uint8)
        cv2.floodFill(im_floodfill, mask, (0,0), 255)
        cv2.imshow("floodfill test ", im_floodfill)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        ret,background = cv2.threshold(im_floodfill,80,255,cv2.THRESH_BINARY)
        ret,foreground = cv2.threshold(im_floodfill,126,255,cv2.THRESH_BINARY_INV)
        foreground = cv2.bitwise_and(image,image, mask=foreground)  # Update foreground with bitwise_and to extract real foreground
        # Convert black and white back into 3 channel greyscale
        background = cv2.cvtColor(background, cv2.COLOR_GRAY2BGR)
        # Combine the background and foreground to obtain our final image
        image = background
        return background
    
    def getCountours(self,image, lower, upper): ## this is where user submitted values need to be added
        while(lower<=upper):
            edged = cv2.Canny(image, lower, upper)
            contours, hierarchy = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            hierShape=hierarchy.shape
            
            for cnt in contours:
                cv2.drawContours(image,[cnt],-1,(0,0,0), 2)
            lower=lower+10
        # cv2.imshow(f'Image after edging', image)     
        # cv2.waitKey(0)  
        # cv2.destroyAllWindows()
        print(f"Hierarchy length {max(hierShape)}") 
        edged = cv2.Canny(image, lower-10, upper)
        contours, hierarchy = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        hierShape=hierarchy.shape
        for i in range(hierShape[1]):
            testhier = hierarchy[0,i,:]
            if (testhier[0]==-1 and testhier[3]==-1):
                cv2.drawContours(image, contours[i],-1,(0, 255, 0), 2)
                cv2.imshow(f'Image with contour {i}', image)
        selected = int(input("Select the contour to use:"))
        self.contours=contours
        self.contour=contours[selected]
        return contours[i]
        
    def showContour(self):
        cv2.drawContours(self.image, self.contour,-1,(0, 255, 0), 3)
        cv2.imshow(f'Image with found contour', self.image) 
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        ##self.drawnContour = cv2.drawContours(self.image2, self.contour, -1, (0,255,0), 2)
        

class Drawing:
     def __init__(self, filename, contour):
         self.fileName = filename
         self.ctr = contour
         self.dxf  = ezdxf.new("R2010")
         self.emf = self.path()
         
     def drawDXF(self):
        ## create DXF file
        dwg = ezdxf.new("R2010")
        msp = dwg.modelspace()
        dwg.layers.new(name="greeny green lines", dxfattribs={"color": 3})
        for n in range(len(self.ctr)):
            if n >= len(self.ctr) :
                n = 0
            try:
                msp.add_line(self.ctr[n], self.ctr[n + 1], dxfattribs={"layer": "single line", "lineweight": 20})
            except IndexError:
                pass
            finally:
                ## now close the loop
                ##rint("Finished drawing DXF, is this good enough for the fridge?")
                pass
        dwg.saveas(self.fileName + ".dxf")
        self.dxf = dwg
        return self.dxf

     def path(self):
        dpi=10
        x,y,width,height = cv2.boundingRect(self.contour)
        print(f"{x} , {y}, {height},  {width}")
        emf=pyemf.EMF(width/5,height/5,dpi, "mm", verbose=False)  ## this still needs to be sorted and the cordinate system fixed
        pen=emf.CreatePen(pyemf.PS_SOLID,3,(0x00,0x00,0x00))
        emf.SelectObject(pen)
        emf.SetBkMode(pyemf.TRANSPARENT)
        emf.BeginPath()
        emf.MoveTo(self.contour[0,0,0],self.contour[0,0,1])
        for n in range(max(self.contour.shape)-1):
            if n >= max(self.contour.shape) - 1:
                n = 0
            point=self.contour[n,0]
            print(f'pint : {point}, x : {point[0]}, y: {point[1]}')
            emf.LineTo(int(point[0]), int(point[1]))
        emf.LineTo(self.contour[0,0,0],self.contour[0,0,1])
        emf.CloseFigure()
        emf.EndPath()
        emf.StrokePath()
        emf.save(self.fileName + ".emf")
        
     
     def saveEMF(self):
        ret=self.emf.save(self.fileName + ".emf")
        print("saved file : " + self.fileName)
        return ret


## Here beings the script ##
filepath = fd.askopenfilename()

# create the object to hold the openCV processed stuff
outline = Outliner(filepath)
print(f"filename : {outline.getFileName()}")
img = outline.importImage()
processedImg = outline.removeBackground(img)
cv2.imshow('removed background', processedImg)
cv2.waitKey(0)
cv2.destroyAllWindows()
# change the two numbers here to adapt the processing. bigger numer at end means more smoothing
contour = outline.getCountours(processedImg, 30,60)
outline.showContour()


# ##cv2.waitKey(0)
## create object to contain the drawings (dxf and emf)
draw = Drawing(filepath, contour)
#dxf = draw.drawDXF()  ## <-- uncoment this to get a nice DXF file
emf = draw.emf ## <-- this creates the emf file. uncomment to get emf output
ret = draw.saveEMF()
print(f"Made EMF file {draw.fileName}, %s" % str(ret))


cv2.destroyAllWindows()