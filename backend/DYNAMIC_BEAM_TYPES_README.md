# Dynamic Beam Types Documentation

 This system dynamically fetches valid beam variants from the Supabase `beam_variants` table instead of using a hardcoded list. This allows you to add standard beam types (like "18x" or "20e") simply by adding them to the database, without changing code.

 However, the system relies on **heuristics** to map these string variants (e.g., "10x") to the correct Python Model Class (e.g., `XBeamModel`).

 ## How it Works

 The mapping logic is located in `src/data_manipulation/ETL/DataProcessor.py` within the `_get_dynamic_beam_map` method (approx. lines 100-140).

 ### Default Rules
 1.  **Ends with 'x'**: Maps to `XBeamModel`.
 2.  **Ends with 'e'**: Maps to `EBeamModel`.

 ### Special Cases (Custom Logic)
 Some beam types, particularly Geometry checks or FFF beams, may not follow standard naming conventions or require a specific model class (like `GeoModel`) instead of the default. These **must** be hardcoded in the exception block.

 ## Customization Instructions

 ### 1. Geometry Checks (GeoModel)
 If you introduce a new geometry check that is **NOT** named standardly (or if you change `6x` to something else for geometry), you must add a specific condition.

 **Example**: Adding a "10xGeo" check for research.

 **File**: `src/data_manipulation/ETL/DataProcessor.py`

 ```python
 # ... inside _get_dynamic_beam_map loop ...

 if variant == "6xMVkVEnhancedCouch":
     beam_map[variant] = (GeoModel, "6xMVkVEnhancedCouch")
 # ADD THIS:
 elif variant == "10xGeo":
     beam_map[variant] = (GeoModel, "10xGeo") 
 # ...
 ```

 > **Note**: If you simply use a name ending in "x" (like "GeometryCheck10x"), the system will default to `XBeamModel` unless you intercept it here!

 ### 2. FFF Beams
 Currently, `6xFFF` is explicitly handled to map to `XBeamModel`. If you add `10xFFF`, you might need to add it explicitly if the default "ends with x" logic isn't sufficient or if you need to pass a special beam type string.

 **Example**: Adding "10xFFF".

 ```python
 # ... inside _get_dynamic_beam_map loop ...

 elif variant == "6xFFF":
     beam_map[variant] = (XBeamModel, "6xFFF")
 # ADD THIS:
 elif variant == "10xFFF":
     # Ensure it uses XBeamModel and the correct identifier string
     beam_map[variant] = (XBeamModel, "10xFFF")
 # ...
 ```

 ## Current Logic (Reference)

 See `src/data_manipulation/ETL/DataProcessor.py` around line 123:

 ```python
 123:        for variant in variants:
 124:            # Map database variant string to Model Class
 125:            # Heuristic based on ending char
 126:            if variant == "6xMVkVEnhancedCouch":
 127:                # Special case for 6x geometry check
 128:                beam_map[variant] = (GeoModel, "6xMVkVEnhancedCouch")
 129:            elif variant == "6xFFF":
 130:                # Special case for 6xFFF check
 131:                beam_map[variant] = (XBeamModel, "6xFFF")
 132:            elif variant.endswith("x"):
 133:                beam_map[variant] = (XBeamModel, variant)
 134:            elif variant.endswith("e"):
 135:                beam_map[variant] = (EBeamModel, variant)
 136:            else:
 137:                logger.warning(f"Unknown variant format from DB: {variant}. Skipping.")
 ```
