#!/bin/bash

PRINTERS=("andrew-printerson" "eric-printman" "printer-cheung" "freddy-printer" "printy-mcprintface" "additive-spiers")

for printer in ${PRINTERS[@]}; do
    echo "Deploying printer $printer"
    cat deployment.yaml | sed -e "s/\${printer-name}/$printer/g" | sed -e "s/latest/${1:-latest}/g" | kubectl apply -f -
    # Deploy printer
done
