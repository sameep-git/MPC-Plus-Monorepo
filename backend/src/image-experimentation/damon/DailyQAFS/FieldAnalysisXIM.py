import numpy as np
import matplotlib.pyplot as plt
from pylinac.core.image import XIM 
from pylinac import image , FieldAnalysis
import pydicom as dicom



# Uses the built-in function of XIM to load in XIM file "XIM file is a compressed PNG images with a custom look up table and tag"
#my_xim_file =r"C:\Users\dsprouts\Desktop\Coding Projects\Images\6Mv_BeamProfileCheck.xim"
#xim_img = FieldAnalysis(XIM(my_xim_file))
# Field Analysis is a another build in function from pylinac this allows for the analyzation of images that were generated from EPID rignt now it is uses default but can be used with custom parameters
#xim_img.analyze()

#print(xim_img.results()) using this as a test print
#xim_img.publish_pdf(filename="XIMflatsym10MV_non_defaultanaly.pdf")


# raw_dataraw=r"C:\Users\dsprouts\Desktop\Coding Projects\Images\10Mv_BeamProfileCheck.xim"
# raw_data=XIM(raw_dataraw)

# ds=raw_data.as_dicom()



# Floodfieldraw=r"C:\Users\dsprouts\Desktop\Coding Projects\Images\Floodfield10MV-Raw.xim"
# floodfield=XIM(Floodfieldraw)

eps=1e-8

baseline_img= image.load("10raw.png")
#flood_img=flood_img.convert("L")
baseline_array =np.asarray(baseline_img)
raw_img =image.load("10raw_0207.png")
raw_array=np.asarray(raw_img)

mean_baseline = float(np.mean(baseline_array))
corrected =(raw_array/(baseline_array+eps))* mean_baseline
corrected_dicom=image.array_to_dicom(corrected,sid=1000,gantry=0,coll=0,couch=0,dpi=280)
corrected_dicom.save_as("Baseline0201vsRaw0207.dcm")



corrected_data=r"C:\Users\dsprouts\Desktop\Coding Projects\Images\Baseline0201vsRaw0207.dcm"
my_img=FieldAnalysis(corrected_data)
my_img.analyze()
print(my_img.results())
my_img.plot_analyzed_image()
my_img.publish_pdf(filename="Baseline0201vsRaw0207.pdf")


#plt.imshow(corrected_dicom1.pixel_array)
#plt.show()






# plt.figure(figsize=(15,5))

# plt.subplot(1,3,1)
# plt.title("Baseline image")
# plt.imshow(flood_array,cmap="gray")
# plt.axis("off")

# plt.subplot(1,3,2)
# plt.title("Raw image")
# plt.imshow(raw_array,cmap="gray")
# plt.axis("off")

# plt.subplot(1,3,3)
# plt.title("Pixel-by-Pixel Corrected")
# plt.imshow(corrected,cmap="gray")
# plt.axis("off")

# plt.show()







