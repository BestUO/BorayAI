from confluent_kafka import Producer
from confluent_kafka import Consumer
import myglobal


class SimpleWrapKafka:

    def __init__(self, config):

        self.topics, self.kafkaservers, self.groupid = self.__GetConfig(config)
        self.producers = self.__CreateProducer()
        self.consumers = self.__CreateConsumer()

    def __del__(self):
        for consumer in self.consumers:
            consumer.close()

    def AddProducer(self):
        self.producers += self.__CreateProducer()

    def PutMessage(self, topic, message):
        for p in self.producers:
            p.poll(0)
            p.produce(topic,
                      message.encode('utf-8'),
                      callback=self.__delivery_report)
            p.flush()

    def AddConsumer(self):
        self.consumers += self.__CreateConsumer()

    def GetMessage(self, cbfun, batchsize):
        for consumer in self.consumers:
            self.__ConsumerFun(consumer, cbfun, batchsize)

    def __ConsumerFun(self, consumer, cbfun, batchsize):
        while True:
            batch = batchsize
            messages = []
            while batch:
                msg = consumer.poll(1.0)
                if msg is None:
                    break
                elif msg.error():
                    myglobal.get_logger().error("Consumer error: {}".format(msg.error()))
                    continue
                else:
                    messages += [msg.value().decode('utf-8')]
                    batch -= 1
            if len(messages):
                res = cbfun(messages)
                for topic, message in res:
                    self.PutMessage(topic, message)
                    myglobal.get_logger().info("send message:"+message)

    def __CreateConsumer(self):
        c = Consumer({
            'bootstrap.servers': self.__GetBrokersString(self.kafkaservers),
            'group.id': self.groupid,
            'auto.offset.reset': 'earliest'
        })
        c.subscribe(self.topics["FunctionTopic"])
        return [c]

    def __GetConfig(self, topics):
        return {
            "FunctionTopic": topics["FunctionTopic"],
            "MiddlewareTopic": topics["MiddlewareTopic"]
        }, topics["bootstrap.servers"], topics["GroupID"]

    def __GetBrokersString(self, tmplist):
        return ",".join(tmplist)

    def __CreateProducer(self):
        return [Producer({'bootstrap.servers': self.__GetBrokersString(self.kafkaservers)})]

    def __delivery_report(self, err, msg):
        """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
        if err is not None:
            myglobal.get_logger().error('Message delivery failed: {}'.format(err))
        else:
            myglobal.get_logger().info('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))
