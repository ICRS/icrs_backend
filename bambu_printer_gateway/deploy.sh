#!/bin/bash

PRINTERS=("andrew-printerson" "")

for printer in ${PRINTERS[@]}; do
    echo "Deploying printer $printer"
    cat deployment.yaml | sed -e "s/\${printer-name}/$printer/g" | kubectl apply -f -
    # Deploy printer
done
