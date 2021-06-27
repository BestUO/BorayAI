import modelimplement
import myglobal

class Process:

    def __init__(self):
        self.models = {}

    def DealWithMessage(self, messages):
        tasks = {}
        for message in messages:
            fun, uuid, modelparams, topic = message.split("_")
            if fun in tasks:
                tasks[fun] += [myglobal.InParams(uuid, modelparams, topic)]
            else:
                tasks[fun] = [myglobal.InParams(uuid, modelparams, topic)]

        # model = myglobal.get_model()
        res = []
        for name in tasks:
            model = self.__GetModelImpl(name)
            # if model.name != name:
            #     myglobal.set_model(self.__GetModelImpl(name))
            #     model = myglobal.get_model()
            if(model.name != "None"):
                res += model.Eval(tasks[name])
        return res

    def __GetModelImpl(self, funname):
        return self.__FindModelInMap(funname)
    
    def __FindModelInMap(self,funname):
        if funname not in self.models:
            if funname == "StyleTransfer-WCT":
                self.models[funname] = modelimplement.StyleTransferWCT()
            elif funname == "StyleTransfer-AdaIN":
                self.models[funname] = modelimplement.StyleTransferAdaIN()
            elif funname == "StyleTransfer-Fast":
                self.models[funname] = modelimplement.StyleTransferFast()
            elif funname == "TextToSpeech":
                self.models[funname] = modelimplement.FastSpeech()
            else:
                self.models[funname] = modelimplement.StyleTransferNone()
        return self.models[funname]
