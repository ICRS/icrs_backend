# docker build -t icrs-registration-page .
# docker push localhost:32000/icrs-registration-page
docker buildx build --builder=builder --build-arg ENV=${2:-dev} --push --platform linux/arm64,linux/amd64 -t localhost:32000/icrs-registration-page:${1:-latest} .

