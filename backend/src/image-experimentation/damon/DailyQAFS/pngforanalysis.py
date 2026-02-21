import numpy as np
import PIL.Image
import matplotlib.pyplot as plt
from pylinac.core.image import XIM

raw =r"C:\Users\dsprouts\Desktop\Coding Projects\Images\10MV_BeamProfileCheck_0207.xim"
raw_img=XIM(raw)
raw_img.save_as("10raw_0207.png")
plt.imshow(raw_img)
plt.show