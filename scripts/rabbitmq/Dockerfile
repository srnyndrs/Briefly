FROM rabbitmq:3-management-alpine

ENV RABBITMQ_CONFIG_FILES=/etc/rabbitmq/conf.d

COPY 90-content-definitions.conf /etc/rabbitmq/conf.d/90-content-definitions.conf
COPY content-dlq.json /etc/rabbitmq/content-dlq.json
