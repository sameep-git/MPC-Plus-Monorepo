import pylinac
from PIL import Image
from pylinac import image , FieldAnalysis
import numpy as np
from pylinac.core.image import XIM , ArrayImage 
import matplotlib.pyplot as plt

def main():
    path = r"data\csv_data\NDS-WKS-SN6543-2015-09-18-08-06-01-0000-BeamCheckTemplate2.5x"
    cp = path + r"\BeamProfileCheck.xim"
    dp = path + r"\Offset.dat"
    fp = path + r"\Floodfield-Raw.xim"
    results = process_image(cp, dp, fp)
    print(results)
    
def process_image(clinical_path, dark_path, flood_path):
    # Load images (you may need to convert XIM to a format pylinac accepts)
    clinical = XIM(clinical_path)
    clinical = np.array(clinical)
    dark = XIM(dark_path)
    dark = np.array(dark)
    flood = XIM(flood_path)
    flood = np.array(flood)
    
    # Apply corrections
    corrected_flood = flood - dark
    corrected_clinical = clinical - dark
    
    # Avoid division by zero
    threshold = 1e-6
    corrected_flood[corrected_flood < threshold] = threshold
    
    # Normalize
    #normalized = corrected_clinical / corrected_flood
    normalized = np.divide(
    corrected_clinical,
    corrected_flood,
    out=np.zeros_like(corrected_clinical, dtype=np.float32),
    where=corrected_flood > threshold
    )

    img = ArrayImage(normalized, dpi = 280)
    analysis = FieldAnalysis(img)
    
    print(analysis)
    analysis.analyze()
    r = analysis.results()
    print(r)
    r = analysis.results_data()
    print(r)
    
    h = analysis.horiz_profile
    plt.figure()
    plt.plot(h.values)
    plt.title("Horizontal Profile")
    plt.xlabel("Pixel")
    plt.ylabel("Intensity")
    plt.grid(True)

    plt.savefig("horizontal_profile.png", dpi=300, bbox_inches="tight")
    plt.close()

    v = analysis.vert_profile
    plt.figure()
    plt.plot(v.values)
    plt.title("Vertical Profile")
    plt.xlabel("Pixel")
    plt.ylabel("Intensity")
    plt.grid(True)

    plt.savefig("vertical_profile.png", dpi=300, bbox_inches="tight")
    plt.close()

    return {
        'flatness_x': r.protocol_results['flatness_horizontal'],
        'flatness_y': r.protocol_results['flatness_vertical'],
        'symmetry_x': r.protocol_results['symmetry_horizontal'],
        'symmetry_y': r.protocol_results['symmetry_vertical']
    }

if __name__ == "__main__":
    main()
