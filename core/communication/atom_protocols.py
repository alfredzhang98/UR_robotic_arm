# -*- coding: utf-8 -*-
# @Time : 25/03/2024 17:34
# @Author : Qingyu Zhang
# @Email : qingyu.zhang.23@ucl.ac.uk
# @Institution : UCL
# @FileName: atom_protocols.py
# @Software: PyCharm
# @Blog ：https://github.com/alfredzhang98

import math
import logging
import time
import numpy as np
from enum import Enum, auto
from threading import Thread, Event
from typing import List, Tuple, Callable, Dict
from crccheck.crc import Crc16
from utils.type_switch import TypeSwitch
from utils.locker import singletonDecorator
import threading
from AtomEncryption import atom_Hash

'''
See this guide: https://alfredzhang98.notion.site/1ebabd414334452586bec7ad4c06f983?pvs=4
AtomEncryption is from https://github.com/alfredzhang98/atom_sdk/tree/master/python_sdk/atom_encryption/dist
pip install AtomEncryption-0.0.1-py3-none-any.whl
'''

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')


class ProtocolStatus:
    p_ture = 1
    p_false = 0
    p_error = -1

    class DecodeErrorType:
        no_error = 0
        header_error = -1
        seq_error = -2
        uuid_error = -3
        package_num_error = -4
        data_num_per_error = -5
        vpp_error = -6  # crc16
        cmd_error = -7

    class Functions(Enum):
        SPP = 0x10
        STEAM = 0x20
        RADIO = 0x30
        VIDEO = 0x40

    class Direction:
        send_start = 0x00
        send_end = 0x7F
        send_need_none_feedback = 0x00
        send_need_sync_feedback = 0x10
        receive_start = 0x80
        receive_end = 0xFF

    class SeqSysCMD:
        class SPP(Enum):
            send_cmd_None = auto()
            send_authentication = auto()
            send_total_info = auto()
            send_lost_package = auto()
            send_wrong_data = auto()

    class ProtocolsLength:
        header_length = 4
        seq_length = 2
        uuid_length = 2
        package_num_length = 4
        data_num_per_package_length = 2
        vpp_length = 2  # crc16
        cmd_length = 2
        total_crc_length = header_length + seq_length + uuid_length + package_num_length + data_num_per_package_length + vpp_length
        total_length = header_length + seq_length + uuid_length + package_num_length + data_num_per_package_length + vpp_length + cmd_length


@singletonDecorator
class AtomProtocols:
    """
    SPP:
        SPP Decode:
    """

    def __init__(self, send_interface: Callable[[List[int], int], bool],
                 receive_interface: Callable[[], List[int]],
                 header: Tuple[int] = (0xE5, 0x5E, 0xF2, 0x2F),
                 package_length: int = 1024,
                 function: ProtocolStatus.Functions = ProtocolStatus.Functions.SPP,
                 authentication_info: str = "atom_default"):
        """
        :param header: default is (0xE5, 0x5E, 0xF2, 0x2F)
        :param package_length: default package length per send
        :param function: SPP / Steam or others
        :param authentication_info: This info should be same in receiver and sender
        :param send_interface: Must put in by user Callable[[List[int], int], int] input: Data and Data_len Return: Int
        :param receive_interface: Must put in by user Callable[] input: Data and Data_len Return: Int
        """
        # Logger
        self.logger = self.logger = logging.getLogger(self.__class__.__name__)

        if send_interface is None or receive_interface is None:
            raise ValueError("Please input your own send and receive interface")
        self._send_callable = send_interface
        self._receive_callable = receive_interface
        self._header = header
        self._package_length = package_length
        self._function = function
        self._authentication_info = authentication_info

        # Flags
        self._authentication_status_sender = False
        self._authentication_status_receiver = False

        # Common
        self._package_split_num = package_length - ProtocolStatus.ProtocolsLength.total_length
        self._send_seq_sys_cmd = ProtocolStatus.SeqSysCMD.SPP.send_cmd_None

        # Sender
        # This stack is used for store encoded send data
        self._encode_data_stack: List[List[int]] = []
        self._max_encode_data_stack_length = 0xFF
        # This stack is used for store the send data with uuid those data need a reply
        # When a reply come please del the uuid
        self._reply_data_stack: Dict[int, Dict[str, List[int]]] = {}
        self._max_reply_data_stack_length = 0xFFFF
        self._package_uuid = 0x00
        # This is a thread for send data
        self._thread_sending = False
        self._u_thread_sending_stop_event = threading.Event()
        self._u_thread_sending = threading.Thread(target=self._thread_encode_sending,
                                                  args=(self._u_thread_sending_stop_event,))
        self.init_sending_thread()
        time.sleep(1)
        # Receiver
        self._last_package_num = 0x00
        self._decode_data_stack: Dict[int, Dict[str, List[int]]] = {}
        self._max_decode_data_stack_length = 0xFFFF
        self._thread_receiving = False
        self._u_thread_receiving_stop_event = threading.Event()
        self._u_thread_receiving = threading.Thread(target=self._thread_decode_receiving,
                                                    args=(self._u_thread_receiving_stop_event,))

        self.init_receiving_thread()

    @property
    def package_length(self):
        return self._package_length

    @package_length.setter
    def package_length(self, value):
        self._package_length = value

    @property
    def reply_data_stack(self):
        return self._reply_data_stack

    @property
    def decode_data_stack(self):
        return self._decode_data_stack

    @property
    def function(self):
        return self._function

    @staticmethod
    def calculate_crc16(data: List[int]):
        return TypeSwitch.int_to_int_list(Crc16.calc(data))

    #########################################
    # Sender
    def init_sending_thread(self) -> None:
        """
        Init the sending thread
        :return: None
        """
        match self._function.value:
            case ProtocolStatus.Functions.SPP.value:
                self._thread_sending = True
                self._u_thread_sending.start()
                self.logger.info("You start the sending thread")
                return None
            case ProtocolStatus.Functions.STEAM.value:
                return None
            case _:
                return None

    def stop_sending_thread(self):
        """
        Stop the sending thread
        :return: None
        """
        match self._function.value:
            case ProtocolStatus.Functions.SPP.value:
                self._thread_sending = False
                self._u_thread_sending_stop_event.set()
                self._u_thread_sending.join()
                self.logger.info("You stop the sending thread")
                return None
            case ProtocolStatus.Functions.STEAM.value:
                return None
            case _:
                return None

    def _thread_encode_sending(self, stop_event):
        try:
            while not stop_event.is_set():
                if self._encode_data_stack:
                    data = self._encode_data_stack.pop(0)
                    self._send_callable(data, len(data))
                else:
                    pass
        except Exception as e:
            self.logger.exception("An exception occurred" + str(e))

    def _insert_send(self, data: List[int], boost: bool = False):
        while len(self._encode_data_stack) > self._max_encode_data_stack_length:
            self._encode_data_stack.pop(0)
        if boost:
            self._encode_data_stack.insert(0, data)
        else:
            self._encode_data_stack.append(data)

    def _encode_basic(self, seq: List[int], cmd: List[int], data: List[int], uuid: int = None) -> List[List[int]]:
        full_data_list = []
        package_count = 0
        # UUID insert in the reply stack
        if uuid is not None:
            uuid_temp = uuid
        else:
            if self._package_uuid >= self._max_reply_data_stack_length:
                self._package_uuid = 0x00
            self._package_uuid = self._package_uuid + 1
            uuid_temp = self._package_uuid
        if (seq[0] & 0xF0) in [ProtocolStatus.Direction.send_need_sync_feedback]:
            self._reply_data_stack[self._package_uuid] = {"seq": seq, "cmd": cmd, "data": data}
        for i in range(0, len(data), self._package_split_num):
            uuid = TypeSwitch.int_to_int_list(uuid_temp, 2)
            crc = self.calculate_crc16(cmd + data[i:i + self._package_split_num])
            package_count = package_count + 1
            package_count_list = TypeSwitch.int_to_int_list(package_count, 4)
            data_length_per_package_list = TypeSwitch.int_to_int_list(ProtocolStatus.ProtocolsLength.cmd_length +
                                                                      len(data[i:i + self._package_split_num]), 2)
            full_data_list.append(
                list(self._header) + seq + uuid + package_count_list + data_length_per_package_list + crc +
                cmd + data[i:i + self._package_split_num])
        return full_data_list

    def send_data(self, cmd: list[int], data: List[int],
                  feedback_status: int = ProtocolStatus.Direction.send_need_none_feedback,
                  send_seq_user_cmd: int = 0x00):
        """
        :param cmd:
        :param data:
        :param feedback_status:  send_need_none_feedback / send_need_async_feedback / send_need_sync_feedback
        :param send_seq_user_cmd: send_ways and seq
        :return: -1 / 0 / 1
        """
        if self._authentication_status_sender:
            if feedback_status not in [ProtocolStatus.Direction.send_need_none_feedback,
                                       ProtocolStatus.Direction.send_need_sync_feedback]:
                raise ValueError("Not input the right feedback_status, please read the instruction")
            datas = self._encode_basic(seq=[feedback_status | ProtocolStatus.SeqSysCMD.SPP.send_cmd_None.value,
                                            send_seq_user_cmd | self._function.value],
                                       cmd=cmd,
                                       data=data)
            for data in datas:
                self._insert_send(data)
        else:
            self._init_authentication_send()

    def _send_internal_reply(self, uuid: int, cmd: List[int], seq: List[int], data: List[int]):
        # uuid to get the data from the receiver stack
        feedback_status = seq[0] & 0xF0
        if feedback_status < 0x80:
            feedback_status = feedback_status | 0x80
        datas = self._encode_basic(seq=[feedback_status | (seq[0] & 0x0F),
                                        seq[1]],
                                   cmd=cmd,
                                   data=data,
                                   uuid=uuid)
        for data in datas:
            self._insert_send(data)

    def send_reply(self, uuid: int):
        # uuid to get the data from the receiver stack
        seq = self._decode_data_stack[uuid]["seq"]
        feedback_status = seq[0] & 0xF0
        if feedback_status < 0x80:
            feedback_status = feedback_status & 0x80
        datas = self._encode_basic(seq=[feedback_status | (seq[0] & 0x0F),
                                        seq[1]],
                                   cmd=self._decode_data_stack[uuid]["cmd"],
                                   data=self._decode_data_stack[uuid]["data"],
                                   uuid=uuid)
        for data in datas:
            self._insert_send(data)

    def _init_authentication_send(self):
        # Send data
        if not self._authentication_status_sender:
            self._send_seq_sys_cmd = ProtocolStatus.SeqSysCMD.SPP.send_authentication.value
            seq_data = [0x00, 0x00]
            seq_data[0] = ProtocolStatus.Direction.send_need_sync_feedback | self._send_seq_sys_cmd
            seq_data[1] = 0x00 | self._function.value
            authentication_data = atom_Hash.hash_data(self._authentication_info, "sha256")
            datas = self._encode_basic(seq=seq_data,
                                       cmd=[0xFF, 0xFF],
                                       data=TypeSwitch.hex_string_to_int_list(authentication_data))
            for data in datas:
                self._send_callable(data, len(data))

    def _init_send_total_info(self, data: List[int]):
        self._send_seq_sys_cmd = ProtocolStatus.SeqSysCMD.SPP.send_total_info.value
        self._total_packages = math.ceil((len(data) - ProtocolStatus.ProtocolsLength.total_length) /
                                         self._package_split_num)
        self._total_data = len(data)
        datas = self._encode_basic(seq=[ProtocolStatus.Direction.send_need_none_feedback | self._send_seq_sys_cmd,
                                        0x00 | self._function.value],
                                   cmd=[0xFF, 0xFF],
                                   data=(TypeSwitch.int_to_int_list(self._total_packages, 16) +
                                         TypeSwitch.int_to_int_list(self._total_data, 16)))
        for data in datas:
            self._send_callable(data, len(data))
        # Todo wait the receiver to confirm they receive the total info

    #########################################
    # Receiver
    def init_receiving_thread(self) -> None:
        """
        Init the receiving thread
        :return: None
        """
        match self._function.value:
            case ProtocolStatus.Functions.SPP.value:
                self._thread_receiving = True
                self._u_thread_receiving.start()
                self.logger.info("You start the receiving thread")
                return None
            case ProtocolStatus.Functions.STEAM.value:
                return None
            case _:
                return None

    def stop_receiving_thread(self):
        """
        Stop the receiving thread
        :return: None
        """
        match self._function.value:
            case ProtocolStatus.Functions.SPP.value:
                self._thread_receiving = False
                self._u_thread_receiving_stop_event.set()
                self._u_thread_receiving.join()
                self.logger.info("You stop the receiving thread")
                return None
            case ProtocolStatus.Functions.STEAM.value:
                return None
            case _:
                return None

    # Those two method is for user to define their own seq, and supervise their own seq function
    @staticmethod
    def init_seq_user_reply_check(function: ProtocolStatus.Functions, seq_user_reply_check: Callable) \
            -> tuple[Event, Thread]:
        """
        Init the sending reply check thread
        :return: None
        """
        match function:
            case ProtocolStatus.Functions.SPP.value:
                thread_sending_reply_check_stop_event = threading.Event()
                u_thread_sending_reply_check = threading.Thread(target=seq_user_reply_check,
                                                                args=(thread_sending_reply_check_stop_event,))
                u_thread_sending_reply_check.start()
                return thread_sending_reply_check_stop_event, u_thread_sending_reply_check
            case ProtocolStatus.Functions.STEAM.value:
                pass
            case _:
                pass

    @staticmethod
    def stop_seq_user_reply_check_thread(function: ProtocolStatus.Functions, event: threading.Event,
                                         thread: threading.Thread):
        """
        Stop the sending thread
        :return: None
        """
        match function:
            case function.SPP:
                event.set()
                thread.join()
                return None
            case ProtocolStatus.Functions.STEAM.value:
                return None
            case _:
                return None

    def _seq_handler(self, uuid: int, seq: List[int], data: List[int]) -> bool:
        # Todo need to finish this function
        seq_data_direction = seq[0] & 0xF0
        seq_sys_cmd = seq[0] & 0x0F
        match self._function.value:
            # SPP
            case ProtocolStatus.Functions.SPP.value:
                # Receive the send data and so some (Receiver)
                if seq_data_direction <= ProtocolStatus.Direction.send_end:
                    match seq_sys_cmd:
                        case ProtocolStatus.SeqSysCMD.SPP.send_cmd_None.value:
                            return False
                        case ProtocolStatus.SeqSysCMD.SPP.send_authentication.value:
                            # reply inside the function
                            self._init_authentication_receive(uuid, seq, data)
                            return True
                        case ProtocolStatus.SeqSysCMD.SPP.send_total_info.value:
                            self._init_receive_total_info(uuid, data)
                            # no reply
                            return True
                        case ProtocolStatus.SeqSysCMD.SPP.send_wrong_data.value:
                            # Todo: need to resend from the wrong data package
                            return True
                        case ProtocolStatus.SeqSysCMD.SPP.send_lost_package.value:
                            # Todo: need to resend from the lost data package
                            return True
                        case _:
                            return False
                ####################
                # Receive the reply data (Sender)
                if seq_data_direction >= ProtocolStatus.Direction.receive_start:
                    # NOTE: This part is Must do, to pop the sender stack
                    if seq_data_direction in [(ProtocolStatus.Direction.send_need_sync_feedback |
                                               ProtocolStatus.Direction.receive_start)]:
                        if self._reply_data_stack[uuid] is not None:
                            temp = self._reply_data_stack[uuid]
                            del self._reply_data_stack[uuid]
                    match seq_sys_cmd:
                        case ProtocolStatus.SeqSysCMD.SPP.send_cmd_None.value:
                            # No feedback
                            return False
                        case ProtocolStatus.SeqSysCMD.SPP.send_authentication.value:
                            self._authentication_status_sender = bool(TypeSwitch.int_list_to_int(data))
                            self.logger.info("Success authentication")
                            return True
                        case ProtocolStatus.SeqSysCMD.SPP.send_total_info.value:
                            # No feedback
                            return True
                        case ProtocolStatus.SeqSysCMD.SPP.send_wrong_data.value:
                            # No feedback
                            return False
                        case ProtocolStatus.SeqSysCMD.SPP.send_lost_package.value:
                            # No feedback
                            return False
                        case _:
                            return False
        return False

    def _package_handler(self, package_num: int):
        if package_num is (self._last_package_num + 1):
            return True
        else:
            # The package is not continuously
            return False

    def _crc_handler(self, cmd: List[int], data: List[int], crc: List[int]) -> bool:
        match self._function.value:
            # SPP
            case ProtocolStatus.Functions.SPP.value:
                if crc is self.calculate_crc16(cmd + data):
                    return True
                else:
                    return False
            case _:
                return False

    def _decode_basic(self, data: List[int]) -> int:
        match self._function.value:
            case ProtocolStatus.Functions.SPP.value:
                header_len = ProtocolStatus.ProtocolsLength.header_length
                seq_len = ProtocolStatus.ProtocolsLength.seq_length
                uuid_len = ProtocolStatus.ProtocolsLength.uuid_length
                package_num_len = ProtocolStatus.ProtocolsLength.package_num_length
                data_num_per_package_len = ProtocolStatus.ProtocolsLength.data_num_per_package_length
                vpp_len = ProtocolStatus.ProtocolsLength.vpp_length
                cmd_len = ProtocolStatus.ProtocolsLength.cmd_length

                data_step = 0
                if (data[data_step + header_len - 1] != self._header[3] or
                        data[data_step + header_len - 2] != self._header[2] or
                        data[data_step + header_len - 3] != self._header[1] or
                        data[data_step + header_len - 4] != self._header[0]):
                    return ProtocolStatus.DecodeErrorType.header_error
                data_step = header_len
                seq = data[data_step: data_step + seq_len]
                data_step = data_step + seq_len
                uuid = TypeSwitch.int_list_to_int(data[data_step: data_step + uuid_len])
                data_step = data_step + uuid_len
                package_num = data[data_step: data_step + package_num_len]
                data_step = data_step + package_num_len
                data_num_per_package = data[data_step: data_step + data_num_per_package_len]
                data_step = data_step + data_num_per_package_len
                vpp = data[data_step: data_step + vpp_len]
                data_step = data_step + vpp_len
                cmd = data[data_step: data_step + cmd_len]
                data_step = data_step + cmd_len
                main_data = data[data_step::]

                # Seq handler, focus on the seq sys cmd
                if self._seq_handler(uuid, seq, main_data):
                    return ProtocolStatus.DecodeErrorType.no_error

                # Package num test
                if not self._package_handler(TypeSwitch.int_list_to_int(package_num)):
                    # Todo: Lost Package Data need sth to do send a feedback to sender lost package
                    return ProtocolStatus.DecodeErrorType.package_num_error

                # not lost data test CRC test
                if not self._crc_handler(cmd, main_data, vpp):
                    # Todo: Wrong Data need sth to do send a feedback to sender lost data
                    return ProtocolStatus.DecodeErrorType.vpp_error

                # Add data
                if uuid not in self._decode_data_stack:
                    self._decode_data_stack[uuid] = {}
                if self._decode_data_stack[uuid] is None or len(self._decode_data_stack[uuid]) <= 2:
                    self._decode_data_stack[uuid]["seq"] = seq
                    self._decode_data_stack[uuid]["package_num"] = package_num
                    self._decode_data_stack[uuid]["data_num_per_package"] = data_num_per_package
                    self._decode_data_stack[uuid]["cmd"] = cmd
                    self._decode_data_stack[uuid]["data"] = main_data
                else:
                    self._decode_data_stack[uuid]["data"].extend(main_data)

            case ProtocolStatus.Functions.STEAM.value:
                pass
            case _:
                pass

    def _thread_decode_receiving(self, stop_event):
        try:
            while not stop_event.is_set():
                data = self._receive_callable()
                self.logger.debug(data)
                while len(self._decode_data_stack) > self._max_decode_data_stack_length:
                    # If over the max stack length, lost the oldest data
                    min_key = min(self._decode_data_stack.keys())
                    self._decode_data_stack.pop(min_key)
                if data is not None and data != []:
                    match self._decode_basic(data):
                        case ProtocolStatus.DecodeErrorType.no_error:
                            pass
                        case ProtocolStatus.DecodeErrorType.header_error:
                            self.logger.warning("header_error")
                        case ProtocolStatus.DecodeErrorType.seq_error:
                            self.logger.warning("seq_error")
                        case ProtocolStatus.DecodeErrorType.uuid_error:
                            self.logger.warning("uuid_error")
                        case ProtocolStatus.DecodeErrorType.package_num_error:
                            self.logger.warning("package_num_error")
                        case ProtocolStatus.DecodeErrorType.data_num_per_error:
                            self.logger.warning("data_num_per_error")
                        case ProtocolStatus.DecodeErrorType.vpp_error:
                            self.logger.warning("vpp_error")
                        case ProtocolStatus.DecodeErrorType.cmd_error:
                            self.logger.warning("cmd_error")
                        case _:
                            pass
                else:
                    pass
        except Exception as e:
            self.logger.exception("An exception occurred" + str(e))

    def _init_authentication_receive(self, uuid: int, seq: List[int], data: List[int]) -> None:
        authentication_data = atom_Hash.hash_data(self._authentication_info, "sha256")
        if data == TypeSwitch.hex_string_to_int_list(authentication_data):
            self._authentication_status_receiver = True
        else:
            self.logger.warning("Wrong authentication data")
        self._send_internal_reply(uuid=uuid,
                                  cmd=[0xFF, 0xFF],
                                  seq=seq,
                                  data=[int(self._authentication_status_receiver)])

    def _init_receive_total_info(self, uuid: int, data: List[int]):
        if uuid not in self._decode_data_stack:
            self._decode_data_stack[uuid] = {}
        self._decode_data_stack[uuid]["total_package"] = data[0:15]
        self._decode_data_stack[uuid]["total_data"] = data[16:31]

    def get_decode_data(self) -> Tuple:
        min_key = min(self._decode_data_stack.keys())
        return min_key, self._decode_data_stack.pop(min_key)


if __name__ == "__main__":
    send_data = []


    def send(data: List[int], data_len: int) -> bool:
        global send_data
        print("send************")
        print(len(data))
        send_data = data
        print(TypeSwitch.int_list_to_hex_string(data))
        print("send************")
        return True


    def receive() -> List[int]:
        global send_data
        # print("Receive")
        send_temp = []
        if send_data is not None:
            send_temp = send_data
            send_data = []
        return send_temp


    sender = AtomProtocols(send, receive)
    sender.send_data([12, 12], [123, 124, 412, 144])
