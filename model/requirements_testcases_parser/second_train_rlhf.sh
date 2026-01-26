#!/bin/bash

# RLHF 训练脚本 - KTO 方法
# 从 checkpoint-9 继续训练

# 设置环境变量
export CUDA_VISIBLE_DEVICES=0

# 使用nohup在后台运行训练命令，输出日志到second_train_rlhf.log
nohup swift rlhf \
    --rlhf_type kto \
    --model Qwen/Qwen-7B-Chat \
    --resume_from_checkpoint '/home/ubuntu/webtest_rlhf_project/first_rlhf_model_output/v0-20251010-124038/checkpoint-9' \
    --train_type lora \
    --dataset '/home/ubuntu/webtest_rlhf_project/train_data/second_train_data/second_train_data.jsonl' \
    --val_dataset '/home/ubuntu/webtest_rlhf_project/train_data/second_train_data/second_dev_data.jsonl' \
    --num_train_epochs 3 \
    --per_device_train_batch_size 1 \
    --per_device_eval_batch_size 1 \
    --learning_rate 3e-5 \
    --lora_rank 8 \
    --lora_alpha 32 \
    --target_modules all-linear \
    --gradient_accumulation_steps 16 \
    --eval_steps 3 \
    --save_steps 3 \
    --save_total_limit 5 \
    --logging_steps 2 \
    --max_length 4096 \
    --output_dir second_rlhf_model_output \
    --warmup_ratio 0.05 \
    --dataloader_num_workers 4 \
    --deepspeed zero3 \
    --offload_optimizer true \
    --offload_model true \
    --gradient_checkpointing true > second_train_rlhf.log 2>&1 &

# 显示后台任务ID
echo "训练任务已在后台启动，进程ID: $!"
echo "日志文件: second_train_rlhf.log"
echo "查看日志: tail -f second_train_rlhf.log"

