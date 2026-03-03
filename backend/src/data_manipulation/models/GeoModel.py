from src.data_manipulation.models.AbstractBeamModel import AbstractBeamModel
from decimal import Decimal

class GeoModel(AbstractBeamModel):
    def __init__(self):
        super().__init__()
        
        #uuid of the beam type
        self._typeID = None 
        
        # ---- IsoCenterGroup ----
        self._IsoCenterSize = Decimal('0.0')
        self._IsoCenterMVOffset = Decimal('0.0')
        self._IsoCenterKVOffset = Decimal('0.0')

        # ---- BeamGroup ----
        self._relative_output = Decimal('0.0')
        self._relative_uniformity = Decimal('0.0')
        self._center_shift = Decimal('0.0')

        # ---- CollimationGroup ----
        self._CollimationRotationOffset = Decimal('0.0')

        # ---- GantryGroup ----
        self._GantryAbsolute = Decimal('0.0')
        self._GantryRelative = Decimal('0.0')

        # ---- EnhancedCouchGroup ----
        self._CouchMaxPositionError = Decimal('0.0')
        self._CouchLat = Decimal('0.0')
        self._CouchLng = Decimal('0.0')
        self._CouchVrt = Decimal('0.0')
        self._CouchRtnFine = Decimal('0.0')
        self._CouchRtnLarge = Decimal('0.0')
        self._RotationInducedCouchShiftFullRange = Decimal('0.0')

        # ---- CollimationGroup / MLCGroup ----
        # 60 leaves for A and B banks (1–60)
        self._MLCLeavesA = {f"Leaf{i}": Decimal('0.0') for i in range(1, 61)}
        self._MLCLeavesB = {f"Leaf{i}": Decimal('0.0') for i in range(1, 61)}

        self._MaxOffsetA = Decimal('0.0')
        self._MaxOffsetB = Decimal('0.0')
        self._MeanOffsetA = Decimal('0.0')
        self._MeanOffsetB = Decimal('0.0')

        # ---- CollimationGroup / MLCBacklashGroup ----
        # 60 leaves for A and B banks (1–60)
        self._MLCBacklashA = {f"Leaf{i}": Decimal('0.0') for i in range(1, 61)}
        self._MLCBacklashB = {f"Leaf{i}": Decimal('0.0') for i in range(1, 61)}

        self._MLCBacklashMaxA = Decimal('0.0')
        self._MLCBacklashMaxB = Decimal('0.0')
        self._MLCBacklashMeanA = Decimal('0.0')
        self._MLCBacklashMeanB = Decimal('0.0')

        # ---- CollimationGroup / JawsGroup ----
        self._JawX1 = Decimal('0.0')
        self._JawX2 = Decimal('0.0')
        self._JawY1 = Decimal('0.0')
        self._JawY2 = Decimal('0.0')

        # ---- CollimationGroup / JawsParallelismGroup ----
        self._JawParallelismX1 = Decimal('0.0')
        self._JawParallelismX2 = Decimal('0.0')
        self._JawParallelismY1 = Decimal('0.0')
        self._JawParallelismY2 = Decimal('0.0')

    # ---------------- IsoCenterGroup ----------------
    def get_IsoCenterSize(self): return self._IsoCenterSize
    def set_IsoCenterSize(self, value): self._IsoCenterSize = Decimal(str(value))

    def get_IsoCenterMVOffset(self): return self._IsoCenterMVOffset
    def set_IsoCenterMVOffset(self, value): self._IsoCenterMVOffset = Decimal(str(value))

    def get_IsoCenterKVOffset(self): return self._IsoCenterKVOffset
    def set_IsoCenterKVOffset(self, value): self._IsoCenterKVOffset = Decimal(str(value))

    # ---------------- BeamGroup ----------------
    def get_relative_output(self): return self._relative_output
    def set_relative_output(self, value): self._relative_output = Decimal(str(value))

    def get_relative_uniformity(self): return self._relative_uniformity
    def set_relative_uniformity(self, value): self._relative_uniformity = Decimal(str(value))

    def get_center_shift(self): return Decimal(self._center_shift)
    def set_center_shift(self, value): self._center_shift = Decimal(str(value))

    # ---------------- CollimationGroup ----------------
    def get_CollimationRotationOffset(self): return self._CollimationRotationOffset
    def set_CollimationRotationOffset(self, value): self._CollimationRotationOffset = Decimal(str(value))

    # ---------------- GantryGroup ----------------
    def get_GantryAbsolute(self): return self._GantryAbsolute
    def set_GantryAbsolute(self, value): self._GantryAbsolute = Decimal(str(value))

    def get_GantryRelative(self): return self._GantryRelative
    def set_GantryRelative(self, value): self._GantryRelative = Decimal(str(value))

    # ---------------- EnhancedCouchGroup ----------------
    def get_CouchMaxPositionError(self): return self._CouchMaxPositionError
    def set_CouchMaxPositionError(self, value): self._CouchMaxPositionError = Decimal(str(value))

    def get_CouchLat(self): return self._CouchLat
    def set_CouchLat(self, value): self._CouchLat = Decimal(str(value))

    def get_CouchLng(self): return self._CouchLng
    def set_CouchLng(self, value): self._CouchLng = Decimal(str(value))

    def get_CouchVrt(self): return self._CouchVrt
    def set_CouchVrt(self, value): self._CouchVrt = Decimal(str(value))

    def get_CouchRtnFine(self): return self._CouchRtnFine
    def set_CouchRtnFine(self, value): self._CouchRtnFine = Decimal(str(value))

    def get_CouchRtnLarge(self): return self._CouchRtnLarge
    def set_CouchRtnLarge(self, value): self._CouchRtnLarge = Decimal(str(value))

    def get_RotationInducedCouchShiftFullRange(self): return self._RotationInducedCouchShiftFullRange
    def set_RotationInducedCouchShiftFullRange(self, value): self._RotationInducedCouchShiftFullRange = Decimal(str(value))

    # ---------------- MLC Leaves A & B ----------------
    def get_MLCLeafA(self, index): return self._MLCLeavesA[f"Leaf{index}"]
    def set_MLCLeafA(self, index, value): self._MLCLeavesA[f"Leaf{index}"] = Decimal(str(value))

    def get_MLCLeafB(self, index): return self._MLCLeavesB[f"Leaf{index}"]
    def set_MLCLeafB(self, index, value): self._MLCLeavesB[f"Leaf{index}"] = Decimal(str(value))

    # ---------------- MLC Offsets ----------------
    def get_MaxOffsetA(self): return self._MaxOffsetA
    def set_MaxOffsetA(self, value): self._MaxOffsetA = Decimal(str(value))

    def get_MaxOffsetB(self): return self._MaxOffsetB
    def set_MaxOffsetB(self, value): self._MaxOffsetB = Decimal(str(value))

    def get_MeanOffsetA(self): return self._MeanOffsetA
    def set_MeanOffsetA(self, value): self._MeanOffsetA = Decimal(str(value))

    def get_MeanOffsetB(self): return self._MeanOffsetB
    def set_MeanOffsetB(self, value): self._MeanOffsetB = Decimal(str(value))

    # ---------------- MLC Backlash ----------------
    def get_MLCBacklashA(self, index): return self._MLCBacklashA[f"Leaf{index}"]
    def set_MLCBacklashA(self, index, value): self._MLCBacklashA[f"Leaf{index}"] = Decimal(str(value))

    def get_MLCBacklashB(self, index): return self._MLCBacklashB[f"Leaf{index}"]
    def set_MLCBacklashB(self, index, value): self._MLCBacklashB[f"Leaf{index}"] = Decimal(str(value))

    def get_MLCBacklashMaxA(self): return self._MLCBacklashMaxA
    def set_MLCBacklashMaxA(self, value): self._MLCBacklashMaxA = Decimal(str(value))

    def get_MLCBacklashMaxB(self): return self._MLCBacklashMaxB
    def set_MLCBacklashMaxB(self, value): self._MLCBacklashMaxB = Decimal(str(value))

    def get_MLCBacklashMeanA(self): return self._MLCBacklashMeanA
    def set_MLCBacklashMeanA(self, value): self._MLCBacklashMeanA = Decimal(str(value))

    def get_MLCBacklashMeanB(self): return self._MLCBacklashMeanB
    def set_MLCBacklashMeanB(self, value): self._MLCBacklashMeanB = Decimal(str(value))

    # ---------------- Jaws Group ----------------
    def get_JawX1(self): return self._JawX1
    def set_JawX1(self, value): self._JawX1 = Decimal(str(value))

    def get_JawX2(self): return self._JawX2
    def set_JawX2(self, value): self._JawX2 = Decimal(str(value))

    def get_JawY1(self): return self._JawY1
    def set_JawY1(self, value): self._JawY1 = Decimal(str(value))

    def get_JawY2(self): return self._JawY2
    def set_JawY2(self, value): self._JawY2 = Decimal(str(value))

    # ---------------- Jaw Parallelism ----------------
    def get_JawParallelismX1(self): return self._JawParallelismX1
    def set_JawParallelismX1(self, value): self._JawParallelismX1 = Decimal(str(value))

    def get_JawParallelismX2(self): return self._JawParallelismX2
    def set_JawParallelismX2(self, value): self._JawParallelismX2 = Decimal(str(value))

    def get_JawParallelismY1(self): return self._JawParallelismY1
    def set_JawParallelismY1(self, value): self._JawParallelismY1 = Decimal(str(value))

    def get_JawParallelismY2(self): return self._JawParallelismY2
    def set_JawParallelismY2(self, value): self._JawParallelismY2 = Decimal(str(value))

    
    #uuid of the beam type
    def get_typeID(self):
        return self._typeID
    
    def set_typeID(self, typeID):
        self._typeID = typeID
