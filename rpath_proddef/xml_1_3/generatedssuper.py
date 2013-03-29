#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


class GeneratedsSuper(object):
    def format_string(self, input_data, input_name=''):
        return input_data
    def format_integer(self, input_data, input_name=''):
        return '%d' % input_data
    def format_float(self, input_data, input_name=''):
        return '%f' % input_data
    def format_double(self, input_data, input_name=''):
        return '%e' % input_data
    def format_boolean(self, input_data, input_name=''):
        return '%s' % input_data

    def __eq__(self, obj):
        if not isinstance(obj, self.__class__):
            return False
        if len(self.member_data_items_) != len(obj.member_data_items_):
            return False
        fields = (x.name for x in self.member_data_items_)
        for field in fields:
            objL = getattr(self, field)
            objR = getattr(obj, field)
            if isinstance(objL, list):
                if not isinstance(objR, list) or len(objL) != len(objR):
                    return False
                for (L, R) in zip(objL, objR):
                    if L != R:
                        return False
                continue
            if objL != objR:
                return False
        return True

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def __copy__(self):
        newobj = self.__class__()
        fields = (x.name for x in self.member_data_items_)
        for field in fields:
            val = getattr(self, field)
            if isinstance(val, list):
                ret = []
                for v in val:
                    if hasattr(v, '__copy__'):
                        v = v.__copy__()
                    ret.append(v)
            elif hasattr(val, '__copy__'):
                val = val.__copy__()
            setattr(newobj, field, val)
        return newobj
