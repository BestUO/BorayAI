import requests
import asyncio
from pathlib import Path
import os
import time
import modelimplement
import logging

class BaseDecorator:
    # @classmethod
    # def ReconnnectIfTimeout(cls,fun):
    #     def wrap(self,*arg,**kwargs):
    #         try:
    #             self.ftp.cwd(self.requestdir)
    #         except(error_perm, error_temp) as e:
    #             self.ftp.connect(host=self.host,timeout=120)
    #             self.ftp.login(user=self.user, passwd=self.passwd)
    #             self.ftp.set_pasv(False)
    #         fun(self,*arg,**kwargs)
    #     return wrap

    @staticmethod
    def MkdirByDay(fun):
        def wrap(conf_json, queuename, *arg,**kwargs):
            requestdirpath = Path(conf_json["LocalRequestDir"]).joinpath(time.strftime("%Y%m%d", time.localtime()),queuename)
            os.makedirs(requestdirpath, exist_ok=True)

            responsedirpath = Path(conf_json["LocalResponseDir"]).joinpath(time.strftime("%Y%m%d", time.localtime()),queuename)
            os.makedirs(responsedirpath, exist_ok=True)

            return fun(*arg,**kwargs)+[requestdirpath]+[responsedirpath]
        return wrap

class ParseMessage:
    @staticmethod
    def ParseRedisMessage(conf_json, queuename, message):
        return getattr(ParseMessage,"ParseRedisMessage_"+ queuename)(conf_json, queuename, message)

    @staticmethod
    def GenerateTask(conf_json, queuename, params):
        return getattr(ParseMessage,"GenerateTask_"+ queuename)(conf_json, params)

    @staticmethod
    def ParseRedisMessage_StyleTransfer_WCT_AdaIN(message):
        [uuid,functionname,params] = message.split("-")
        [sourceimgurl,styleimgurl,alpha] = params.split("#")
        return [uuid,functionname,[sourceimgurl,styleimgurl,alpha]]

    @staticmethod
    def GenerateTask_StyleTransfer_WCT_AdaIN(params):
        downloadfiles = []
        [uuid,functionname,[sourceimgurl,styleimgurl,alpha],requestdirpath,responsedirpath] = params

        sourceimgname = requestdirpath.joinpath(sourceimgurl.split("/")[-1])
        if(not sourceimgname.exists()):
            downloadfiles += [[sourceimgurl,sourceimgname]]

        styleimgname = requestdirpath.joinpath(styleimgurl.split("/")[-1])
        if(not styleimgname.exists()):
            downloadfiles += [[styleimgurl,styleimgname]]

        resultimgname = responsedirpath.joinpath(uuid+"_result.jpg")

        evaltask = [[sourceimgname,styleimgname,alpha,resultimgname]]

        return [downloadfiles,evaltask]

    @staticmethod
    @BaseDecorator.MkdirByDay
    def ParseRedisMessage_StyleTransfer_WCT(message):
        return ParseMessage.ParseRedisMessage_StyleTransfer_WCT_AdaIN(message)

    @staticmethod
    def GenerateTask_StyleTransfer_WCT(conf_json, params):
        return ParseMessage.GenerateTask_StyleTransfer_WCT_AdaIN(params)

    @staticmethod
    @BaseDecorator.MkdirByDay
    def ParseRedisMessage_StyleTransfer_AdaIN(message):
        return ParseMessage.ParseRedisMessage_StyleTransfer_WCT_AdaIN(message)

    @staticmethod
    def GenerateTask_StyleTransfer_AdaIN(conf_json, params):
        return ParseMessage.GenerateTask_StyleTransfer_WCT_AdaIN(params)

    @staticmethod
    @BaseDecorator.MkdirByDay
    def ParseRedisMessage_StyleTransfer_Fast(message):
        [uuid,functionname,params] = message.split("-")
        [sourceimgurl,stylename] = params.split("#")
        return [uuid,functionname,[sourceimgurl,stylename]]

    @staticmethod
    def GenerateTask_StyleTransfer_Fast(conf_json, params):
        downloadfiles = []
        [uuid,functionname,[sourceimgurl,stylename],requestdirpath,responsedirpath] = params

        sourceimgname = requestdirpath.joinpath(sourceimgurl.split("/")[-1])
        if(not sourceimgname.exists()):
            downloadfiles += [[sourceimgurl,sourceimgname]]

        modelpath = conf_json["StyleTransfer_Fast"][stylename]

        resultimgname = responsedirpath.joinpath(uuid+"_result.jpg")

        evaltask = [[sourceimgname,modelpath,resultimgname]]
        return [downloadfiles,evaltask]

    @staticmethod
    async def DownloadFile(asyncioloop, url, newname):
        future = asyncioloop.run_in_executor(None,requests.get, url)
        response = await future
        with open(newname,"wb") as file:
            file.write(response.content)

    @staticmethod
    def DealWithMessages(conf_json, queuename, messages):
        downloadtasks = []
        evaltasks = []
        asyncioloop = asyncio.get_event_loop()
        for message in messages:
            params = ParseMessage.ParseRedisMessage(conf_json, queuename, str(message,"utf-8"))
            [downloadfiles,evaltask] = ParseMessage.GenerateTask(conf_json, queuename, params)
            for [url,filename] in downloadfiles:
                downloadtasks += [ParseMessage.DownloadFile(asyncioloop, url,filename)]

            evaltasks += evaltask
        
        if(len(downloadtasks) > 0):
            asyncioloop.run_until_complete(asyncio.wait(downloadtasks))
        return evaltasks


class EvalByModels:
    def __init__(self):
        self.models = {}

    def __FindModelInMap(self,queuename):
        if queuename not in self.models:
            if queuename == "StyleTransfer_WCT":
                self.models[queuename] = modelimplement.StyleTransferWCT()
            elif queuename == "StyleTransfer_AdaIN":
                self.models[queuename] = modelimplement.StyleTransferAdaIN()
            elif queuename == "StyleTransfer_Fast":
                self.models[queuename] = modelimplement.StyleTransferFast()
            elif queuename == "TextToSpeech":
                self.models[queuename] = modelimplement.FastSpeech()
            elif queuename == "Translate":
                self.models[queuename] = modelimplement.Translate()
            else:
                self.models[queuename] = modelimplement.StyleTransferNone()
        return self.models[queuename]

    def DealWithEvalTasks(self, conf_json, queuename, evaltasks):
        model = self.__FindModelInMap(queuename)
        if(model.name != "None"):
            resultimgnames = model.EvalBatch(evaltasks)
            tasks = []
            asyncioloop = asyncio.get_event_loop()
            uploadurl = "http://{ip}:{port}/api/uploadfile".format(ip = conf_json["HttpServer"]["host"], port = conf_json["HttpServer"]["port"])
            for resultimgname in resultimgnames:
                tasks += [self.__UploadFile(uploadurl,asyncioloop,resultimgname)]
            if(len(tasks) > 0):
                asyncioloop.run_until_complete(asyncio.wait(tasks))

    async def __UploadFile(self, url, asyncioloop, newname):
        asyncioloop.run_in_executor(None, self.__PostFile, url, newname)


    def __PostFile(self, url, newname):
        uploadfile = {
            "filename":(None,newname.name),
            "file":(newname.name,newname.read_bytes(),"image/jpg")
        }
        res = requests.post(url,files = uploadfile)