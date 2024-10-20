#docker build -t localhost:32000/icrs-access .
#docker push localhost:32000/icrs-access
docker buildx build --builder=builder --push --platform linux/arm64,linux/amd64 -t localhost:32000/icrs-bambu-printer-gateway:${1:-latest} .
