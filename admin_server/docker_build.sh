docker buildx build --builder=builder --push --platform linux/arm64,linux/amd64 -t localhost:32000/icrs-access:${1:-latest} .
