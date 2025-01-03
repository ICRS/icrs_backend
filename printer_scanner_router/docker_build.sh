docker buildx build --builder=builder --push --platform linux/arm64,linux/amd64 -t localhost:32000/printer_scanner_router:${1:-latest} .
