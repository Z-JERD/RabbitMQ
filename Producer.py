"""生产者，发送数据"""

import pika
import uuid

class ProducerObj(object):

    def __init__(self,host):
        """建立与RabbitMQ服务器"""
        self.host = host
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
        self.channel = self.connection.channel()


    def one_on_one(self,message,queue):
        """一对一消费  一个生产者一个消费者
        确保收件人队列存在。如果我们向不存在的位置发送消息，RabbitMQ将丢弃该消息。让创建一个向其传递消息的队列"""
        self.channel.queue_declare(queue=queue)
        #routing_key指定消息应该去哪个队列
        self.channel.basic_publish(exchange='',routing_key=queue,body=message)
        print(" [x] Sent 'Hello World!'")
        #关闭连接实现刷新网络缓冲区
        self.connection.close()

    def one_on_many(self,message,queue):
        """一个生产者对应多个消费者"""
        self.channel.queue_declare(queue=queue)
        #routing_key指定消息应该去哪个队列
        self.channel.basic_publish(exchange='',routing_key=queue,body=message)
        print(" [x] Sent 'Hello World!'")
        #关闭连接实现刷新网络缓冲区
        self.connection.close()
        #执行任务
        '''
        python new_task.py First message.
        python new_task.py Second message..
        python new_task.py Third message...
        python new_task.py Fourth message....
        python new_task.py Fifth message.....
        
        '''

    def one_on_many_persistence(self,message,queue):
        """一个生产者对应多个消费者 开启队列和消息的持久性"""
        self.channel.queue_declare(queue='hello', durable=True)
        # 打开通道的确认模式
        #self.channel.confirm_delivery()
        self.channel.basic_publish(exchange='',
                                   routing_key=queue,
                                   body=message,
                                   properties=pika.BasicProperties(
                                       delivery_mode=2,  # make message persistent
                                   ))
        print(" [x] Sent 'Hello World!'")
        # 关闭连接实现刷新网络缓冲区
        self.connection.close()

    def publish_subscribe(self,message):
        """发布订阅模式 定义交换类型 exchange_type='fanout
          它将收到的所有消息广播到它知道的所有队列中'
        """
        #声明交换类型
        self.channel.exchange_declare(exchange='logs',exchange_type='fanout')
        self.channel.basic_publish(exchange='logs',
                                   routing_key='',
                                   body=message
                                  )
        print(" [x] Sent 'Hello World!'")
        self.connection.close()

    def keyword_routing(self,severity,message):
        """关键字指定路由匹配 有选择地接收消息
            交换类型:exchange_type='direct'
            消息进入队列，其  绑定密钥与消息的路由密钥完全匹配
        """
        #定义交换类型为direct 并指定路由
        self.channel.exchange_declare(exchange='direct_logs',
                                      exchange_type='direct'
                                      )
        self.channel.basic_publish(exchange='direct_logs',
                                   routing_key=severity,
                                   body=message)
        print(" [x] Sent %r:%r" % (severity, message))
        self.connection.close()

    def fuzzy_matching(self,severity,message):
        """模糊匹配  交换类型exchange_type='topic'
            例：severitry = "kern.*"
                severitry = "*.critical"
                severitry = "#"
        """
        self.channel.exchange_declare(exchange='topic_logs',
                                 exchange_type='topic')

        self.channel.basic_publish(exchange='topic_logs',
                              routing_key=severity,
                              body=message)
        print(" [x] Sent %r:%r" % (severity, message))
        self.connection.close()

    def on_response(self,ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def rpc_deal(self, message):
        """ RPC 客户端发送请求消息，服务器回复响应消息。为了接收响应，客户端需要发送带有请求的“回调”队列地址"""
        #定义回调队列
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue
        self.corr_id = str(uuid.uuid4())
        self.response = None

        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=message
        )
        while self.response is None:
            self.connection.process_data_events()
        return int(self.response)




