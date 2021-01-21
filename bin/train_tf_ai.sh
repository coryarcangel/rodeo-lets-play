#!/usr/bin/env bash

eval "$(conda shell.bash hook)"
conda activate tf-ai-env
python src/tf_ai_trainer.py
