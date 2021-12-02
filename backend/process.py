import modelimplement
import myglobal
from kafkawrap.kafkamessage import kafkamodelwrap
from ftplib import FTP, error_perm
from pathlib import Path
import time
import os

class FTPWrap():
    def __init__(self, config):
        host, user, passwd, self.requestdir, self.responsedir = config["FTPConfig"]["host"], config["FTPConfig"]["user"], \
            config["FTPConfig"]["passwd"], config["FTPConfig"]["requestdir"], config["FTPConfig"]["responsedir"]
        self.ftp = FTP(host=host, user=user, passwd=passwd)
        self.ftp.set_pasv(False)
        self.localrequestdir = config["LocalRequestDir"]
        self.localresponsedir = config["LocalResponseDir"]

    def __del__(self):
        self.ftp.quit()

    def DownLoadFile(self, funname, modelparams):
        if(funname == "StyleTransfer-WCT" or funname == "StyleTransfer-AdaIN"):
            return self.__DownLoadWCTAdaIN__(modelparams)
        elif(funname == "StyleTransfer-Fast"):
            return self.__DownLoadFast__(modelparams)
        elif(funname == "TextToSpeech"):
            return self.__DownLoadTextToSpeech__(modelparams)
        elif(funname == "Translate"):
            return self.__DownLoadTranslate__(modelparams)

    def __DownLoadWCTAdaIN__(self, modelparams):
        content, style, alpha = modelparams.split(":")
        contentfilepath = Path(self.localrequestdir).joinpath(content)
        stylefilepath = Path(self.localrequestdir).joinpath(style)
        os.makedirs(contentfilepath.parent, exist_ok=True)
        
        self.ftp.cwd(self.requestdir)
        with open(contentfilepath,"wb") as fp:
            self.ftp.retrbinary("RETR " + content, fp.write)
        with open(stylefilepath,"wb") as fp:
            self.ftp.retrbinary("RETR " + style, fp.write)
        return [str(contentfilepath), str(stylefilepath), alpha]

    def __DownLoadFast__(self, modelparams):
        content, style = modelparams.split(":")
        contentfilepath = Path(self.localrequestdir).joinpath(content)
        os.makedirs(contentfilepath.parent, exist_ok=True)
        
        self.ftp.cwd(self.requestdir)
        with open(contentfilepath,"wb") as fp:
            self.ftp.retrbinary("RETR " + content, fp.write)
        return [str(contentfilepath), style]

    def __DownLoadTextToSpeech__(self, modelparams):
        return modelparams.split(":")

    def __DownLoadTranslate__(self, modelparams):
        return modelparams

    def UpLoadFile(self, funname, message):
        if(funname == "StyleTransfer-WCT" or funname == "StyleTransfer-AdaIN" 
            or funname == "StyleTransfer-Fast" or funname == "TextToSpeech"):
            self.__UpLoadFile__(message)

    def __UpLoadFile__(self, message):
        remoteresponsepath = message.split("_")[-1]
        transferedfilepath = Path(self.localresponsedir).joinpath(remoteresponsepath)
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

    def __init__(self, ftpwrap):
        self.models = {}
        self.ftpwrap = ftpwrap

    def __FtpDownload__(self, funname, modelparams):
        return self.ftpwrap.DownLoadFile(funname, modelparams)

    def __FtpUpload__(self, funname, modelparams):
        return self.ftpwrap.UpLoadFile(funname, modelparams)

    def DealWithMessage(self, messages):
        tasks = {}
        for message in messages:
            uuid, funname, modelparams, restopic = message.split("_")
            modelparams = self.__FtpDownload__(funname, modelparams)
            if funname in tasks:
                tasks[funname] += [myglobal.InParams(uuid, modelparams, restopic)]
            else:
                tasks[funname] = [myglobal.InParams(uuid, modelparams, restopic)]

        res = []
        for name in tasks:
            model = self.__GetModelImpl(name)
            if(model.name != "None"):
                res += model.Eval(tasks[name])
                self.__FtpUpload__(name, res[-1][-1])
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


