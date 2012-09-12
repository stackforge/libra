from json import dumps


class ServiceFault(object):
    def __init__(self, code, message, details):
        self.code = code
        self.message = message
        self.details = details

    def to_json(self):
        data = {
            "serviceFault": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }
        return data

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)


class BadRequest(ServiceFault):
    def __init__(self,
                 validation_errors,
                 code="400",
                 message="Validation fault",
                 details="The object is not valid"):
        ServiceFault.__init__(self, code, message, details)
        self.validation_errors = validation_errors

    def to_json(self):
        data = {
            "badRequest": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "validationErrors": {
                    "message": self.validation_errors
                }
            }
        }
        return data

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)
