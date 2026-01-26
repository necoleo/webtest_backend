import json
import time
import requests
import os

API_URL = "http://159.75.166.52:3389/v1/chat/completions"

def call_ai_model(messages):
    payload = {
        "model": "api-generate-func-case",
        "messages": messages,
        "temperature": 0.1
    }
    
    try:
        start_time = time.time()
        response = requests.post(API_URL, json=payload, timeout=30)
        print(f"API调用耗时：{time.time() - start_time:.2f}秒")
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"API错误: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"API调用异常: {str(e)}")
        return None

def process_data():
    # 确保输出文件存在
    if not os.path.exists('fail.jsonl'):
        open('fail.jsonl', 'w').close()
    
    with open('new_train.jsonl', 'r', encoding='utf-8') as infile, \
         open('fail.jsonl', 'a', encoding='utf-8') as outfile:
        
        for line in infile:
            try:
                data = json.loads(line.strip())
                messages = data["messages"]
                
                # 提取前四个角色消息
                input_messages = messages[:4]
                # 获取预期回复内容
                expected_content = messages[4]["content"] if len(messages) > 4 else ""
                expected_length = len(expected_content)
                
                # 调用AI模型
                ai_response = call_ai_model(input_messages)
                
                if ai_response is None:
                    print("API调用失败，跳过当前条目")
                    continue
                
                # 检查生成长度是否超过预期20%
                ai_length = len(ai_response)
                if expected_length > 0 and ai_length > expected_length * 1.2:
                    print(f"AI生成内容: {ai_response}")
                    print(f"预期内容: {expected_content}")
                    print(f"生成长度过长: AI生成{ai_length}字符 > 预期{expected_length}字符的120%\n")
                    
                    # 修改数据
                    if len(messages) > 4:
                        messages[4]["content"] = ai_response
                    else:
                        messages.append({
                            "role": "assistant",
                            "content": ai_response
                        })
                    
                    data["messages"] = messages
                    data["label"] = False
                    
                    # 写入失败文件
                    outfile.write(json.dumps(data, ensure_ascii=False) + '\n')
                    print("已写入fail.jsonl")
                else:
                    print(f"生成长度正常: AI生成{ai_length}字符 <= 预期{expected_length}字符的120%")
                    
            except json.JSONDecodeError:
                print("JSON解析错误，跳过无效行")
            except KeyError as e:
                print(f"数据结构错误: {str(e)}")
            except Exception as e:
                print(f"处理异常: {str(e)}")

if __name__ == "__main__":
    process_data()
    print("处理完成！")