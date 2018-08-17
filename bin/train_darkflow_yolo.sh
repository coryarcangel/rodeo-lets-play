flow --train --model cfg/yolo.cfg --gpu 1.0 --dataset "/home/cory/pascal/VOC2012/JPEGImages" --annotation "/home/cory/pascal/VOC2012/Annotations/"

flow --train --model cfg/yolo.cfg --dataset "/home/cory/pascal/VOC2012/JPEGImages" --annotation "/home/cory/pascal/VOC2012/Annotations/" --gpu 0.5 --gpuName '/gpu:1' --batch 2 --epoch 100 --trainer sgd

flow --train --model cfg/tiny-yolo.cfg --dataset "/home/cory/pascal/VOC2012/JPEGImages" --annotation "/home/cory/pascal/VOC2012/Annotations/" --gpu 0.7 --gpuName '/gpu:1' --batch 10 --epoch 100 --trainer sgd


