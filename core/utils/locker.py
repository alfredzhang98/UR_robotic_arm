# -*- coding: utf-8 -*-
# @Time : 26/03/2024 01:06
# @Author : Qingyu Zhang
# @Email : qingyu.zhang.23@ucl.ac.uk
# @Institution : UCL
# @FileName: locker.py
# @Software: PyCharm
# @Blog ：https://github.com/alfredzhang98


def singletonDecorator(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
