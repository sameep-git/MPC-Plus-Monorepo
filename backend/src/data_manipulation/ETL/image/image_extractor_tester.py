"""
Standalone tester for `image_extractor.py`.

This script:
  - Builds an `ImageModel` from a local MPC beam directory
  - Runs the gain‑map–corrected EPID pipeline
  - Prints flatness & symmetry metrics
  - (Optionally) saves the smoothed profile plots

It does **not** connect to any database.

Usage examples (from project root):

    python -m src.data_manipulation.ETL.image_calculations.image_extractor_tester \
        /path/to/BeamCheckTemplate6e -b 6e --save-profiles

    6e Test:
    python -m src.data_manipulation.ETL.image_calculations.image_extractor_tester \
        "data/csv_data/NDS-WKS-SN6543-2025-09-18-08-06-01-0004-BeamCheckTemplate6e" -b 6e --save-profiles

    9e Test:
    python -m src.data_manipulation.ETL.image_calculations.image_extractor_tester \
        "data/csv_data/NDS-WKS-SN6543-2025-09-18-08-06-01-0005-BeamCheckTemplate9e" -b 9e --save-profiles

    12e Test:
    python -m src.data_manipulation.ETL.image_calculations.image_extractor_tester \
        "data/csv_data/NDS-WKS-SN6543-2025-09-19-07-41-49-0006-BeamCheckTemplate12e" -b 12e --save-profiles
    
    16e Test:
    python -m src.data_manipulation.ETL.image_calculations.image_extractor_tester \
        "data/csv_data/NDS-WKS-SN6543-2025-09-19-07-41-49-0007-BeamCheckTemplate16e" -b 16e --save-profiles

    2_5x Test:
    python -m src.data_manipulation.ETL.image_calculations.image_extractor_tester \
        "data/csv_data/NDS-WKS-SN6543-2025-09-18-08-06-01-0000-BeamCheckTemplate2.5x" -b 2_5x --save-profiles

"""

import argparse
import logging
import os
import sys

from pylinac.core.image import XIM

from src.data_manipulation.ETL.image.image_extractor import image_extractor
from src.data_manipulation.models.ImageModel import ImageModel


logger = logging.getLogger(__name__)


def build_image_model(folder: str, beam_type: str) -> ImageModel:
    """
    Given a beam results folder, construct an ImageModel with
    clinical, flood, and dark image paths set appropriately.

    Expected files inside `folder`:
      - BeamProfileCheck.xim
      - Floodfield-Raw.xim
      - Offset.dat
    """
    folder = os.path.abspath(folder)

    clinical_path = os.path.join(folder, "BeamProfileCheck.xim")
    flood_path = os.path.join(folder, "Floodfield-Raw.xim")
    dark_path = os.path.join(folder, "Offset.dat")

    missing = [
        name
        for name, path in [
            ("BeamProfileCheck.xim", clinical_path),
            ("Floodfield-Raw.xim", flood_path),
            ("Offset.dat", dark_path),
        ]
        if not os.path.exists(path)
    ]
    if missing:
        raise FileNotFoundError(
            f"Missing required image file(s) in folder '{folder}': {', '.join(missing)}"
        )

    image = ImageModel()
    image.set_path(clinical_path)
    image.set_type(beam_type)

    # Derive metadata from the path using existing helpers on the model
    image.set_date(image._getDateFromPathName(clinical_path))
    image.set_machine_SN(image._getSNFromPathName(clinical_path))
    image.set_image_name(image.generate_image_name())

    # Load clinical XIM image
    image.set_image(XIM(image.get_path()))

    # Derive flood and dark paths (same convention as DataProcessor)
    image.set_flood_image_path(flood_path)
    image.set_dark_image_path(dark_path)

    logger.info("ImageModel initialized for beam '%s' in folder '%s'", beam_type, folder)
    return image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Local tester for EPID gain‑map image_extractor (no database).",
        usage=(
            "python -m src.data_manipulation.ETL.image_calculations.image_extractor_tester "
            "FOLDER -b BEAM_TYPE [--save-profiles]"
        ),
    )

    parser.add_argument(
        "folder",
        help=(
            "Path to a beam results directory containing "
            "'BeamProfileCheck.xim', 'Floodfield-Raw.xim', and 'Offset.dat'."
        ),
    )
    parser.add_argument(
        "-b",
        "--beam",
        required=True,
        help="Beam type identifier (e.g. 6e, 9e, 12e, 16e, 10x, 15x, 6xFFF, 6xMVkVEnhancedCouch).",
    )
    parser.add_argument(
        "--save-profiles",
        action="store_true",
        help="Save horizontal and vertical smoothed profile plots as PNGs in a 'profiles' subfolder.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug‑level logging for troubleshooting.",
    )

    return parser.parse_args()


def save_profile_figures(image_model: ImageModel, output_dir: str, beam_type: str) -> None:
    """
    Save the horizontal and vertical profile figures (if present) to PNG files.
    """
    import matplotlib.pyplot as plt

    os.makedirs(output_dir, exist_ok=True)

    horiz_fig = image_model.get_horizontal_profile_graph()
    vert_fig = image_model.get_vertical_profile_graph()

    if horiz_fig is not None:
        horiz_path = os.path.join(output_dir, f"{beam_type}_horizontal_profile.png")
        horiz_fig.savefig(horiz_path, dpi=150, bbox_inches="tight")
        logger.info("Saved horizontal profile plot to %s", horiz_path)

    if vert_fig is not None:
        vert_path = os.path.join(output_dir, f"{beam_type}_vertical_profile.png")
        vert_fig.savefig(vert_path, dpi=150, bbox_inches="tight")
        logger.info("Saved vertical profile plot to %s", vert_path)

    # Close figures to free memory for repeated test runs
    plt.close("all")


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting image_extractor tester")
    logger.info("Beam type: %s", args.beam)
    logger.info("Folder: %s", args.folder)

    try:
        image_model = build_image_model(args.folder, args.beam)
    except Exception as exc:
        logger.error("Failed to initialize ImageModel: %s", exc)
        sys.exit(1)

    extractor = image_extractor()

    try:
        extractor.process_image(image_model, is_test=True)
    except Exception as exc:
        logger.error("Image extraction / analysis failed: %s", exc)
        sys.exit(1)

    # Print core metrics to stdout for quick inspection
    print("\n=== EPID FieldAnalysis Results ===")
    print(f"Beam type: {image_model.get_type()}")
    print(f"Machine SN: {image_model.get_machine_SN()}")
    print(f"Image name: {image_model.get_image_name()}")
    print()
    print(f"Flatness (Horizontal): {image_model.get_flatness_horizontal()}")
    print(f"Flatness (Vertical):   {image_model.get_flatness_vertical()}")
    print(f"Symmetry (Horizontal): {image_model.get_symmetry_horizontal()}")
    print(f"Symmetry (Vertical):   {image_model.get_symmetry_vertical()}")
    print("=================================\n")

    if args.save_profiles:
        profiles_dir = os.path.join(os.path.abspath(args.folder), "profiles")
        save_profile_figures(image_model, profiles_dir, args.beam)


if __name__ == "__main__":
    main()


