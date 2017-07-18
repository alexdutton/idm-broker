import threading

from idm_broker.consumer import BrokerTaskConsumer


class BrokerTaskConsumerTestCaseMixin(object):
    def setUp(self):
        self.broker_task_consumer = BrokerTaskConsumer()
        self.broker_task_consumer_thread = threading.Thread(target=self.broker_task_consumer)
        self.broker_task_consumer_thread.start()
        super().setUp()

    def tearDown(self):
        self.broker_task_consumer.should_stop = True
        self.broker_task_consumer_thread.join()
        super().tearDown()

