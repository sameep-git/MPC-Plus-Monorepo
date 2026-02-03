import os
import unittest
from unittest.mock import MagicMock, patch
import logging

from src.data_manipulation.ETL.DataProcessor import DataProcessor
from src.data_manipulation.models.EBeamModel import EBeamModel
from src.data_manipulation.models.GeoModel import GeoModel

# Set up basic logging to see output
logging.basicConfig(level=logging.INFO)

class TestDynamic(unittest.TestCase):
    
    @patch('src.data_manipulation.ETL.DataProcessor.Uploader')
    @patch('src.data_manipulation.ETL.DataProcessor.data_extractor')
    @patch('src.data_manipulation.ETL.DataProcessor.image_extractor')
    def test_dynamic_beam_map(self, mock_image_ex, mock_data_ex, mock_uploader_cls):
        # Setup mocks
        mock_up_instance = mock_uploader_cls.return_value
        mock_up_instance.connect.return_value = True
        # Mock variants returned from DB
        mock_up_instance.get_beam_variants.return_value = ['6e', '10x', '6x']
        
        # Test Path for 6xFFF (matches 6x variant)
        path = r"data\csv_data\NDS-WKS-SN6543-2025-09-19-07-41-49-0001-BeamCheckTemplate6xFFF"
        
        dp = DataProcessor(path)
        
        # We need to spy on `_init_beam_model` or verify logs to know what happened
        # But easier, let's just spy on the `extract` method of data_extractor or image_extractor
        # or mock `_init_beam_model` on the instance?
        
        with patch.object(dp, '_init_beam_model', wraps=dp._init_beam_model) as mock_init_model:
            with patch.object(dp, '_init_beam_image') as mock_init_image:
                 dp.RunTest()
                 
                 # Verify connect called
                 mock_up_instance.connect.assert_called()
                 
                 # Verify get_beam_variants called
                 mock_up_instance.get_beam_variants.assert_called()
                 
                 # Verify it matched '6x' variant to GeoModel
                 # _init_beam_model(model_class, beam_type)
                 # Expecting GeoModel, "6xFFF" (because of special handling logic in DataProcessor)
                 # Wait, let's check DataProcessor logic for 6x
                 # if key == "6x": if "BeamCheckTemplate6xFFF" in path: beam_type = "6xFFF"
                 
                 mock_init_model.assert_called()
                 args, _ = mock_init_model.call_args
                 model_class, beam_type = args
                 
                 print(f"\nDetected Model Class: {model_class.__name__}")
                 print(f"Detected Beam Type: {beam_type}")
                 
                 assert model_class == GeoModel
                 assert beam_type == "6xFFF"
                 
        print("Success! Dynamic Beam Mapping verified.")

if __name__ == '__main__':
    unittest.main()
