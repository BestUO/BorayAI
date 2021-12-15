from kafka import producer


def confluent_kafka_consumer_performance():
    import confluent_kafka
    import uuid
    import time

    topic = 'StyleTransfer-WCT'
    msg_consumed_count = 0
    conf = {'bootstrap.servers': '47.94.2.209:9092',
            'group.id': uuid.uuid1(),
            'session.timeout.ms': 6000,
            'default.topic.config': {
                'auto.offset.reset': 'earliest'
            }
            }

    consumer = confluent_kafka.Consumer(**conf)

    consumer_start = time.time()
    # This is the same as pykafka, subscribing to a topic will start a background thread
    consumer.subscribe([topic])

    while True:
        msg = consumer.poll(1)
        if msg:
            msg_consumed_count += 1
            print(msg)

        if msg_consumed_count >= 10:
            break

    consumer_timing = time.time() - consumer_start
    consumer.close()
    return consumer_timing


def kpython():
    from kafka import KafkaConsumer
    import json

    consumer = KafkaConsumer('127.0.0.1',
                            group_id='work1',
                            bootstrap_servers=['47.94.2.209:9092'])
    for message in consumer:
        # message value and key are raw bytes -- decode if necessary!
        # e.g., for unicode: `message.value.decode('utf-8')`
        print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                            message.offset, message.key,
                                            message.value))

    # consume earliest available messages, don't commit offsets
    # KafkaConsumer(auto_offset_reset='earliest', enable_auto_commit=False)

    # # consume json messages
    # KafkaConsumer(value_deserializer=lambda m: json.loads(m.decode('ascii')))

    # # consume msgpack
    # KafkaConsumer(value_deserializer=msgpack.unpackb)

    # # StopIteration if no message after 1sec
    # KafkaConsumer(consumer_timeout_ms=1000)

    # # Subscribe to a regex topic pattern
    # consumer = KafkaConsumer()
    # consumer.subscribe(pattern='^awesome.*')

    # # Use multiple consumers in parallel w/ 0.9 kafka brokers
    # # typically you would run each on a different server / process / CPU
    # consumer1 = KafkaConsumer('my-topic',
    #                         group_id='my-group',
    #                         bootstrap_servers='my.server.com')
    # consumer2 = KafkaConsumer('my-topic',
    #                         group_id='my-group',
    #                         bootstrap_servers='my.server.com')


def test():
    from kafka import KafkaProducer
    import json

    producer = KafkaProducer(bootstrap_servers=["47.94.2.209:9981"],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),security_protocol="PLAINTEXT")
    acc_ini=523416
    print("OK")
    producer.send("StyleTransfer-WCT","acc")
    # producer.flush()

if __name__ == "__main__":
    test()
    # kpython()
    # time_span = confluent_kafka_consumer_performance()
    # print(time_span)