"""消费者，消费数据"""

import pika
import time

class ConsumerObj(object):

    def __init__(self,host):
        """建立与RabbitMQ服务器"""
        self.host = host
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
        self.channel = self.connection.channel()

    def callback(self,ch,method,properties,body):
        """一个生产者对应一个消费者收到消息时，Pika库都会调用此回调函数"""
        print(" [x] Received %r" % body)


    def callback_loop(self,ch, method, properties, body):
        """一个生产者对应多个消费者  循环调度
            默认情况下，RabbitMQ将按顺序将每条消息发送给下一个消费者。
            平均而言，每个消费者将获得相同数量的消息。这种分发消息的方式称为循环法
            即A拿完B拿,B的数据处理结束,A的数据未结束,B等着A结束取完数据后
            """
        print(" [x] Received %r" % body)
        time.sleep(body.count('.'))
        print(" [x] Done")
        #启动多个消费者
        '''
            消费者1：python worker.py
            #=> [*] Waiting for messages. To exit press CTRL+C
            # => [x] Received 'First message.'
            # => [x] Received 'Third message...'
            # => [x] Received 'Fifth message.....'
            消费者2：python worker.py
            # => [*] Waiting for messages. To exit press CTRL+C
            # => [x] Received 'Second message..'
            # => [x] Received 'Fourth message....'
        '''

    def callback_fair(self,ch, method, properties, body):
        """一个生产者对应多个消费者 公平调度
            谁来谁取(谁有空谁处理)不再按照奇偶数排列"""
        print(" [x] Received %r" % body)
        time.sleep(body.count('.'))
        print(" [x] Done")
        self.channel.basic_qos(prefetch_count=1)

    def one_on_one(self,queue):
        """一对一的消费
            为了保证从queue中能取到数据，需要保证队列存在，因此创建队列
            ack是标记 消费者拿走数据后必须返回一个标记,得到这个标记就删掉。否则数据一直存在
            no_ack=True 一旦RabbitMQ向客户发送消息，它立即将其标记为删除
        """
        self.channel.queue_declare(queue=queue)
        self.channel.basic_consume(consumer_callback = self.callback,queue=queue,no_ack=True)
        print(' [*] Waiting for messages. To exit press CTRL+C')
        #进入一个永无止境的循环
        self.channel.start_consuming()

    def one_on_many(self,queue):
        """一个生产者对应多个消费者"""
        self.channel.queue_declare(queue=queue)
        self.channel.basic_consume(consumer_callback=self.callback_loop, queue=queue, no_ack=True)
        print(' [*] Waiting for messages. To exit press CTRL+C')
        # 进入一个永无止境的循环
        self.channel.start_consuming()

    def one_on_many_ack(self,queue):
        """一个生产者对应多个消费者 开启消息确认 消息持久性 和公平派遣(谁来谁消费)"""
        self.channel.queue_declare(queue=queue, durable=True)
        self.channel.basic_consume(consumer_callback=self.callback_fair, queue=self.queue)
        self.channel.start_consuming()

    def publish_subscribe(self):
        """发布订阅模式 定义交换类型 交换名称和交换类型和生产者中的保持一致
          创建一个随机名称的队列
        """
        # 1.声明交换类型
        self.channel.exchange_declare(exchange='logs', exchange_type='fanout')
        #2.创建随机的队列，关闭消费者连接后，队列自动删除
        result = self.channel.queue_declare(exclusive=True)
        queue_name = result.method.queue #获取队列名称
        #3.将队列和exchange绑定
        self.channel.queue_bind(exchange='logs',queue=queue_name)
        print(' [*] Waiting for logs. To exit press CTRL+C')
        #4.消费者消费调用回调函数
        self.channel.basic_consume(consumer_callback=self.callback,queue=queue_name)
        #5.监听队列中是否有消息
        self.channel.start_consuming()

    def keyword_routing(self,severities=None):
        """关键字指定路由匹配 有选择地接收消息"""
        # 1.声明交换类型
        self.channel.exchange_declare(exchange='direct_logs', exchange_type='direct')
        # 2.创建随机的队列，关闭消费者连接后，队列自动删除
        result = self.channel.queue_declare(exclusive=True)
        queue_name = result.method.queue  # 获取队列名称
        # 3.将队列和exchange绑定
        if not severities:
            print("Usage: %s [info] [warning] [error]\n")
            return 1
        for severity in severities:
            #一个队列对应一个获多个路由
            self.channel.queue_bind(exchange='direct_logs', queue=queue_name,routing_key=severity)
        print(' [*] Waiting for logs. To exit press CTRL+C')
        # 4.消费者消费调用回调函数
        self.channel.basic_consume(consumer_callback=self.callback, queue=queue_name)
        # 5.监听队列中是否有消息
        self.channel.start_consuming()

    def fuzzy_matching(self,severities=None):
        """模糊匹配  交换类型exchange_type='topic'
            severities = [kern.g "a.critical"]
        """
        self.channel.exchange_declare(exchange='topic_logs',
                                 exchange_type='topic')

        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue
        if not severities:
            print("Usage: %s [info] [warning] [error]\n")
            return 1
        for severity in severities:
            self.channel.queue_bind(exchange='topic_logs',
                               queue=queue_name,
                               routing_key=severity)

        self.channel.basic_consume(callback,
                              queue=queue_name,
                              no_ack=True)

        self.channel.start_consuming()

    def rpc_deal(self, message):
        """RPC 客户端发送请求消息，服务器回复响应消息。为了接收响应，客户端需要发送带有请求的“回调”队列地址"""

        def on_request(ch, method, props, body):
            n = int(body)
            print(" [.] fib(%s)" % n)
            response = 'HELLO WORLD'

            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties(correlation_id= \
                                                                 props.correlation_id),
                             body=response)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(on_request, queue='rpc_queue')
        print(" [x] Awaiting RPC requests")
        self.channel.start_consuming()
