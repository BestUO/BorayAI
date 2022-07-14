from asyncio import get_event_loop
import myglobal
import json
import logging
from logging.handlers import TimedRotatingFileHandler
import os

def ftp_kafka_main(conf_json):
    from kafkawrap.kafkamessage import kafkamodelwrap
    from modelimplement import StyleTransferWCT
    import processfromkafka

    # myglobal.set_logger(logger)
    myglobal.set_model(StyleTransferWCT())

    ftp = processfromkafka.FTPWrap(conf_json)
    p = processfromkafka.Process(ftp, conf_json)
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
    #     "uuid_TextToSpeech_中午吃饭叫上我:zh:0_047094002209")
    # kafka.PutMessage(
    #     "Translate",
    #     "uuid_Translate_今天是个好天气_047094002209")

    kafka.GetMessage(p.DealWithMessage, conf_json["BatchSize"])

def http_redis_main(conf_json):
    import redis
    import time
    import uuid
    from processfromredis import ParseMessage,EvalByModels

    rclient = redis.Redis(host=conf_json["RedisConfig"]["host"],port=conf_json["RedisConfig"]["port"],password=conf_json["RedisConfig"]["passwd"])
    queuename = conf_json["RedisConfig"]["queuename"]
    evalbymodel = EvalByModels()
    while(True):
        messages = rclient.execute_command('LPOP', queuename, conf_json["BatchSize"])
        if(not messages):
            time.sleep(2)
        else:
            taskuuid = uuid.uuid1().hex
            try:
                logging.getLogger("aiecent").info("start uuid: " + taskuuid)
                evaltasks = ParseMessage.DealWithMessages(conf_json, queuename, messages)
                evalbymodel.DealWithEvalTasks(conf_json, queuename, evaltasks)
                logging.getLogger("aiecent").info("end uuid: " + taskuuid)
            except:
                logging.getLogger("aiecent").error("something wrong with uuid:{uuid} message:{messages}".format(uuid=taskuuid, messages=messages))
                continue

if __name__ == "__main__":
    config_file = "./config.json"
    with open(config_file) as f:
        conf_json = json.load(f)
    if not os.path.exists(conf_json["LogPath"]):
        os.makedirs(conf_json["LogPath"])
    logfilename = conf_json["LogPath"] + "BorayAI_Aiecent.log"
    logformat = "%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"

    formatter = logging.Formatter(logformat)
    log_file_handler = TimedRotatingFileHandler(filename=logfilename, when="midnight", interval=1, backupCount=30)
    log_file_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("aiecent")
    logger.addHandler(log_file_handler)

    http_redis_main(conf_json)

    logger.removeHandler(log_file_handler)
