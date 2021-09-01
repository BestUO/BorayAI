import myglobal
import json
from kafka.simplewrap import SimpleWrapKafka
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
    if not os.path.exists(conf_json["backendlogpath"]):
        os.makedirs(conf_json["backendlogpath"])
    logfilename = conf_json["backendlogpath"] + "BorayAI_Backend.log"
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

    kafka = SimpleWrapKafka(conf_json)
    """
    message type:
    functionname_uuid_contentpath:stylepath:alpha_middlewarechannel
    filename:
    middlewarechannel-uuid-content/style/result.jpg
    """
    for n in range(1):
    #     kafka.PutMessage(
    #         "StyleTransfer-WCT",
    #         "StyleTransfer-WCT_1234568_20210402/192168001007-1234566-content.jpg:20210402/192168001007-1234566-style.jpg:0.8_192168001007")
        # kafka.PutMessage(
        #     "StyleTransfer-AdaIN",
        #     "StyleTransfer-AdaIN_1234566_20210402/192168001007-1234566-content.jpg:20210402/192168001007-1234566-style.jpg:0.8_192168001007")
        # kafka.PutMessage(
        #     "StyleTransfer-Fast",
        #     "StyleTransfer-Fast_1234566_20210402/192168001007-1234566-content.jpg:faststyle2_192168001007")
        kafka.PutMessage(
            "TextToSpeech",
            "TextToSpeech_1234566_have a good day:en:0_192168001007")

    p = process.Process()
    kafka.GetMessage(p.DealWithMessage, conf_json["BatchSize"])
    myglobal.get_logger.removeHandler(log_file_handler)


if __name__ == "__main__":
    main()
