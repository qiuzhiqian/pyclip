#  Copyright 2021 Spencer Phillip Young
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
"""
Provides the clipboard functionality for usmart via ``cotent-hub``
"""
from .base import ClipboardBase, ClipboardSetupException, ClipboardException
from typing import Union

import dbus
import dbus.service
import dbus.mainloop.glib

class MirClipboard(ClipboardBase):
    def __init__(self):
        self.conn = dbus.SessionBus()
        self.sufaceid = "18c3da18-3825-4d63-b974-8c46ef71f910" # for test

    @staticmethod
    def serializeMimeData(data: Union[str, bytes], encoding: str = None):
        if encoding is None:
            encoding = "utf-8"
        use_bytes = None
        if isinstance(data, bytes):
            use_bytes = True
        elif isinstance(data, str):
            use_bytes = False
        else:
            raise TypeError("data argument must be of type str or bytes, not {}".format(type(data)))
        

        mimeRawData = b""
        mimeType = ["text/plain"]

        mimeRawData = mimeRawData + len(mimeType).to_bytes(4, byteorder='little', signed=True)

        offset = 4
        for mime in mimeType:
            offset = offset + 4*4
            format_size = len(mime)
            
            mimeRawData = mimeRawData + offset.to_bytes(4, byteorder='little', signed=True)
            mimeRawData = mimeRawData + format_size.to_bytes(4, byteorder='little', signed=True)
            offset=offset+format_size

            data_size = len(data)
            mimeRawData = mimeRawData + offset.to_bytes(4, byteorder='little', signed=True)
            mimeRawData = mimeRawData + data_size.to_bytes(4, byteorder='little', signed=True)
            offset=offset+data_size

            mimeRawData = mimeRawData + bytes(mime, encoding = encoding)
            if use_bytes:
                mimeRawData = mimeRawData + data
            else:
                mimeRawData = mimeRawData + bytes(data, encoding = encoding)
            
        #print("data: {}".format(mimeRawData))
        return mimeRawData

    @staticmethod
    def deserializeMimeData(data):
        if len(data) < 4+ 4*4:
            return ""
        format_cnt = int.from_bytes(data[0:4], byteorder='little', signed=True)

        if format_cnt != 1:
            logging.warning("can't support multiple format")

        ret_data = ""
        offset = 4
        for x in range(format_cnt):
            format_offset = int.from_bytes(data[offset:offset+4], byteorder='little', signed=True)
            format_size = int.from_bytes(data[offset+4:offset+8], byteorder='little', signed=True)

            data_offset = int.from_bytes(data[offset+8:offset+12], byteorder='little', signed=True)
            data_size = int.from_bytes(data[offset+12:offset+16], byteorder='little', signed=True)
            
            rawformat = str(data[format_offset:format_offset+format_size], encoding = "utf-8")
            rawdata = str(data[data_offset:data_offset+data_size], encoding = "utf-8")

            offset = offset + data_offset + data_size

            if len(rawdata) != 0:
                ret_data = rawdata
                break
        
        return ret_data

    def copy(self, data: Union[str, bytes], encoding: str = None) -> None:
        mimedata = self.serializeMimeData(data,encoding)
        remote_object = self.conn.get_object("com.ubuntu.content.dbus.Service", "/")
        service_ifc = dbus.Interface(remote_object,dbus_interface='com.ubuntu.content.dbus.Service')
        status = service_ifc.CreatePaste("unity8",self.sufaceid,mimedata,["text/plain"])
        #print("status: []".format(status))

    def paste(self, encoding: str = None, text: bool = None, errors: str = None):
        remote_object = self.conn.get_object("com.ubuntu.content.dbus.Service", "/")
        service_ifc = dbus.Interface(remote_object,dbus_interface='com.ubuntu.content.dbus.Service')
        data = service_ifc.GetLatestPasteData(self.sufaceid)
        rawdata = self.deserializeMimeData(bytes(data))
        #print("rawdata {}".format(rawdata))
        return rawdata

    def clear(self):
        """
        Clear the clipboard contents

        :return:
        """
        self.copy('')
