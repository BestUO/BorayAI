import modelimplement
from kafkawrap.kafkamessage import kafkamodelwrap
from ftplib import FTP, error_perm, error_temp
from pathlib import Path
import os
import paramspreprocess
import logging
import socket

class BaseDecorator:
    @classmethod
    def ReconnnectIfTimeout(cls,fun):
        def wrap(self,*arg,**kwargs):
            try:
                self.ftp.cwd(self.requestdir)
            except(error_perm, error_temp) as e:
                self.ftp.connect(host=self.host,timeout=120)
                self.ftp.login(user=self.user, passwd=self.passwd)
                self.ftp.set_pasv(False)
            fun(self,*arg,**kwargs)
        return wrap


class FTPWrap(BaseDecorator):
    def __init__(self, config):
        self.host, self.user, self.passwd, self.requestdir, self.responsedir = config["FTPConfig"]["host"], config["FTPConfig"]["user"], \
            config["FTPConfig"]["passwd"], config["FTPConfig"]["requestdir"], config["FTPConfig"]["responsedir"]
        self.ftp = FTP(host=self.host, user=self.user, passwd=self.passwd,timeout=120)
        self.ftp.set_pasv(False)
        self.localrequestdir = Path(config["LocalRequestDir"])
        self.localresponsedir = Path(config["LocalResponseDir"])

    def __del__(self):
        self.ftp.quit()

    @BaseDecorator.ReconnnectIfTimeout
    def DownLoadFile(self, funname, modelparams):
        if(funname == "StyleTransfer-WCT" or funname == "StyleTransfer-AdaIN"):
            self.__DownLoadWCTAdaIN__(modelparams)
        elif(funname == "StyleTransfer-Fast"):
            self.__DownLoadFast__(modelparams)
        elif(funname == "TextToSpeech"):
            self.__DownLoadTextToSpeech__(modelparams)
        elif(funname == "Translate"):
            self.__DownLoadTranslate__(modelparams)

    def __DownLoadWCTAdaIN__(self, modelparams):
        contentfilepath, stylefilepath, alpha = modelparams
        content = Path(contentfilepath).relative_to(self.localrequestdir)
        style = Path(stylefilepath).relative_to(self.localrequestdir)

        os.makedirs(Path(contentfilepath).parent, exist_ok=True)
        
        self.ftp.cwd(self.requestdir)
        with open(contentfilepath,"wb") as fp:
            self.ftp.retrbinary("RETR " + str(content), fp.write)
        with open(stylefilepath,"wb") as fp:
            self.ftp.retrbinary("RETR " + str(style), fp.write)

    def __DownLoadFast__(self, modelparams):
        contentfilepath, _ = modelparams
        content = Path(contentfilepath).relative_to(self.localrequestdir)
        os.makedirs(Path(contentfilepath).parent, exist_ok=True)
        
        self.ftp.cwd(self.requestdir)
        with open(contentfilepath,"wb") as fp:
            self.ftp.retrbinary("RETR " + str(content), fp.write)

    def __DownLoadTextToSpeech__(self, modelparams):
        pass

    def __DownLoadTranslate__(self, modelparams):
        pass

    @BaseDecorator.ReconnnectIfTimeout
    def UpLoadFile(self, funname, message):
        if(funname == "StyleTransfer-WCT" or funname == "StyleTransfer-AdaIN" 
            or funname == "StyleTransfer-Fast" or funname == "TextToSpeech"):
            self.__UpLoadFile__(message)

    def __UpLoadFile__(self, message):
        remoteresponsepath = message.split("_")[-1]
        transferedfilepath = self.localresponsedir.joinpath(remoteresponsepath)
        self.ftp.cwd(self.responsedir)
        dirandname = remoteresponsepath.split("/")
        for dir in dirandname[:-1]:
            try:
                self.ftp.cwd(dir)
            except error_perm:
                self.ftp.mkd(dir)
                self.ftp.cwd(dir)
             
        with open(transferedfilepath,"rb") as fp:
            self.ftp.storbinary("STOR " + dirandname[-1], fp)

class Process:

    def __init__(self, ftpwrap, config):
        self.models = {}
        self.ftpwrap = ftpwrap
        self.config = config

    def __FtpDownload__(self, message, *arg, **kwargs):
        self.ftpwrap.DownLoadFile(*arg, **kwargs)
        logging.getLogger("aiecent").info("download finish for message:" + message)

    def __FtpUpload__(self, message, *arg, **kwargs):
        logging.getLogger("aiecent").info("upload finish for message:" + message)
        self.ftpwrap.UpLoadFile(*arg, **kwargs)

    # def DealWithMessage(self, messages):
    #     tasks = {}
    #     try:#err code
    #         for message in messages:
    #             uuid, funname, modelparams, restopic = message.split("_")
    #             # modelparams = self.__FtpDownload__(funname, modelparams)
    #             if funname in tasks:
    #                 tasks[funname] += [myglobal.InParams(uuid, modelparams, restopic)]
    #             else:
    #                 tasks[funname] = [myglobal.InParams(uuid, modelparams, restopic)]

    #         res = []
    #         for name in tasks:
    #             model = self.__GetModelImpl(name)
    #             if(model.name != "None"):
    #                 res += model.Eval(tasks[name])
    #                 self.__FtpUpload__(name, res[-1][-1])
    #         return res
    #     except ValueError:
    #         return [[self.config["DefaultTopic"], "00000000_errparams: " + message]]

    # def DealWithMessage(self, messages):
    #     res = []
    #     for message in messages:
    #         try:
    #             uuid, funname, modelparams, restopic = message.split("_")
    #             modelparams = self.__FtpDownload__(funname, modelparams)
    #             model = self.__GetModelImpl(funname)
    #             if(model.name != "None"):
    #                 res += model.Eval([myglobal.InParams(uuid, modelparams, restopic)])
    #                 self.__FtpUpload__(funname, res[-1][-1])
    #         except ValueError:
    #             res += [[self.config["DefaultTopic"], "00000000_errparams: " + message]]
    #     return res

    def DealWithMessage(self, messages):
        res = []
        for message in messages:
            try:
                paramsprecheck = paramspreprocess.GetParamsPreProcesscls(self.config, message)
                params = paramsprecheck.ParamsPreProcess()

                self.__FtpDownload__(message, paramsprecheck.funname, params[1])

                model = self.__GetModelImpl(paramsprecheck.funname)
                if(model.name != "None"):
                    res += [model.Eval(params)]
                    logging.getLogger("aiecent").info("model.Eval finish for message:"+message)
                    
                    self.__FtpUpload__(message, paramsprecheck.funname, res[-1][-1])

            except (ValueError,AttributeError) as e:
                res += [[self.config["DefaultTopic"], "00000000_errparams: " + message]]
            except error_perm as e:
                res += [[self.config["DefaultTopic"], "00000000_FTPDownloadErr: " + message]]
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
            elif funname == "Translate":
                self.models[funname] = modelimplement.Translate()
            else:
                self.models[funname] = modelimplement.StyleTransferNone()
        return self.models[funname]


