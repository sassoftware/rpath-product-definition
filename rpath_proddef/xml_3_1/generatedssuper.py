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
        if len(self._member_data_items) != len(obj._member_data_items):
            return False
        fields = (x.name for x in self._member_data_items)
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
