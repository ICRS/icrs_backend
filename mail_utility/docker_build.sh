docker buildx build --builder=builder --push --platform linux/arm64,linux/amd64 -t localhost:32000/mail_utility:${1:-latest} .
