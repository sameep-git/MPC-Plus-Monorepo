import pylinac
from PIL import Image
from pylinac import image , FieldAnalysis
import numpy as np
from pylinac.core.image import XIM , ArrayImage

def main():
    cp = r"src\image-experimentation\brae\Stephens\BeamProfileCheck.png"
    dp = r"src\image-experimentation\brae\Stephens\Offset.png"
    fp = r"src\image-experimentation\brae\Stephens\Floodfield-Raw.png"
    results = process_epid_image(cp, dp, fp)
    print(results)
    
def process_epid_image(clinical_path, dark_path, flood_path):
    # Load images (you may need to convert XIM to a format pylinac accepts)
    # clinical = XIM(clinical_path)
    # dark = XIM(dark_path)
    # flood = XIM(flood_path)
    clinical = image.load(clinical_path)
    clinical = np.array(clinical)
    dark = image.load(dark_path)
    dark = np.array(dark)
    flood = image.load(flood_path)
    flood = np.array(flood)
    
    # Apply corrections
    corrected_flood = flood - dark
    corrected_clinical = clinical - dark
    
    # Avoid division by zero
    threshold = 1e-6
    corrected_flood[corrected_flood < threshold] = threshold
    
    # Normalize
    normalized = corrected_clinical / corrected_flood
    normalized_image_path = r"src\image-experimentation\brae\Stephens\Normalized.png"
    # #normalized.save_as(normalized_image_path)
    # # Scale floats 0-1 to 0-255 and convert to uint8
    # normalized_uint8 = np.clip(normalized * 255, 0, 255).astype(np.uint8)
    # img = Image.fromarray(normalized_uint8)
    # img.save(normalized_image_path)

    corrected = normalized
    corrected_dicom = image.array_to_dicom(
            corrected,
            sid=1000,
            gantry=0,
            coll=0,
            couch=0,
            dpi=280
        )
    corrected_dicom.save_as(normalized_image_path)
    corrected_data = normalized_image_path
    
    # Use pylinac for analysis
    # You may need to save normalized image and load with FieldAnalysis
    # or subclass to work with arrays directly
    
    analysis = FieldAnalysis(normalized_image_path)
    #analysis.analyze()
    # try:
    #     analysis.analyze()
    # except KeyError:
    #     print("Warning: Penumbra could not be calculated, but flatness/symmetry will still work.")
    
    return {
        'flatness_x': analysis.flatness_horizontal,
        'flatness_y': analysis.flatness_vertical,
        'symmetry_x': analysis.symmetry_horizontal,
        'symmetry_y': analysis.symmetry_vertical
    }

if __name__ == "__main__":
    main()
