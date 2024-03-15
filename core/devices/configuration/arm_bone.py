from dataclasses import dataclass


@dataclass(frozen=True)
class ArmBone:
    bone_branch1: float = 0.0
    bone_branch2: float = 0.0
    bone_branch3: float = 0.0
    bone_branch4: float = 0.0
    bone_small: float = 0.0
    bone_end: float = 0.0

    def __repr__(self) -> str:
        return f'''bone_branch1:{self.bone_branch1}\n
bone_branch2:{self.bone_branch2}\n
bone_branch3:{self.bone_branch3}\n
bone_branch4:{self.bone_branch4}\n
bone_small:{self.bone_small}\n
bone_end:{self.bone_end}\n'''

    @property
    def bone_lengths_list(self):
        return self.bone_branch1, self.bone_branch2, self.bone_branch3, self.bone_branch4, self.bone_small, self.bone_end
