from abc import ABC
from datetime import datetime
import re
import xml.etree.ElementTree as ET
import os

class AbstractBeamModel(ABC):
    def __init__(self):
        self._type = ""
        self._path = ""
        self._date = None
        self._machine_SN = None
        self._typeID = None
        self._baseline = False
        self._imageModel = None
        self._symmetry_horizontal = None
        self._symmetry_vertical = None
        self._flatness_horizontal = None
        self._flatness_vertical = None
        self._horizontal_profile_graph = None
        self._vertical_profile_graph = None

    # --- Getters ---
    def get_type(self):
        return self._type

    def get_typeID(self):
        return self._typeID

    def get_date(self):
        return self._date

    def get_path(self):
        return self._path

    def get_machine_SN(self):
        return self._machine_SN

    def get_baseline(self):
        return self._baseline

    def get_image_model(self):
        return self._imageModel
    
    def get_symmetry_horizontal(self):
        return self._symmetry_horizontal

    def get_symmetry_vertical(self):
        return self._symmetry_vertical

    def get_flatness_horizontal(self):
        return self._flatness_horizontal

    def get_flatness_vertical(self):
        return self._flatness_vertical
    
    def get_horizontal_profile_graph(self):
        return self._horizontal_profile_graph
    
    def get_vertical_profile_graph(self):
        return self._vertical_profile_graph

    # --- Setters ---
    def set_type(self, type_value):
        self._type = type_value

    def set_typeID(self, typeID):
        self._typeID = typeID

    def set_path(self, path):
        self._path = path

    def set_date(self, date):
        self._date = date

    def set_machine_SN(self, SN):
        self._machine_SN = SN
    
    def set_baseline(self, baseline):
        self._baseline = baseline

    def set_image_model(self, imageModel):
        self._imageModel = imageModel
    
    def set_symmetry_horizontal(self, value):
        self._symmetry_horizontal = value

    def set_symmetry_vertical(self, value):
        self._symmetry_vertical = value

    def set_flatness_horizontal(self, value):
        self._flatness_horizontal = value

    def set_flatness_vertical(self, value):
        self._flatness_vertical = value

    def set_horizontal_profile_graph(self, value):
        self._horizontal_profile_graph = value

    def set_vertical_profile_graph(self, value):
        self._vertical_profile_graph = value

    # --- Concrete utility methods shared by subclasses ---
    def _getDateFromPathName(self, path: str) -> datetime:
        """
        Extracts a datetime from the given path.
        Example:
            '...NDS-WKS-SN6543-2025-09-19-07-41-49-0008-GeometryCheckTemplate6xMVkVEnhancedCouch'
            → datetime(2025, 9, 19, 7, 41, 49)
        Raises:
            ValueError: if no valid date pattern is found in the path.
        """
        match = re.search(r'(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})', path)
        if not match:
            raise ValueError(f"Could not extract date from path: {path}")
        
        date_str = match.group(1)
        return datetime.strptime(date_str, "%Y-%m-%d-%H-%M-%S")

    def _getSNFromPathName(self, path: str) -> str:
        """
        Extracts a machine ID (serial number) from the given path.
        Example:
            '...NDS-WKS-SN6543-2025-09-19-07-41-49-0008-GeometryCheckTemplate6xMVkVEnhancedCouch'
            → 'SN6543'
            '/Users/alexandrem/Desktop/MPC Data/Arlington/NDS-WKS-SN5512-2025-09-17-07-08-59-0002-BeamCheckTemplate10x'
            → 'SN5512'
        Raises:
            ValueError: if no valid serial number pattern is found in the path.
        """
        match = re.search(r'SN(\d+)', path)
        if not match:
            raise ValueError(f"Could not extract serial number from path: {path}")
        return "SN" + (match.group(1))
    
    def _getIsBaselineFromPathName(self, pathName: str) -> bool:
        """
        Extracts the <IsBaseline> value from the Check.xml file located in the same
        directory as the provided Results.csv path.

        Example:
            Input path: /path/to/myDirectory/Results.csv
            Reads file: /path/to/myDirectory/Check.xml

            <IsBaseline>false</IsBaseline> → returns False
            <IsBaseline>true</IsBaseline>  → returns True

        Args:
            pathName (str): Path to the Results.csv file.

        Raises:
            FileNotFoundError: If Check.xml does not exist.
            ValueError: If <IsBaseline> tag is missing or XML cannot be parsed.
        """
        # Replace Results.csv with Check.xml
        directory = os.path.dirname(pathName)
        check_xml_path = os.path.join(directory, "Check.xml")

        if not os.path.exists(check_xml_path):
            raise FileNotFoundError(f"Check.xml not found in directory: {directory}")

        # Namespace used in the XML
        ns = {'mpc': 'http://www.varian.com/MPC'}

        try:
            tree = ET.parse(check_xml_path)
            root = tree.getroot()
            elem = root.find('mpc:IsBaseline', ns)

            if elem is None or elem.text is None:
                raise ValueError(f"<IsBaseline> tag not found in file: {check_xml_path}")

            return elem.text.strip().lower() == "true"

        except ET.ParseError as e:
            raise ValueError(f"Failed to parse XML file '{check_xml_path}': {e}")
    
    def set_flat_and_sym_vals_from_image(self):
        """
        Retrieve the image analysis model associated with the current image.
        This model is responsible for computing field metrics such as
        flatness and symmetry from the processed (PNG) image.
        """
        myImageModel = self.get_image_model()

        # Extract and store horizontal and vertical flatness values
        self.set_flatness_horizontal(myImageModel.get_flatness_horizontal())
        self.set_flatness_vertical(myImageModel.get_flatness_vertical())

        # Extract and store horizontal and vertical symmetry values
        self.set_symmetry_horizontal(myImageModel.get_symmetry_horizontal())
        self.set_symmetry_vertical(myImageModel.get_symmetry_vertical())

        # Extract and store horizontal and vertical flatness graphs
        self.set_vertical_profile_graph(myImageModel.get_vertical_profile_graph())
        self.set_horizontal_profile_graph(myImageModel.get_horizontal_profile_graph())
