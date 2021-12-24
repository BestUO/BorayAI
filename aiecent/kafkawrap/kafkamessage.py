from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import logging

class kafkamodelwrap:

    def __init__(self, config):

        functiontopics, kafkaservers, group_id = self.__GetConfig(config)
        self.producers = self.__CreateProducer(kafkaservers)
        self.consumers = self.__CreateConsumer(functiontopics=functiontopics, group_id=group_id, bootstrap_servers=kafkaservers)

    def __GetConfig(self, config):
        return config["RequestTopic"], config["BootstrapServers"], config["GroupID"]

    def __CreateConsumer(self, functiontopics, group_id, bootstrap_servers):
        # consumers =KafkaConsumer(group_id=group_id,
        #                     bootstrap_servers=bootstrap_servers,
        #                     value_deserializer=lambda m: json.loads(m.decode('ascii')),
        #                     heartbeat_interval_ms=30)
        consumers =KafkaConsumer(group_id=group_id,
                            bootstrap_servers=bootstrap_servers,
                            heartbeat_interval_ms=30)
        consumers.subscribe(functiontopics)
        return consumers

    def __CreateProducer(self, kafkaservers):
        # producer = KafkaProducer(bootstrap_servers=kafkaservers,value_serializer=lambda v: json.dumps(v).encode("ascii"))
        producer = KafkaProducer(bootstrap_servers=kafkaservers)
        return producer

    def PutMessage(self, topic, message):
        future = self.producers.send(topic, message.encode())

        # Block for 'synchronous' sends
        try:
            record_metadata = future.get(timeout=10)
        except KafkaError as e:
            # Decide what to do if produce request failed...
            logging.getLogger("aiecent").info(e)
            pass

        # Successful result returns assigned partition and offset
        logging.getLogger("aiecent").info("topic:{topic}\t partition:{partition} \t offset:{offset}".format(
            topic = record_metadata.topic, partition=record_metadata.partition, offset=record_metadata.offset))
        logging.getLogger("aiecent").info("send message:"+message)

    def __DealWithMessage(self, messages, cbfun):
        res = cbfun(messages)
        for topic, message in res:
            self.PutMessage(topic, message)

    def GetMessage(self, cbfun, batchsize):
        for message in self.consumers:
            logging.getLogger("aiecent").info("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                                message.offset, message.key,
                                                message.value.decode()))
            self.__DealWithMessage([message.value.decode()], cbfun)

if __name__ == "__main__":
    pass