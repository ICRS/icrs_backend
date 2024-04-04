# ICRS LAB SECURITY

This project contains the necessary infrastructure for interfacing with the numerous systems in the lab. [Note: this does not contain the ICRS-Slicer Project]

## Projects:

* Server: contains all the necessary components for the lab
* Bambu Printer Gateway: a translation layer from bambu p1 printers to REST service
* Registration Page: React project for registering new users

## Build Instructions

BUILDX Create Builder:
docker buildx create --config ~/.docker/buildx/config.toml --name builder --driver-opt network=host

The config.toml file should look like this:
```
[registry."REGISTRY_IP:REGISTRY_PORT"]
http = true
insecure = true
```

Run the build_docker.sh script file in each respective folder

## Deployment instructions:

Deploy each project to k8s respectively with:
```
kubectl apply -f deployment.yaml 
```
