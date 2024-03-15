from dataclasses import dataclass, field
from turtle import position
from typing import List


@dataclass(frozen=True)
class StableArmParam:
    bone_branch1: float = 0.0
    bone_branch2: float = 0.0
    bone_branch3: float = 0.0
    bone_branch4: float = 0.0
    bone_small: float = 0.0
    bone_end: float = 0.0

    def __post_init__(self):
        pass

    def __repr__(self) -> str:
        return f"bone_branch1:{self.bone_branch1}\n" \
               f"bone_branch2:{self.bone_branch2}\n" \
               f"bone_branch3:{self.bone_branch3}\n" \
               f"bone_branch4:{self.bone_branch4}\n" \
               f"bone_small:{self.bone_small}\n" \
               f"bone_end:{self.bone_end}"

    @property
    def bone_lengths_list(self):
        return self.bone_branch1, self.bone_branch2, self.bone_branch3, \
            self.bone_branch4, self.bone_small, self.bone_end


@dataclass
class DynamicArmParam:
    # J1,J2,J3,J4,J5,J6 or more DOF
    joint_angle_list: List[int]

    def __post_init__(self):
        pass

    def __repr__(self) -> str:
        return f"joint_angle_list:{self.joint_angle_list}"

    @property
    def joint_angle(self):
        """This could change the list and certain data"""
        return self.joint_angle_list

    @joint_angle.setter
    def joint_angle(self, update_list):
        """This could change the list and certain data"""
        self.joint_angle_list = update_list
