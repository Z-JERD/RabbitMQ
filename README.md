#### 1.常用的消息中间件：
    1.RabbitMQ、RocketMQ、ActiveMQ、Kafka、ZeroMQ、MetaMQ
    2.Redis MySQL也可是实现消息队列的功能
    其他MQ的优势：
        1.Apache ActiveMQ曝光率最高，但是可能会丢消息。
        2.ZeroMQ延迟很低、支持灵活拓扑，但是不支持消息持久化和崩溃恢复。
        3.Kafka 定位是日志消息队列。吞吐量最大。
        4.Rabbit MQ 是可靠性更强，对数据一致性、稳定性和可靠性要求很高的场景


#### 2.消息队列的特点：
    1.采用异步处理模式
        消息发送者可以发送一个消息而无须等待响应，接收者无需对消息发送者做出同步回应
    2.发送者和接受者不必了解对方、只需要确认消息；
    3.发送者和接受者不必同时在线。

    应用场景：
        1. 支付系统处理完成后会把支付结果放到消息中间件里，通知订单系统修改订单支付状态
        2.短信通知、终端状态推送、App 推送、用户注册

### RabbitMQ: 是一个开源的AMQP实现，服务器端用Erlang语言编写
    官方文档:https://www.rabbitmq.com/
    参考文档：https://www.sojson.com/blog/48.html
              AMQP介绍https://blog.csdn.net/qq_33314107/article/details/80172042
    #### 1.RabbitMQ的组成
            队列服务：由发消息者(生产者)，队列和收消息者(消费者)组成
            RabbitMQ：生产者---RabbitMQ(交换器---队列)---消费者
                      在队列的基础上多做了一层抽象，在生产者和队列之间加入交换器(Exchange)，生产者和队列没有直接的联系
                      生产者把消息发送给交换器，交换器根据调度策略把消息给队列
    #### 2.AMQP核心概念：消息队列协议，如图AMQP
            在异步通讯中，消息不会立刻到达接收方，而是被存放到一个容器中，当满足一定的条件之后，消息会被容器发送给接收方，
            这个容器即消息队列。而完成这个功能需要双方和容器以及其中的各个组件遵守统一的约定和规则。
            Server：AMQP的服务端称为Broker 接受客户端的链接，实现AMQP实体服务
            Connection：连接，应用程序与Broker的网络连接
            Channel:网络信道，几乎所有的操作都在Channel中进行，它是进行消息读写的通道，客户端可建立多个Channel
                    每个Channel代表一个会话任务
            Message：服务器和应用程序之间传送的数据.由Properties和Body组成。Properties对消息进行修饰，比如指定消息的优先级和延迟等特性。
                     Body这是消息的实体内容
            Virtual host：虚拟地址，最上层的消息路由，一个Virtual Host里面可以有若干个Exchange和Queue
                          同一个Virtual Host里面不能有相同名称的Exchange和Queue
                          一般隔离不同的项目和应用。比如订单的项目和优惠券的项目分别放到不同的Virtual Host中
            Exchange：交换机，接受消息，根据路由键转发消息到绑定的Queue
            Binding：Exchange和Queue之间的虚拟连接
            Routing Key：路由规则，确定如何路由一个特定消息
            Queue:消息队列，保存消息并将它们转发给消费者

        ##### 为什么使用AMQP：
             在分布式的系统中，子系统如果使用socket连接进行通讯，有很多问题需要解决。比如：
             1.信息的发送者和接受者如何维持这个连接，如果一方中断，这期间的数据如何防止丢失？
             2.如何降低发送者和接受者的耦合度？
             3.如何让优先级高的接受者先接到数据？
             4.如何将信息发送到相关的接收者，如果接受者订阅了不同的数据，如何正确的分发到接受者？
             5.如何保证接受者接到了完整，正确或是有序的数据？
             AMQP解决了这些问题。RabbitMQ(AMQP)的优点：1.成熟稳定2.路由策略灵活3.消息传输可靠4.集群方案成熟
    #### 3.AMQP通信流程：
        （1）建立连接Connection。由producer和consumer创建连接，连接到broker的物理节点上。
        （2）建立消息Channel。Channel是建立在Connection之上的，一个Connection可以建立多个Channel。
                producer连接Virtual Host 建立Channel，Consumer连接到相应的queue上建立Channel。
        （3）发送消息。由Producer发送消息到Broker中的exchange中。
        （4）路由转发。exchange收到消息后，根据一定的路由策略，将消息转发到相应的queue中去。
        （5）消息接收。Consumer会监听相应的queue，一旦queue中有可以消费的消息，queue就将消息发送给
                Consumer端。
        （6）消息确认。当Consumer完成某一条消息的处理之后，需要发送一条ACK消息给对应的Queue。
               Queue收到ACK信息后，才会认为消息处理成功，并将消息从Queue中移除；如果在对应的Channel断开后，
               Queue没有收到这条消息的ACK信息，该消息将被发送给另外的Channel。至此一个消息的发送接收流程走完
               了。消息的确认机制提高了通信的可靠性。

    #### 4.RabbitMQ消息的执行流程：如图 rabbitmq-work
            生产者指定路由键和Exchange----Message----Virtual host---Exchange---(根据路由键匹配相对的队列)Queue---消费者(到指定的队列中取值)
            RabbitMQ中消息传递模型的核心思想：
                生产者永远不会将任何消息直接发送到队列。实际上，生产者通常甚至不知道消息是否会被传递到任何队列。
                生产者只能向交易所(Exchange)发送消息

    #### 5.发送方确认模式：确保消息正确地发送至RabbitMQ
            1.当确认模式没有打开时，即使队列和交换机不存在，投递消息返回的都是True;
            2.当确认模式打开时，投递失败会返回False，成功返回True，如果队列不存在，交换机会叫消息丢掉，但不会通知生产者；如果交换机不存在，会报错；
            3.同一个信道，确认模式和事务模式只能存在一个，不能同时启用，否则报错；

    #### 6.RabbitMQ 接收方消息确认(消费者挂掉的措施)：no_ack = False 默认手动消息确认已经打开
           1. 为了确保消息永不丢失，RabbitMQ支持 消息确认。消费者发回ack（nowledgement）告诉RabbitMQ已收到，处理了特定消息，
              RabbitMQ可以自由删除它
           2.如果消费者死亡（其通道关闭，连接关闭或TCP连接丢失）而不发送确认，RabbitMQ将理解消息未完全处理并将重新排队。
             如果同时有其他在线消费者，则会迅速将其重新发送给其他消费者
           3.如果设置no_ack=True 一旦RabbitMQ向客户发送消息，它立即将其标记为删除。在这种情况下，如果杀死消费者
             我们将丢失它刚刚处理的消息


    #### 7.消息的持久性(RabbitMQ挂掉的措施)：
            当RabbitMQ退出或崩溃时，它将忘记队列和消息。确保消息不会丢失需要做两件事：我们需要将队列和消息都标记为持久。
            1.声明队列是持久的
                channel.queue_declare（queue = 'hello'，durable = True）
            2.消息的持久性
                channel.basic_publish(exchange='',
                          routing_key="task_queue",
                          body=message,
                          properties=pika.BasicProperties(
                             delivery_mode = 2, # make message persistent
                          ))


### RabbitMQ分发模式：
        1.一对一：一个生产者对应一个消费者
        2.一对多：一个生产者对应多个消费者。消费者取数据的类型分为：1.循环调度 2.平均分配
        3.发布订阅：
            消息队列中的数据被消费被一次便消失
            RabbitMQ实现发布和订阅时，会为每一个订阅者创建一个队列，而发布者发布消息时，会将消息放置在所有相关队列中
            1.定义交换类型 exchange_type='fanout’进行无意识的广播 它将收到的所有消息广播到它知道的所有队列中
            2.创建队列：每当我们连接到Rabbit时，我们都需要一个新的空队列。要做到这一点，我们可以创建一个随机名称的队列
            3.绑定：绑定是交换和队列之间的关系，简单的理解为 队列对来自此交换的消息感兴趣
        4.关键字发送:指定routing_key
            发送消息时明确指定某个队列并向其中发送消息，有选择地接收消息
            交换类型:exchange_type='direct'

        5.模糊匹配：
            让队列绑定几个模糊的关键字，之后发送者将数据发送到exchange，exchange将传入”路由值“和 ”关键字“进行匹配，
            匹配成功，则将数据发送到指定队列
            原理同关键字发送相同：使用特定路由密钥发送的消息将被传递到与匹配绑定密钥绑定的所有队列。但是绑定键有两个重要的特殊情况：
                *（星号）可以替代一个单词。
                ＃（hash）可以替换零个或多个单词。

        6.RPC:双向通道
            场景：客户端发送消息给服务端,服务端处理完后将结果返回,客户端获取到数据
            处理：客户端往队列1送完数据后,建个新的队列2,服务端在队列1接收数据后,将处理后将结果放到队列2返回,客户端在队列2处接收
            对于RPC请求，客户端发送带有两个属性的消息：  reply_to，设置为回调队列，correlation_id，设置为每个请求的唯一值。
