## What is Event-Driven Architecture (EDA)?
- Event-Driven Architecture is a software architecture in which different components communicate with each other through events.

- Instead of one service directly calling another service and waiting for its response, a service publishes an event when something happens. Other services can listen for that event and perform their own tasks.

## Main components of EDA
1. Producer
Service that generates an event.
Example: Doctor Service.
2. Message Broker
Receives and distributes events.
Examples: RabbitMQ, Apache Kafka.
3. Consumer
Service that receives and processes events.
Example: Notification Service.

## Synchronous vs Event-Driven Architecture
### Synchronous communication
- Doctor Service directly calls Notification Service.
```
Doctor Service
      |
      | HTTP Request
      v
Notification Service
      |
      | Response
      v
Doctor Service
```
- Drawback of Synchronous: Doctor Service waits for Notification Service to respond.

### Event-Driven communication
```
Doctor Service
      |
      | Publish Event
      v
   RabbitMQ
      |
      | Consume Event
      v
Notification Service
```

Doctor Service doesn't need to wait for notification processing.

### What is Reverse Proxy?
- A Reverse Proxy is a server that sits between clients and backend servers. It receives client requests, forwards them to the appropriate backend server, and returns the response to the client.