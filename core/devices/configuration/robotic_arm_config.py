from dataclasses import dataclass
from .arm_param import ArmParam


@dataclass
class RoboticArmConfig:
    """
    :param armParam: The bone length of the robotic arm
    """
    armParam: ArmParam

    def print_info(self) -> None:
        print(self.armParam)
