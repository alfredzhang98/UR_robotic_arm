from devices.configuration import StableArmParam, DynamicArmParam
from devices.configuration import RoboticArmConfig

armBone_stable_ur3e = StableArmParam(151.8, 243.5, 213.2)
armBone_dynamic_ur3e = DynamicArmParam(joint_angle_list=[1, 23, 4, 5, 6, 7])

config = RoboticArmConfig(
    armStableParam=armBone_stable_ur3e,
    armDynamicParam=armBone_dynamic_ur3e
)
