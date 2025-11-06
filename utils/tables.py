from enum import Enum, auto


class InputTables(Enum):

    OperationScenario = auto()
    OperationScenario_Component_Battery = auto()
    OperationScenario_Component_Behavior = auto()
    OperationScenario_Component_Boiler = auto()
    OperationScenario_Component_Building = auto()
    OperationScenario_Component_EnergyPrice = auto()
    OperationScenario_Component_HeatingElement = auto()
    OperationScenario_Component_HotWaterTank = auto()
    OperationScenario_Component_PV = auto()
    OperationScenario_Component_Region = auto()
    OperationScenario_Component_SpaceCoolingTechnology = auto()
    OperationScenario_Component_SpaceHeatingTank = auto()
    OperationScenario_Component_Vehicle = auto()
    OperationScenario_BehaviorProfile = auto()
    OperationScenario_DrivingProfile_ParkingHome = auto()
    OperationScenario_DrivingProfile_Distance = auto()
    OperationScenario_EnergyPrice = auto()
    OperationScenario_RegionWeather = auto()


class OutputTables(Enum):
    OperationResult_OptHour = auto()
    OperationResult_OptMonth = auto()
    OperationResult_OptYear = auto()
    OperationResult_RefHour = auto()
    OperationResult_RefMonth = auto()
    OperationResult_RefYear = auto()
    OperationResult_EnergyCost = auto()
    OperationResult_EnergyCostChange = auto()

