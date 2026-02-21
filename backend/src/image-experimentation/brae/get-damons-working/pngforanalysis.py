import numpy as np
import PIL.Image
import matplotlib.pyplot as plt
from pylinac.core.image import XIM

#raw =r"C:\Users\dsprouts\Desktop\Coding Projects\Images\10MV_BeamProfileCheck_0207.xim"
#raw = r"/Users/braeogle/Desktop/MPC-Plus/iDrive/NDS-WKS-SN6543-2025-09-19-07-41-49-0004-BeamCheckTemplate6e/BeamProfileCheck.xim"
raw =  r"src/image-experimentation/brae/get-damons-working/images-and-reports/beamprofilecheck.xim"
raw_img=XIM(raw)
raw_img.save_as("src/image-experimentation/brae/get-damons-working/images-and-reports/10raw_0207.png")
plt.imshow(raw_img)
plt.show