from abc import ABC, abstractmethod
import json
import PytorchWCT.stwct as stwct
import PytorchAdaIN.stadain as stadain
import FastNeuralStyleTransfer.stfast as stfast
import HuggingFace.translate as translate
import TextToSpeech.tts as tts
import time
import os
import myglobal
from pathlib import Path

class ModelInterface(ABC):

    def __init__(self, name):
        self.name = name
        self.configfilename = "../config.json"
        with open(self.configfilename) as f:
            self.conf_json = json.load(f)
        self.usegpu = self.conf_json["UseGPU"]

    @abstractmethod
    def _Parseconfig(self, json):
        pass

    @abstractmethod
    def _GetModel(self):
        pass

    @abstractmethod
    def _ParseParams(self, params):
        pass

    @abstractmethod
    def Eval(self, params):
        pass

    def MKDIRByDay(self):
        dirpath = Path(self.conf_json["LocalResponseDir"]).joinpath(time.strftime("%Y%m%d", time.localtime()),self.name)
        os.makedirs(dirpath, exist_ok=True)
        return dirpath


class StyleTransferWCT(ModelInterface):

    def __init__(self, name="StyleTransfer-WCT"):
        super(StyleTransferWCT, self).__init__(name)
        self.config = self._Parseconfig(self.conf_json[name])
        self.model = self._GetModel()
        
    def _GetModel(self):
        return stwct.GetModel(self.usegpu, self.config)

    def _Parseconfig(self, json):
        return json

    def _ParseParams(self, params):
        def parsemodelparams(modelparams):
            return modelparams

        resultpath = self.MKDIRByDay()
        p1 = []
        p2 = []
        for param in params:
            p1 += [[param.topic, param.uuid]]
            p2 += [parsemodelparams(param.modelparams) + [str(resultpath.joinpath(param.uuid+"-response.jpg"))]]
        return p1, p2

    def Eval(self, params):
        p1, p2 = self._ParseParams(params)
        stwct.Eval(self.usegpu, self.model, self.conf_json["ContentSize"], self.conf_json["StyleSize"], p2)
        result = []
        for p in zip(p1, p2):
            result += [[p[0][0], p[0][1] + "_{name}_".format(name=self.name) + p[1][-1][len(self.conf_json["LocalResponseDir"]):]]]
        return result


class StyleTransferAdaIN(ModelInterface):

    def __init__(self, name="StyleTransfer-AdaIN"):
        super(StyleTransferAdaIN, self).__init__(name)
        self.config = self._Parseconfig(self.conf_json[name])
        self.model = self._GetModel()

    def _GetModel(self):
        return stadain.GetModel(self.usegpu, self.config)

    def _Parseconfig(self, json):
        return json

    def _ParseParams(self, params):
        def parsemodelparams(modelparams):
            return modelparams

        resultpath = self.MKDIRByDay()
        p1 = []
        p2 = []
        for param in params:
            p1 += [[param.topic, param.uuid]]
            p2 += [parsemodelparams(param.modelparams) + [str(resultpath.joinpath(param.uuid+"-response.jpg"))]]
        return p1, p2

    def Eval(self, params):
        p1, p2 = self._ParseParams(params)
        stadain.Eval(self.usegpu, self.model, self.conf_json["ContentSize"], self.conf_json["StyleSize"], p2)
        result = []
        for p in zip(p1, p2):
            result += [[p[0][0], p[0][1] + "_{name}_".format(name=self.name) + p[1][-1][len(self.conf_json["LocalResponseDir"]):]]]
        return result


class StyleTransferFast(ModelInterface):

    def __init__(self, name="StyleTransfer-Fast"):
        super(StyleTransferFast, self).__init__(name)
        self.config = self._Parseconfig(self.conf_json[name])
        self.model = self._GetModel()

    def _GetModel(self):
        return stfast.GetModel(self.usegpu, self.config)

    def _Parseconfig(self, json):
        return json

    def _ParseParams(self, params):
        def parsemodelparams(modelparams):
            modelpath = self.config[modelparams[-1]]
            return [modelparams[0], modelpath]

        resultpath = self.MKDIRByDay()
        p1 = []
        p2 = []
        for param in params:
            p1 += [[param.topic, param.uuid]]
            p2 += [parsemodelparams(param.modelparams) + [str(resultpath.joinpath(param.uuid+"-response.jpg"))]]
        return p1, p2

    def Eval(self, params):
        p1, p2 = self._ParseParams(params)
        stfast.Eval(self.usegpu, self.model, self.conf_json["ContentSize"], self.conf_json["StyleSize"], p2)
        result = []
        for p in zip(p1, p2):
            result += [[p[0][0], p[0][1] + "_{name}_".format(name=self.name) + p[1][2][len(self.conf_json["LocalResponseDir"]):]]]
        return result

class FastSpeech(ModelInterface):

    def __init__(self, name="TextToSpeech"):
        super(FastSpeech, self).__init__(name)
        self.config = self._Parseconfig(self.conf_json[name])
        self.model = self._GetModel()

    def _GetModel(self):
        return tts.GetModel(self.usegpu, self.config)

    def _Parseconfig(self, json):
        return json

    def _ParseParams(self, params):
        def parsemodelparams(modelparams):
            text, modelname, speakerid = modelparams
            modelpath = self.config[modelname]
            return [text, modelpath, int(speakerid), modelname]

        resultpath = self.MKDIRByDay()
        p1 = []
        p2 = []
        for param in params:
            p1 += [[param.topic, param.uuid]]
            p2 += [parsemodelparams(param.modelparams) + [str(resultpath.joinpath(param.uuid+"-response.wav"))]]
        return p1, p2

    def Eval(self, params):
        p1, p2 = self._ParseParams(params)
        tts.Eval(self.usegpu, self.model, p2)
        result = []
        for p in zip(p1, p2):
            result += [[p[0][0], p[0][1] + "_{name}_".format(name=self.name) + p[1][4][len(self.conf_json["LocalResponseDir"]):]]]
        return result

class Translate(ModelInterface):

    def __init__(self, name="Translate"):
        super(Translate, self).__init__(name)
        self.config = self._Parseconfig(self.conf_json[name])
        self.model = self._GetModel()

    def _GetModel(self):
        return translate.GetModel(self.usegpu, self.config)

    def _Parseconfig(self, json):
        return json

    def _ParseParams(self, params):
        def parsemodelparams(modelparams):
            return modelparams.split("/")

        resultpath = self.MKDIRByDay()
        p1 = []
        p2 = []
        for param in params:
            p1 += [[param.topic, param.uuid]]
            p2 += [parsemodelparams(param.modelparams)]
        return p1, p2

    def Eval(self, params):
        p1, p2 = self._ParseParams(params)
        translated = translate.Eval(self.usegpu, self.model, p2)
        result = []
        for p in zip(p1, p2):
            result += [[p[0][0], p[0][1] + "_{name}_".format(name=self.name) + translated]]
        return result

class StyleTransferNone(ModelInterface):

    def __init__(self, name="None"):
        super(StyleTransferNone, self).__init__(name)

    def _GetModel(self):
        myglobal.get_logger().error("ERROR")

    def Parseconfig(self, json):
        pass

    def _ParseParams(self, params):
        pass

    def Eval(self, params):
        myglobal.get_logger().error("ERROR")