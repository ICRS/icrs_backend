# docker build -t localhost:32000/icrsbot-file-queue-manager .
# docker push localhost:32000/icrsbot-file-queue-manager
docker buildx build --builder=builder --push --platform linux/arm64,linux/amd64 -t localhost:32000/icrsbot-printer-queue-manager:$1 .
