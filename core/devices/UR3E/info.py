from devices.configuration import ArmBone
from devices.configuration import RoboticArmConfig

armBone_ur3e = ArmBone(151.8, 243.5, 213.2)

config = RoboticArmConfig(
    Bone=armBone_ur3e
)
