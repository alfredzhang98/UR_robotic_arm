from dataclasses import dataclass
from .arm_bone import ArmBone


@dataclass
class RoboticArmConfig:
    """
    :param Bone: The bone length of the robotic arm
    """
    Bone: ArmBone

    def print_info(self) -> None:
        print(self.Bone)
