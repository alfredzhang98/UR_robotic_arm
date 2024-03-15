from dataclasses import dataclass
from .arm_param import StableArmParam, DynamicArmParam


@dataclass
class RoboticArmConfig:
    """
    :param armStableParam: The bone length of the robotic arm
    :param armDynamicParam: The J param
    """
    armStableParam: StableArmParam
    armDynamicParam: DynamicArmParam

    def print_info(self) -> None:
        print(self.armStableParam)
        print(self.armDynamicParam)
