# EPID Gain Map Pipeline – Implementation Documentation

## Overview

This module implements an **EPID gain map correction pipeline** for MPC image analysis. Unlike traditional workflows that separate calibration and daily processing, this implementation performs **all steps dynamically at runtime**.

The pipeline corrects detector artifacts while preserving the true radiation beam profile, enabling accurate flatness and symmetry analysis.

---

## Key Design Differences

Compared to the reference pipeline:

- Gain map is built **on-the-fly** for each run
- Accepts **variable number of flood images**
- Includes **automatic bad pixel correction**
- Uses **direct pylinac integration (ArrayImage)**
- Profile smoothing is used for **visualization only**

---

## End-to-End Workflow

The main function:

```
process_image()
```

Performs:

1. Load clinical and dark images  
2. Build gain map from flood images  
3. Apply detector correction  
4. Run beam analysis (pylinac)  
5. Generate smoothed profile plots  

---

## Gain Map Construction

### Steps

1. **Dark Subtraction**
```
F_net = F_raw - Dark
```

2. **Median Stacking**
- Multiple floods → pixel-wise median
- Single flood → used directly

3. **Beam Shape Estimation**
```
beam_shape = median_filter(flood_net, size=kernel_size)
```

4. **Detector Isolation**
```
gain_map = flood_net / beam_shape
```

5. **ROI Normalization**
- Central 80% of image used
- Ensures mean ≈ 1.0

6. **Bad Pixel Detection**
- Values outside `[0.7, 1.3]` flagged
- Gain map clipped to prevent instability

---

## Clinical Image Correction

1. **Dark Subtraction**
```
C_net = C_raw - Dark
```

2. **Gain Correction**
```
corrected = C_net / gain_map
```

3. **Bad Pixel Interpolation (Custom Behavior)**
```
corrected[bad_pixel_mask] = median_filter(corrected, size=5)
```

This replaces defective pixels instead of excluding them.

---

## Beam Analysis (pylinac)

Instead of reconstructing DICOM:

```
img = ArrayImage(corrected, dpi=280)
analysis = FieldAnalysis(img)
```

### Configuration:
- Protocol: VARIAN  
- In-field ratio: 0.8  
- Edge detection: FWHM  

---

## Profile Smoothing

- Method: **Savitzky–Golay filter**
- Used only for:
  - Visualization
  - QA plots

⚠️ Not used for metric calculation  
(pylinac handles internal processing)

---

## Output Metrics

The pipeline extracts:

- Flatness (Horizontal & Vertical)
- Symmetry (Horizontal & Vertical)

Also generates:
- Crossline profile plot (raw vs smoothed)
- Inline profile plot (raw vs smoothed)

---

## Design Tradeoffs

| Decision | Benefit | Tradeoff |
|--------|--------|--------|
| Runtime gain map | Simpler workflow | Higher compute cost |
| Single flood fallback | Works with limited data | Lower SNR |
| Bad pixel interpolation | Stable outputs | Slight loss of fidelity |
| No pre-analysis smoothing | Avoids double smoothing | Depends on pylinac |

---

## Key Takeaway

The pipeline separates:

- **Detector behavior** (gain map)
- **Beam behavior** (clinical signal)

By removing only high-frequency detector artifacts, it preserves the true beam profile while ensuring stable and reliable QA metrics.
