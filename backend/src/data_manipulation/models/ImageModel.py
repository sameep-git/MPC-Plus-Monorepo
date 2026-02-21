from src.data_manipulation.models.AbstractBeamModel import AbstractBeamModel
import numpy as np

class ImageModel(AbstractBeamModel):
    def __init__(self):
        super().__init__()
        self._symmetry_horizontal = None
        self._symmetry_vertical = None
        self._flatness_horizontal = None
        self._flatness_vertical = None
        self._flood_image_path = None
        self._dark_image_path = None
        self._flatness_graph = None
        self._symmetry_graph = None

    # Getters
    def get_image(self):
        return self._image

    def get_image_name(self):
        return self._image_name
        return self._flatness_vertical

    def get_flood_image_path(self):
        return self._flood_image_path

    def get_dark_image_path(self):
        return self._dark_image_path
    

    # Setters
    def set_image(self, image):
        self._image = image

    def set_image_name(self, image_name):
        self._image_name = image_name

    def set_flood_image_path(self, flood_image_path):
        self._flood_image_path = flood_image_path

    def set_dark_image_path(self, dark_image_path):
        self._dark_image_path = dark_image_path
    
    # Image naming helper
    def generate_image_name(self):
        """
        Image Name Format:
        machine_id/date/beam_type/time/
        """
        machine_id = self.get_machine_SN()         # or another method if your machine_id differs
        beam_type = self.get_type()
        date_obj = self.get_date()

        date_str = date_obj.strftime("%Y%m%d")    # date part
        time_str = date_obj.strftime("%H%M%S")    # time part

        name = "BeamProfileCheck"

        # return path-style string
        return f"{machine_id}/{date_str}/{beam_type}/{time_str}/{name}"

    def convert_XIM_to_PNG(self):
        """
        MPC images are natively stored and handled as XIM files.
        However, pylinac field analysis operates on standard image formats (e.g., PNG),
        and our database only stores PNG images.
        
        This method converts the current XIM image into a NumPy array representation
        suitable for PNG-based analysis and persistence.
        """
        xim_image = self.get_image()

        if xim_image is None:
            raise ValueError("No XIM image set. Load an image before conversion to PNG.")

        # Convert XIM image to a NumPy array (PNG-compatible in-memory format)
        png_array = np.asarray(xim_image)

        # Store the converted image for downstream field analysis and DB storage
        self.set_image(png_array)


