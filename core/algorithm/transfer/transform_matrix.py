##!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 15/03/2024 20:31
# @Author : Qingyu Zhang
# @Email : qingyu.zhang.23@ucl.ac.uk
# @Institution : UCL
# @FileName: test.py
# @Software: PyCharm
# @Blog ：https://github.com/alfredzhang98
"""
@auther
- (Xw, Yw, Zw): The target's position coordinates in the world coordinate system, representing
the target's global location.
- (alpha, beta, gamma): The target's orientation in the world coordinate system, described using
three Euler angles. Alpha is the rotation around the Z-axis (Yaw), beta is the rotation around the
Y-axis (Pitch), and gamma is the rotation around the X-axis (Roll).

Given a point P_a in the world coordinate system, we can transform P_a to a new point P_b in the
target coordinate system B using the target's position and orientation information. This
transformation involves applying a rotation and translation to map the point from the world
coordinate system to a local coordinate system referenced by the target. This mapping is useful
for understanding and manipulating the positions of objects across different reference frames,
especially in fields like 3D modeling, robotic navigation, and spatial analysis.

The class and methods implement this transformation by:
1. Calculating the rotation matrix based on the target's orientation (Euler angles alpha, beta, gamma).
2. Applying the rotation matrix and translation vector (the target's position Xw, Yw, Zw) to transform
the point P_a in the world coordinate system to point P_b in the target coordinate system B.
3. Returning the coordinates of the new point P_b in the target coordinate system B.

This process considers both rotation and translation, ensuring a complete mapping from a global
reference frame to a local reference frame. This way, objects and points in different spatial
reference frames can be flexibly handled and analyzed.

Example:
    >>> arm_transform = TransformMatrix(position=[1, 2, 3], orientation=[30, 45, 60])
    >>> point_a = [4, 5, 6]  # Example point in coordinates A
    >>> point_b = arm_transform.transform_coordinates(point_a)
    >>> print("Point in coordinates B:" + point_b)
    >>> point_a_recovered = arm_transform.inverse_transform_coordinates(point_b)
    >>> print("Point recovered in coordinates A:")
"""

import numpy as np


class TransformMatrix:
    def __init__(self, position, orientation):
        self._position = np.array(position)
        self._orientation = np.array(orientation)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, new_position):
        self._position = np.array(new_position)

    @property
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, new_orientation):
        self._orientation = np.array(new_orientation)

    @classmethod
    def from_dict(cls, data):
        """Create an instance of TransformMatrix based on the provided dictionary"""
        position = data.get('position', [0, 0, 0])
        orientation = data.get('orientation', [0, 0, 0])
        return cls(position, orientation)

    def get_transform_matrix(self):
        alpha, beta, gamma = np.radians(self._orientation)
        Rz = np.array([[np.cos(alpha), -np.sin(alpha), 0, 0],
                       [np.sin(alpha), np.cos(alpha), 0, 0],
                       [0, 0, 1, 0],
                       [0, 0, 0, 1]])

        Ry = np.array([[np.cos(beta), 0, np.sin(beta), 0],
                       [0, 1, 0, 0],
                       [-np.sin(beta), 0, np.cos(beta), 0],
                       [0, 0, 0, 1]])

        Rx = np.array([[1, 0, 0, 0],
                       [0, np.cos(gamma), -np.sin(gamma), 0],
                       [0, np.sin(gamma), np.cos(gamma), 0],
                       [0, 0, 0, 1]])

        translation_matrix = np.eye(4)
        translation_matrix[:3, 3] = self._position

        rotation_matrix = Rz @ Ry @ Rx
        transform_matrix = translation_matrix @ rotation_matrix

        return transform_matrix

    def transform_coordinates(self, point_a):
        # Assuming point_a is a 3D point in the form of a list or a NumPy array
        point_a_homogeneous = np.append(np.array(point_a), 1)  # Convert to homogeneous coordinates
        transform_matrix = self.get_transform_matrix()
        point_b_homogeneous = transform_matrix @ point_a_homogeneous  # Transform the point
        point_b = point_b_homogeneous[:3]  # Convert back to 3D coordinates from homogeneous coordinates
        return point_b

    def inverse_transform_coordinates(self, point_b):
        # Assuming point_b is a point in coordinates B
        point_b_homogeneous = np.append(np.array(point_b), 1)  # Convert to homogeneous coordinates
        transform_matrix = self.get_transform_matrix()
        inverse_transform_matrix = np.linalg.inv(transform_matrix)  # Compute the inverse of the transform matrix
        point_a_homogeneous = inverse_transform_matrix @ point_b_homogeneous  # Transform the point back
        point_a = point_a_homogeneous[:3]  # Convert back to 3D coordinates from homogeneous coordinates
        return point_a
