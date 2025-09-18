#!/bin/bash

kubectl delete -f deploy/client/client.yaml
kubectl delete -f deploy/server/server.yaml
kubectl delete -f deploy/processor/processor.yaml
kubectl delete -f deploy/producer/producer.yaml
kubectl delete -f deploy/kafka/kafka.yaml
kubectl delete -f deploy/redis/redis.yaml

kubectl apply -f deploy/redis/redis.yaml
kubectl apply -f deploy/kafka/kafka.yaml
kubectl apply -f deploy/producer/producer.yaml

sleep 15
kubectl apply -f deploy/processor/processor.yaml

kubectl apply -f deploy/server/server.yaml
kubectl apply -f deploy/client/client.yaml