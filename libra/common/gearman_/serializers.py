import json

from gearman import DataEncoder


class JSONDataEncoder(DataEncoder):
    """ Class to transform data that the worker either receives or sends. """

    @classmethod
    def encode(cls, encodable_object):
        """ Encode JSON object as string """
        return json.dumps(encodable_object)

    @classmethod
    def decode(cls, decodable_string):
        """ Decode string to JSON object """
        return json.loads(decodable_string)
