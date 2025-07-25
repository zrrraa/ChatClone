#!/bin/bash

# 获取当前系统时间戳，格式为 YYYY-MM-DD-HH-MM-SS
timestamp=$(date +"%Y-%m-%d-%H-%M-%S")

# 定义输出目录的基础路径
output_base_dir="LLaMA-Factory/saves/Qwen2.5-7B-Instruct-AWQ/lora/train"

# 拼接时间戳到输出目录
output_dir="${output_base_dir}_${timestamp}"

# 执行训练命令
llamafactory-cli train \
    --stage sft \
    --do_train True \
    --model_name_or_path /home/zrrraa/Project/model/Qwen2.5-7B-Instruct-AWQ \
    --preprocessing_num_workers 16 \
    --finetuning_type lora \
    --template qwen \
    --flash_attn auto \
    --dataset_dir LLaMA-Factory/data \
    --dataset wechat \
    --cutoff_len 512 \
    --learning_rate 5e-05 \
    --num_train_epochs 3.0 \
    --max_samples 100000 \
    --per_device_train_batch_size 2 \
    --gradient_accumulation_steps 4 \
    --lr_scheduler_type cosine \
    --max_grad_norm 1.0 \
    --logging_steps 5 \
    --save_steps 500 \
    --warmup_steps 300 \
    --packing False \
    --enable_thinking False \
    --report_to none \
    --output_dir "${output_dir}" \
    --bf16 True \
    --plot_loss True \
    --trust_remote_code True \
    --ddp_timeout 180000000 \
    --include_num_input_tokens_seen True \
    --optim adamw_torch \
    --quantization_bit 4 \
    --quantization_method bnb \
    --double_quantization True \
    --lora_rank 8 \
    --lora_alpha 16 \
    --lora_dropout 0 \
    --lora_target all