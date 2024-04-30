# Running

Example command:

```
docker run -v $YOUR_DIRECTORY_PATH:/app/squashfs-root/bin/tmp $YOUR_IMAGE_TAG --curr-bed-type "Textured PEI Plate" --avoid-extrusion-cali-region --allow-rotations --avoid-extrusion-cali-region --orient 1 --arrange 1 --load-settings "machine.json;process.json" --load-filaments "filament.json"  --ensure-on-bed --slice 0 --export-slicedata slice --export-3mf tmp/out.3mf tmp/test.stl
```
