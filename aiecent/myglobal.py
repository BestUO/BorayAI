class Global_Test:
    model = ""
    logger = ""

def set_model(model):
    Global_Test.model = model

def get_model():
    return Global_Test.model

def set_logger(logger):
    Global_Test.logger = logger

def get_logger():
    return Global_Test.logger


class InParams:
    def __init__(self, uuid, modelparams, topic):
        self.uuid = uuid
        self.modelparams = modelparams
        self.topic = topic


class OutParams:
    def __init__(self, uuid, modelparams, topic):
        self.uuid = uuid
        self.modelparams = modelparams
        self.topic = topic