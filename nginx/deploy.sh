kubectl create configmap nginx-conf -n ingress --from-file nginx-conf=nginx-prod.conf --dry-run=client -o yaml | kubectl apply -f -
