#!/bin/bash

# apply the ingress-nginx controller manifest
echo "Applying ingress-nginx controller manifest..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.13.2/deploy/static/provider/cloud/deploy.yaml

# install metallb
echo "Installing MetalLB..."
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.15.2/config/manifests/metallb-native.yaml

# wait for metallb to be ready before applying the config
sleep 20

# apply the metallb configuration (defines the range of IPs that can be assigned to the load balancer)
echo "Applying MetalLB configuration..."
kubectl apply -f deploy/ingress_config/metallb-config.yaml