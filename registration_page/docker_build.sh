# docker build -t icrs-registration-page .
# docker push localhost:32000/icrs-registration-page
docker buildx build --builder=builder --push --platform linux/arm64,linux/amd64 -t localhost:32000/icrs-registration-page .

