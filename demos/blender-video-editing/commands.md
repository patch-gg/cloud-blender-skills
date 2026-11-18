# blender-video-editing: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
python <skills_dir>/blender-cloud/scripts/cloud.py push clips
python <skills_dir>/blender-cloud/scripts/cloud.py --timeout 1800 run '<skills_dir>/blender-video-editing/scripts/vse_edit.py' -- --clips cuts/blender-workflow-recipes/ cuts/blender-core/ cuts/blender-cloud/ cuts/blender-scene-setup/ cuts/blender-asset-qa/ cuts/blender-hardsurface-modeling/ cuts/blender-sculpting/ cuts/blender-retopology-uv/ cuts/blender-geometry-nodes/ cuts/blender-pbr-materials/ cuts/blender-texturing/ cuts/blender-texture-baking/ cuts/blender-stylized-npr/ cuts/blender-character-rigging/ cuts/blender-facial-shapekeys/ cuts/blender-animation/ cuts/blender-clothing/ cuts/blender-hair-grooming/ cuts/blender-environment-kits/ cuts/blender-time-of-day/ cuts/blender-weather-fx/ cuts/blender-simulation/ cuts/blender-lighting-lookdev/ cuts/blender-game-optimization/ cuts/blender-export-pipelines/ cuts/blender-rendering/ cuts/blender-pipeline-automation/ cuts/blender-addon-development/ --fps 24 --resolution 1280 720 --crossfade 4 --title 'cloud blender skills' --title-seconds 1.6 --out //reel.mp4 --render --save reel.blend
```
