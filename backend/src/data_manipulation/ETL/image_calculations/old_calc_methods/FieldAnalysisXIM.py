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

# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
# Small value added to avoid division by zero.
# Some baseline pixels may be zero or extremely small (dead pixels, edges).
# This keeps the math stable without affecting real image values.
# -------------------------------------------------------------------------
eps = 1e-8

# -------------------------------------------------------------------------
# Load the BASELINE image (reference detector response)
# This image represents the expected or "normal" pixel intensities.
# -------------------------------------------------------------------------
baseline_img = image.load(
    "src/image-experimentation/brae/get-damons-working/images-and-reports/10raw.png"
)

# Convert the baseline image to a NumPy array for pixel-wise math
baseline_array = np.asarray(baseline_img)

# -------------------------------------------------------------------------
# Load the RAW image (image being compared against the baseline)
# -------------------------------------------------------------------------
raw_img = image.load(
    "src/image-experimentation/brae/get-damons-working/images-and-reports/10raw_0207.png"
)

# Convert the raw image to a NumPy array
raw_array = np.asarray(raw_img)

# -------------------------------------------------------------------------
# Compute the mean intensity of the baseline image.
# This is used to re-scale the corrected image so overall brightness
# stays consistent with the baseline.
# -------------------------------------------------------------------------
mean_baseline = float(np.mean(baseline_array))

# -------------------------------------------------------------------------
# Perform pixel-by-pixel normalization:
#   1. Divide the raw image by the baseline image
#   2. Add eps to prevent divide-by-zero
#   3. Multiply by the baseline mean to preserve intensity scale
#
# This corrects detector non-uniformity while keeping physics intact.
# -------------------------------------------------------------------------
corrected = (raw_array / (baseline_array + eps)) * mean_baseline

# -------------------------------------------------------------------------
# Convert the corrected NumPy array back into a DICOM image.
# Geometry metadata (SID, gantry, collimator, couch) is required
# so pylinac can properly analyze the image.
# -------------------------------------------------------------------------
corrected_dicom = image.array_to_dicom(
    corrected,
    sid=1000,
    gantry=0,
    coll=0,
    couch=0,
    dpi=280
)

# Save the corrected DICOM image to disk
corrected_dicom.save_as(
    "src/image-experimentation/brae/get-damons-working/images-and-reports/Baseline0201vsRaw0207.dcm"
)

# -------------------------------------------------------------------------
# Run pylinac Field Analysis on the corrected DICOM image
# -------------------------------------------------------------------------
corrected_data = (
    "src/image-experimentation/brae/get-damons-working/images-and-reports/"
    "Baseline0201vsRaw0207.dcm"
)

# Initialize field analysis
#my_img = FieldAnalysis(corrected_data)
my_img = FieldAnalysis(XIM(r"data\csv_data\NDS-WKS-SN6543-2025-09-19-07-41-49-0004-BeamCheckTemplate6e\BeamProfileCheck.xim"))

# Perform flatness, symmetry, and other field metrics
my_img.analyze()

# Print numerical analysis results to the console
print(my_img.results())

# Display the analyzed image with pylinac overlays
#my_img.plot_analyzed_image()

# Generate a PDF report with results and annotated images
my_img.publish_pdf(
    filename="src/image-experimentation/brae/get-damons-working/images-and-reports/Baseline0201vsRaw0207.pdf"
)

h = my_img.horiz_profile

plt.figure()
plt.plot(h.values)
plt.title("Horizontal Profile")
plt.xlabel("Pixel")
plt.ylabel("Intensity")
plt.grid(True)

plt.savefig("horizontal_profile.png", dpi=300, bbox_inches="tight")
plt.close()
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







