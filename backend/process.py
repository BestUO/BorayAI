import modelimplement
import myglobal

class Process:

    def __init__(self):
        pass

    def DealWithMessage(self, messages):
        tasks = {}
        for message in messages:
            myglobal.get_logger().info("recv message:"+message)
            fun, uuid, modelparams, topic = message.split("_")
            if fun in tasks:
                tasks[fun] += [myglobal.InParams(uuid, modelparams, topic)]
            else:
                tasks[fun] = [myglobal.InParams(uuid, modelparams, topic)]

        model = myglobal.get_model()
        res = []
        for name in tasks:
            if model.name != name:
                myglobal.set_model(self.__GetModelImpl(name))
                model = myglobal.get_model()
            if(model.name != "None"):
                res += model.Eval(tasks[name])
        return res

    def __GetModelImpl(self, funname):
        if funname == "StyleTransfer-WCT":
            return modelimplement.StyleTransferWCT()
        elif funname == "StyleTransfer-AdaIN":
            return modelimplement.StyleTransferAdaIN()
        elif funname == "StyleTransfer-Fast":
            return modelimplement.StyleTransferFast()
        else:
            return modelimplement.StyleTransferNone()