#!/bin/bash

# rollback metallb
echo "Rolling back MetalLB..."
kubectl delete -f https://raw.githubusercontent.com/metallb/metallb/v0.15.2/config/manifests/metallb-native.yaml

# rollback the metallb configuration
echo "Rolling back MetalLB configuration..."
kubectl delete -f deploy/ingress_config/metallb-config.yaml

# rollback the ingress-nginx controller configuration
echo "Rolling back ingress-nginx controller configuration..."
kubectl delete -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.13.2/deploy/static/provider/cloud/deploy.yaml
