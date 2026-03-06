"""
from pylinac.core.image import XIM
from pylinac.mlc import Field


# Load XIM
xim = XIM("/Users/braeogle/Desktop/MPC-Plus/iDrive/NDS-WKS-SN6543-2025-09-19-07-41-49-0004-BeamCheckTemplate6e/BeamProfileCheck.xim")

# Create Field object
field = Field(xim.array)

# Horizontal profile
flat_h = field.flatness_h
sym_h = field.symmetry_h

# Vertical profile
flat_v = field.flatness_v
sym_v = field.symmetry_v

print(f"Horizontal Flatness: {flat_h:.2f}%")
print(f"Horizontal Symmetry: {sym_h:.2f}%")
print(f"Vertical Flatness: {flat_v:.2f}%")
print(f"Vertical Symmetry: {sym_v:.2f}%")
 """

from pylinac import FieldAnalysis, Protocol
from pylinac.core.image import XIM
import matplotlib.pyplot as plt

def analyze_xim_flat_sym(xim_path, protocol=Protocol.VARIAN, in_field_ratio=0.8):
    """
    Analyze flatness and symmetry using pylinac FieldAnalysis for a XIM image.

    Args:
        xim_path (str): Path to the .xim image
        protocol (Protocol): Protocol to use (Varian, Elekta, etc.)
        in_field_ratio (float): Fraction of field to use for metrics (e.g., 0.8 for central 80%)

    Returns:
        dict: Results with flatness/symmetry and other field data
    """
    # Load XIM as a pylinac image
    xim_img = XIM(xim_path)

    # Create a FieldAnalysis object using the XIM array
    fa = FieldAnalysis(image=xim_img.array)

    # Analyze with the chosen protocol
    fa.analyze(protocol=protocol, in_field_ratio=in_field_ratio)

    # Print/plot as needed
    fa.plot_analyzed_image()
    plt.show()

    # Results
    res_str = fa.results()
    print(res_str)

    return fa.results_data()


if __name__ == "__main__":
    #xim_file = "path/to/your/image.xim"
    xim_file = "/Users/braeogle/Desktop/MPC-Plus/iDrive/NDS-WKS-SN6543-2025-09-19-07-41-49-0004-BeamCheckTemplate6e/BeamProfileCheck.xim"
    results = analyze_xim_flat_sym(xim_file)
    print("Results dict:", results)
