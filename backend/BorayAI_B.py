import myglobal
import json
from kafkawrap.kafkamessage import kafkamodelwrap
from modelimplement import StyleTransferWCT
import process
import logging
from logging.handlers import TimedRotatingFileHandler
# import re
import os


def main():
    filename = "../config.json"
    with open(filename) as f:
        conf_json = json.load(f)
    if not os.path.exists(conf_json["LogPath"]):
        os.makedirs(conf_json["LogPath"])
    logfilename = conf_json["LogPath"] + "BorayAI_Backend.log"
    logformat = "%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"

    formatter = logging.Formatter(logformat)
    log_file_handler = TimedRotatingFileHandler(filename=logfilename, when="D", interval=1, backupCount=30)
    # log_file_handler.suffix = "%Y-%m-%d_%H-%M.log"
    # log_file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}.log$")
    log_file_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.addHandler(log_file_handler)

    myglobal.set_logger(logger)
    myglobal.set_model(StyleTransferWCT())

    ftp = process.FTPWrap(conf_json)
    p = process.Process(ftp, conf_json)
    # ftp.DownLoadFile("StyleTransfer-WCT", "20211117/StyleTransfer-WCT/uuid-content.jpg:20211117/StyleTransfer-WCT/uuid-style.jpg:0.8")
    # ftp.UpLoadFile("StyleTransfer-WCT", "20211117/StyleTransfer-WCT/uuid-styletransfered.jpg")
    kafka = kafkamodelwrap(conf_json)

    # for n in range(1):
    # kafka.PutMessage(
    #     "StyleTransfer-WCT",
    #     "uuid_StyleTransfer-WCT_20211117/StyleTransfer-WCT/uuid-content.jpg:20211117/StyleTransfer-WCT/uuid-style.jpg:0.8_047094002209")
    # kafka.PutMessage(
    #     "StyleTransfer-AdaIN",
    #     "uuid_StyleTransfer-AdaIN_20211117/StyleTransfer-AdaIN/uuid-content.jpg:20211117/StyleTransfer-AdaIN/uuid-style.jpg:0.8_047094002209")
    # kafka.PutMessage(
    #     "StyleTransfer-Fast",
    #     "uuid_StyleTransfer-Fast_20211117/StyleTransfer-Fast/uuid-content.jpg:faststyle1_047094002209")
    # kafka.PutMessage(
    #     "TextToSpeech",
    #     "uuid_TextToSpeech_have a good day:en:0_047094002209")
    # kafka.PutMessage(
    #     "Translate",
    #     "uuid_Translate_今天是个好天气_047094002209")

    kafka.GetMessage(p.DealWithMessage, conf_json["BatchSize"])
    logger.removeHandler(log_file_handler)

    

if __name__ == "__main__":
    main()
