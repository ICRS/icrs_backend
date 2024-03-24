PRINTERS=["andrew-printerson",""]

for printer in ${PRINTERS[@]}; do
    echo "Deploying printer $printer"
    cat deployment.yaml | sed "s/${printer-name}/$printer/g" | kubectl apply -f -
    # Deploy printer
done
