# -*- coding: utf-8 -*-
# @Time : 31/03/2024 17:24
# @Author : Qingyu Zhang
# @Email : qingyu.zhang.23@ucl.ac.uk
# @Institution : UCL
# @FileName: type_switch.py
# @Software: PyCharm
# @Blog ：https://github.com/alfredzhang98
from typing import List, Tuple


class TypeSwitch:
    @staticmethod
    def int_list_to_str(int_list: List[int]) -> str:
        return ''.join(chr(i) for i in int_list)

    @staticmethod
    def str_to_int_list(string: str) -> List[int]:
        return [ord(c) for c in string]

    @staticmethod
    def int_list_to_tuple(int_list: List[int]) -> Tuple:
        return tuple(int_list)

    @staticmethod
    def tuple_to_int_list(u_tuple: Tuple) -> List[int]:
        return list(u_tuple)

    @staticmethod
    def char_list_to_int_list(char_list: List[str]) -> List[int]:
        return [ord(c) for c in char_list]

    @staticmethod
    def int_list_to_char_list(int_list: List[int]) -> List[str]:
        return [chr(i) for i in int_list]

    @staticmethod
    def char_list_to_str(char_list: List[str]) -> str:
        return ''.join(char_list)

    @staticmethod
    def str_to_char_list(string: str) -> List[str]:
        return list(string)

    @staticmethod
    def hex_string_to_int_list(hex_string: str) -> List[int]:
        """Convert a hex string to a list of integers."""
        return [int(hex_string[i:i + 2], 16) for i in range(0, len(hex_string), 2)]

    @staticmethod
    def int_list_to_hex_string(int_list: List[int]) -> list[str]:
        """Convert a list of integers to a list of hex strings without '0x' prefix and padded with zeros if
        necessary."""
        return ['{:02x}'.format(number) for number in int_list]

    @staticmethod
    def bytes_to_int_list(b: bytes) -> List[int]:
        return list(b)

    @staticmethod
    def int_list_to_bytes(int_list: List[int]) -> bytes:
        return bytes(int_list)

    @staticmethod
    def bytes_to_str(b: bytes, encoding='utf-8') -> str:
        return b.decode(encoding)

    @staticmethod
    def str_to_bytes(s: str, encoding='utf-8') -> bytes:
        return s.encode(encoding)

    @staticmethod
    def int_to_int_list(n: int, specified_length: int = None, order: str = "msb") -> List[int]:
        byte_list = []
        while n:
            byte_list.append(n & 0xFF)
            n >>= 8
        if order == 'msb':
            byte_list.reverse()
        if specified_length is not None:
            additional_length = specified_length - len(byte_list)
            if additional_length < 0:
                raise ValueError("Specified length is less than the generated list length.")
            # 对于msb，高位在前；对于lsb，高位在后
            byte_list = ([0] * additional_length + byte_list) if order == 'msb' else (byte_list + [0] * additional_length)
        return byte_list

    @staticmethod
    def int_list_to_int(byte_list: List[int], order: str = "msb") -> int:
        if order == 'lsb':
            byte_list = byte_list[::-1]
        result = 0
        for byte in byte_list:
            result = (result << 8) | byte
        return result