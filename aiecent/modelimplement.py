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
        self.configfilename = "./config.json"
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

    def Eval(self, params):
        resultpath = self.MKDIRByDay()
        p1, p2 = params
        p2 += [str(resultpath.joinpath(p1[1]+"-response.jpg"))]
        stwct.Eval(self.usegpu, self.model, self.conf_json["ContentSize"], self.conf_json["StyleSize"], p2)
        return [p1[0], p1[1] + "_{name}_".format(name=self.name) + str(Path(p2[-1]).relative_to(self.conf_json["LocalResponseDir"]))]


class StyleTransferAdaIN(ModelInterface):

    def __init__(self, name="StyleTransfer-AdaIN"):
        super(StyleTransferAdaIN, self).__init__(name)
        self.config = self._Parseconfig(self.conf_json[name])
        self.model = self._GetModel()

    def _GetModel(self):
        return stadain.GetModel(self.usegpu, self.config)

    def _Parseconfig(self, json):
        return json

    def Eval(self, params):
        resultpath = self.MKDIRByDay()
        p1, p2 = params
        p2 += [str(resultpath.joinpath(p1[1]+"-response.jpg"))]
        stadain.Eval(self.usegpu, self.model, self.conf_json["ContentSize"], self.conf_json["StyleSize"], p2)
        return [p1[0], p1[1] + "_{name}_".format(name=self.name) + str(Path(p2[-1]).relative_to(self.conf_json["LocalResponseDir"]))]


class StyleTransferFast(ModelInterface):

    def __init__(self, name="StyleTransfer-Fast"):
        super(StyleTransferFast, self).__init__(name)
        self.config = self._Parseconfig(self.conf_json[name])
        self.model = self._GetModel()

    def _GetModel(self):
        return stfast.GetModel(self.usegpu, self.config)

    def _Parseconfig(self, json):
        return json

    def Eval(self, params):
        resultpath = self.MKDIRByDay()
        p1, p2 = params
        p2 += [str(resultpath.joinpath(p1[1]+"-response.jpg"))]
        stfast.Eval(self.usegpu, self.model, self.conf_json["ContentSize"], self.conf_json["StyleSize"], p2)
        return [p1[0], p1[1] + "_{name}_".format(name=self.name) + str(Path(p2[-1]).relative_to(self.conf_json["LocalResponseDir"]))]

class FastSpeech(ModelInterface):

    def __init__(self, name="TextToSpeech"):
        super(FastSpeech, self).__init__(name)
        self.config = self._Parseconfig(self.conf_json[name])
        self.model = self._GetModel()

    def _GetModel(self):
        return tts.GetModel(self.usegpu, self.config)

    def _Parseconfig(self, json):
        return json

    def Eval(self, params):
        resultpath = self.MKDIRByDay()
        p1, p2 = params
        p2 += [str(resultpath.joinpath(p1[1]+"-response.wav"))]
        tts.Eval(self.usegpu, self.model, p2)
        return [p1[0], p1[1] + "_{name}_".format(name=self.name) + str(Path(p2[-1]).relative_to(self.conf_json["LocalResponseDir"]))]

class Translate(ModelInterface):

    def __init__(self, name="Translate"):
        super(Translate, self).__init__(name)
        self.config = self._Parseconfig(self.conf_json[name])
        self.model = self._GetModel()

    def _GetModel(self):
        return translate.GetModel(self.usegpu, self.config)

    def _Parseconfig(self, json):
        return json

    def Eval(self, params):
        p1, p2 = params
        translated = translate.Eval(self.usegpu, self.model, p2)
        return [p1[0], p1[1] + "_{name}_".format(name=self.name) + translated]

class StyleTransferNone(ModelInterface):

    def __init__(self, name="None"):
        super(StyleTransferNone, self).__init__(name)

    def _GetModel(self):
        myglobal.get_logger().error("ERROR")

    def Parseconfig(self, json):
        pass

    def Eval(self, params):
        myglobal.get_logger().error("ERROR")