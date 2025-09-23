# Overview

This is a personal project (purely for learning) to briefly explore setting up a few components in a simple producer consumer application. The components include:
1. Producer -> A simple FastAPI microservice which generates a json message representing
an action (in this case 'login') performed by a user. The message is sent to a Kafka broker
2. Kafka Broker -> Used to store messages sent by the producer. The processor component streams messages from the broker 
3. Processor -> A Spark based application which uses structured streaming to pull messages from the kafka broker. It processes the messages, computes the count of a particular action and writes the result to redis
4. Redis -> Used to store the raw data (login information) and the metrics (count of logins)
5. Grpc Server -> A simple grpc server which exposes an api to retrieve the raw data and/or metrics from Redis
6. Grpc Client/Consumer -> A FastAPI microservice which includes a grpc client that interacts with the grpc server to retrieve the raw data and/or metrics

## Structure

The project is structured as follows:
1. client/ -> Includes logic for the grpc client/consumer component
2. db/ -> Includes logic to connect to redis
3. grpc_config/ -> Includes the proto file and generated grpc code
4. processor/ -> Includes logic for the spark based processor component
5. producer/ -> Includes logic for the producer component
6. server/ -> Includes logic for the grpc server component
7. deploy/client -> Includes k8s manifest and Dockerfile for the consumer component
8. deploy/processor -> Includes k8s manifest and Dockerfile for the processor component
9. deploy/producer -> Includes k8s manifest and Dockerfile for the producer component
10. deploy/server -> Includes k8s manifest and Dockerfile for the grpc server component
11. deploy/kafka -> Includes k8s manifest to setup a kafka broker
12. deploy/redis -> Includes k8s manifest to setup a redis instance
13. deploy/ingress_config -> Includes logic to apply the ingress-nginx-controller and setup metallb for load balancing. Note: you may need to configure the pool of IPs in the metallb-config.yaml file based on your local setup

## Prerequisites

1. Python 3.12 (it should work with 3.x versions, but not tested)
2. Colima (on macOS). This setup should work on k3s running directly on a linux machine as well (not tested)
3. Podman or Docker (to build container images)
4. kubectl
5. Helm (to install ingress-nginx-controller)
6. Maven (to retrieve the spark-sql-kafka jar and its dependencies, tested with v3.9.11)
7. Java (to run maven commands, tested with openjdk v17.0.16)

## Manual Deployment Steps (Local with Colima)

1. Ensure you've built all relevant images. For example to build the producer image, run
`podman build -f deploy/producer/Dockerfile -t producer .`. Ensure that the tags match those specified in the corresponding k8s manifest files. Note: You may need to modify the JAVA_HOME path in the processor Dockerfile based on your system architecture (arm64 for apple silicon, amd64 for intel/amd)
2. Save the images as a tar file. For example, to save the producer image, run
`podman save -o producer.tar producer:latest`
3. Start Colima with Kubernetes enabled (skip this step if you already have k3s running on your system) -> `colima start --kubernetes --runtime containerd --cpu 4 --memory 4`
Adjust the cpu and memory based on your system resources (though this could affect the performance of specific components, particularly spark)
4. ssh into the colima VM -> `colima ssh`. Apply the ingress config to setup the ingress-nginx controller and metallb -> `bash deploy/ingress_config/apply_config.sh`
5. Load the images into the k3s cluster runnning on the colima vm -> `sudo ctr -n k8s.io images import <image-name>.tar`
6. Verify the image has been uploaded into the cluster with -> `sudo ctr -n k8s.io images list`
7. Apply the manifests using the start_cluster_local.sh script -> `./start_cluster_local.sh`
8. You may need to reapply the processor component if the pod hasn't started -> `kubectl apply -f deploy/processor/processor.yaml`
9. Verify all pods are running -> `kubectl get pods -A`
10. Retrieve the ingress IP -> `kubectl get svc -A` to identify the EXTERNAL-IP of the ingress-nginx-controller service in the ingress-nginx namespace
11. To test, ssh into the colima vm and run the following 
   - `curl -H "Host: producer.local" http://<INGRESS_IP>/login`. This will generate a login message and pass it on to the other components as stated in the overview section
   -  `curl -H "Host: grpc-client.local" http://<INGRESS_IP>/metrics` to retrieve the count of logins or `curl -H "Host: grpc-client.local" http://<INGRESS_IP>/raw-data` to retrieve the last 10 raw login messages

## Automated Deployment Steps
1. Ensure you have setup a microshift or k3s cluster (note both configurations have been verified only on macos)
2. Refer the gitops repo README (https://github.com/srivathsashreyas/metrics-collector-py-gitops) for steps to install ArgoCD

## Useful Commands (Reference)

1. Create a netshoot pod to test connectivity to other pods/resources using standard network tools (curl, ping, nc etc.)  -> `kubectl run -i --image=nicolaka/netshoot --restart=Never -- bash`
2. Exec into the netshoot pod -> `kubectl exec -it <pod-name> -- bash`
3. Setup a kafka pod with client tools to debug/test the kafka broker ->  `kubectl run kafka-client --restart="Never" --image=confluentinc/cp-kafka:7.6.0 -- sleep infinity`
4. If the pod is already running: `kubectl exec -it kafka-client -- bash`
   Run kafka commands inside the pod:
   -  to list topics - `kafka-topics --bootstrap-server kafka-0.kafka.default.svc.cluster.local:9092 --list`
   -  to consume messages from the 'metrics' topic (refer https://stackoverflow.com/questions/38024514/understanding-kafka-topics-and-partitions for a simple description on partitions in kafka) `kafka-console-consumer --topic metrics --from-beginning --bootstrap-server kafka-0.kafka.default.svc.cluster.local:9092 --partition 0` 
   -  to send messages to the topic 'metrics' - `kafka-console-producer --broker-list kafka-0.kafka.default.svc.cluster.local:9092 --topic metrics`
5. To send requests to the producer service using ingress-nginx, first get the ingress IP using `kubectl get svc -A` to identify the EXTERNAL-IP of the ingress-nginx-controller service in the ingress-nginx namespace. Then, run the following command (replace <INGRESS_IP> with the actual ingress IP):
   `curl -H "Host: producer.local" http://<INGRESS_IP>/login`
Note: If using colima, you'll need to run colima ssh and then run the curl command from within the colima VM.
6. Retrieve jars associated with spark-sql-kafka-0-10_2.13:4.0.0 using the following maven command:
`mvn dependency:copy-dependencies -DoutputDirectory=./jars -DincludeScope=runtime`
This will download the jar and its dependencies to the ./jars directory. 
Note: pom.xml should be present in the current directory with the appropriate dependency specified. Don't forget to download the jar itself from the maven repository using this link -> https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.13/4.0.0/spark-sql-kafka-0-10_2.13-4.0.0.jar or with the mvn dependency:get command. Place this jar in the same directory (./jars) 
7. If using separate spark master and worker nodes -> install bitnami/spark on your cluster with 2 worker pods: 
`helm install spark oci://registry-1.docker.io/bitnamicharts/spark --set worker.replicaCount=2`
8. To upgrade and set resource limits for the spark configuration: 
`helm upgrade spark oci://registry-1.docker.io/bitnamicharts/spark --set worker.replicaCount=2 --set worker.resources.limits.cpu=2 --set worker.resources.limits.memory=4Gi`
9. To generate the python grpc code from the proto file, run the following command (from the workspace root directory):
`python -m grpc_tools.protoc -Igrpc_config/out=./grpc_config \ --python_out=. --grpc_python_out=. \ --pyi_out=. \ ./grpc_config/metrics.proto` 
This sets the parent directory for the generated code to ./grpc_config/out.
--python_out, --grpc_python_out and pyi_out specify the relative path (w.r.t. the parent) for the generated code (based on the methods and types specified in the .proto file)

## Known Issues:

1. You may need to manually re-create specific components if certain associated resources were not configured properly when using the startup script. For example, if the producer component deployment and service was created but not the ingress; delete the producer component -> `kubectl delete -f deploy/producer/producer.yaml` and re-apply the manifest -> `kubectl apply -f deploy/producer/producer.yaml`