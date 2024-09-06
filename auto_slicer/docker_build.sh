docker buildx build --builder=builder --push --platform linux/amd64 -t localhost:32000/auto-slicer:$1 .
