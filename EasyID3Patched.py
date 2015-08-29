"""Docstring goes here"""
import sys
from mutagen.easyid3 import EasyID3
from config import mapping

reload(sys)
sys.setdefaultencoding("utf-8")



class EasyID3Patched(EasyID3):

    def __init__(self, filename):
        super(EasyID3Patched, self).__init__(filename)
        self._unmodified_data = {k:v for k, v in self.iteritems()}

    @property
    def model_dict(self):
        model_dict = {mapping['to_model'].get(k, k): self._translate_file_value(v) for k, v in self.iteritems()}
        model_dict['path'] = unicode(self.filename)
        return model_dict

    @property
    def is_modified(self):
        return self._unmodified_data != {k:v for k, v in self.iteritems()}

    def update_from_dict(self, input_dict):
        valid_keys = self.valid_keys.keys()
        update_data = {mapping['to_file'].get(k, k): self._translate_model_value(v) for k, v in input_dict.iteritems()}
        update_data = {k: v for k, v in update_data.iteritems() if k in valid_keys and v}
        self.update(update_data)

    def _translate_model_value(self, value):
        # convert None/Null values to empty strings so Mutagen won't complain
        if not value:
            return u''

        # I assume decimals need to be whole percents here (energy/valence), then unicode it cuz Mutagen
        elif isinstance(value, float):
            if value <= 1:
                return unicode(int(value * 100))
            else:
                return unicode(int(value))

        # yup, Mutagen needs everything to be unicode/strings
        else:
            return unicode(value)

    def _translate_file_value(self, value):
    # convert list values to actual value cuz Mutagen is special

        if isinstance(value, list) and value:

            value = value[0]

            if not value:
                return None
        else:
            return None

        if isinstance(value, unicode) or isinstance(value, str):
            try:
                value = float(value)
                if value <= 1:
                    return int(value * 100)
                else:
                    return int(value)
            except ValueError:
                return value

        else:
            return value
