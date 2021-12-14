from abc import ABC, abstractmethod
import importlib
from pathlib import Path

class ParamsPreProcessBase(ABC):
    def __init__(self, config, uuid, funname, modelparams, restopic):
        self.uuid = uuid
        self.funname = funname
        self.modelparams = modelparams
        self.restopic = restopic
        self.config = config[funname]
        self.localdir = Path(config["LocalRequestDir"])

    @abstractmethod
    def _PreCheck(self):
        pass

    @abstractmethod
    def ParamsPreProcess(self):
        pass

    @classmethod
    def decorator(cls, fun):
        def wrap(self, *arg, **kwargs):
            self._PreCheck(*arg,**kwargs)
            return fun(self, *arg,**kwargs)
        return wrap
        

class WCTParamsPreProcess(ParamsPreProcessBase):
    def __init__(self, *arg, **kwargs):
        super(WCTParamsPreProcess, self).__init__(*arg, **kwargs)

    def _PreCheck(self):
        # 20211117/StyleTransfer-WCT/uuid-content.jpg:20211117/StyleTransfer-WCT/uuid-style.jpg:0.8
        img1, img2, alpha = self.modelparams.split(":")

    @ParamsPreProcessBase.decorator    
    def ParamsPreProcess(self):
        def parsemodelparams(modelparams):
            content, style, alpha = modelparams.split(":")
            contentfilepath = Path(self.localdir).joinpath(content)
            stylefilepath = Path(self.localdir).joinpath(style)
            return [str(contentfilepath), str(stylefilepath), alpha]

        p1 = [self.restopic, self.uuid]
        p2 = parsemodelparams(self.modelparams)
        return p1, p2

class AdaINParamsPreProcess(ParamsPreProcessBase):
    def __init__(self, *arg, **kwargs):
        super(AdaINParamsPreProcess, self).__init__(*arg, **kwargs)

    def _PreCheck(self):
        # 20211117/StyleTransfer-WCT/uuid-content.jpg:20211117/StyleTransfer-WCT/uuid-style.jpg:0.8
        img1, img2, alpha = self.modelparams.split(":")

    @ParamsPreProcessBase.decorator    
    def ParamsPreProcess(self):
        def parsemodelparams(modelparams):
            content, style, alpha = modelparams.split(":")
            contentfilepath = Path(self.localdir).joinpath(content)
            stylefilepath = Path(self.localdir).joinpath(style)
            return [str(contentfilepath), str(stylefilepath), alpha]

        p1 = [self.restopic, self.uuid]
        p2 = parsemodelparams(self.modelparams)
        return p1, p2

class FastParamsPreProcess(ParamsPreProcessBase):
    def __init__(self, *arg, **kwargs):
        super(FastParamsPreProcess, self).__init__(*arg, **kwargs)

    def _PreCheck(self):
        _, modelname = self.modelparams.split(":")
        if modelname not in self.config:
            raise ValueError

    @ParamsPreProcessBase.decorator    
    def ParamsPreProcess(self):
        def parsemodelparams(modelparams):
            filename, modelname = modelparams.split(":")
            modelpath = self.config[modelname]
            return [str(self.localdir.joinpath(filename)), modelpath]

        p1 = [self.restopic, self.uuid]
        p2 = parsemodelparams(self.modelparams)
        return p1, p2

class TextToSpeechParamsPreProcess(ParamsPreProcessBase):
    def __init__(self, *arg, **kwargs):
        super(TextToSpeechParamsPreProcess, self).__init__(*arg, **kwargs)

    def _PreCheck(self):
        s, language, speakid = self.modelparams.split(":")
        if language not in self.config or speakid != "0":
            raise ValueError

    @ParamsPreProcessBase.decorator    
    def ParamsPreProcess(self):
        def parsemodelparams(modelparams):
            text, modelname, speakerid = modelparams.split(":")
            modelpath = self.config[modelname]
            return [text, modelpath, int(speakerid), modelname]

        p1 = [self.restopic, self.uuid]
        p2 = parsemodelparams(self.modelparams)
        return p1, p2

class TranslateParamsPreProcess(ParamsPreProcessBase):
    def __init__(self, *arg, **kwargs):
        super(TranslateParamsPreProcess, self).__init__(*arg, **kwargs)

    def _PreCheck(self):
        pass

    @ParamsPreProcessBase.decorator    
    def ParamsPreProcess(self):
        def parsemodelparams(modelparams):
            return modelparams.split("/")

        p1 = [self.restopic, self.uuid]
        p2 = parsemodelparams(self.modelparams)
        return [p1, p2]

def GetParamsPreProcesscls(config, message):
    uuid, funname, modelparams, restopic = message.split("_")
    classname = funname.split("-")[-1] + "ParamsPreProcess"
    module = importlib.import_module("paramspreprocess")
    return getattr(module,classname)(config, uuid, funname, modelparams, restopic)