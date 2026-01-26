# webtest_model

## RLHF 第一次训练

### 参数

补依赖

deepspeed需要使用的依赖

```
pip install deepspeed

sudo apt install -y openmpi-bin openmpi-common libopenmpi-dev

pip install mpi4py
```



```
CUDA_VISIBLE_DEVICES=0 \
swift rlhf \
    --model Qwen/Qwen3-8B \
    --rlhf_type kto \
    --train_type lora \
    --dataset '/home/ubuntu/webtest_rlhf_project/train_data/first_train.jsonl' \
	--val_dataset '/home/ubuntu/webtest_rlhf_project/train_data/first_dev.jsonl' \
    --torch_dtype float16 \
    --deepspeed zero2 \
    --num_train_epochs 3 \
    --per_device_train_batch_size 1 \
    --per_device_eval_batch_size 1 \
    --learning_rate 1e-4 \
    --lora_rank 8 \
    --lora_alpha 32 \
    --target_modules all-linear \
    --gradient_accumulation_steps 16 \
    --eval_steps 30 \
    --save_steps 30 \
    --save_total_limit 2 \
    --logging_steps 5 \
    --max_length 8000 \
    --output_dir webtest_first_train_output \
    --warmup_ratio 0.05 \
    --dataloader_num_workers 4 \
    --model_author swift \
    --model_name swift-robot
```



```
CUDA_VISIBLE_DEVICES=0 \
swift infer \
    --adapters webtest_first_train_output/v0-20250828-112759/checkpoint-30 \
    --stream false \
    --merge_lora true \
    --infer_backend vllm \
    --vllm_max_model_len 8192 \
    --temperature 0.1 \
    --max_new_tokens 4000
```



```
sudo apt update && sudo apt install -y git-lfs
```



推送到 ModelScope

```
CUDA_VISIBLE_DEVICES=0 \
swift export \
    --adapters webtest_first_train_output/v0-20250828-112759/checkpoint-30 \
    --push_to_hub true \
    --hub_model_id 'heypon/webtest' \
    --hub_token 'ms-288c2b2d-b00f-432c-8a20-d75b0a14f923' \
    --use_hf false
```



部署为本地 API 服务

```
CUDA_VISIBLE_DEVICES=0 \
swift deploy \
    --model Qwen/Qwen3-8B \
    --adapters heypon/webtest \
    --max_new_tokens 2048 \
    --served_model_name webtest-lora \
    --merge_lora true \
    --port 8888 \
    --host 0.0.0.0 
```



远程调用，使用 openai 方式调用

pip install openai





### 需求关联

向量、向量库



距离相似度、余弦相似度



提取关联需求的方法（Ai、向量）



需求提炼框架



需求提炼框架代码解读



如何结合需求提炼框架及训练的模型





