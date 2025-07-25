import csv
import json
import os
import pandas as pd
import re

csv_folder = './csv'
print(f'当前处理目录 {csv_folder}')

# 加载屏蔽词
blocked_words = json.load(open('./blocked_words.json', encoding='utf-8'))['blocked_words']
type_list = ['文本', '图片', '卡片式链接', '合并转发的聊天记录', '视频', '语音', '未知', '分享的小程序', '引用回复']


def handle_sft_csv(csvfile):
    chat_df = pd.read_csv(csvfile)
    chat_df = chat_df[chat_df['type_name'].isin(values=type_list)]
    chat_df['content'] = chat_df['msg']

    # 清洗文本内容
    for i in chat_df.index:
        content = chat_df.loc[i, 'content']
        if chat_df.loc[i, 'type_name'] == '引用回复':
            # 删除[引用]及其后面的所有内容
            content = re.sub(r'\[引用\].*', '', content)
            content = content.strip()
            chat_df.loc[i, 'content'] = content
        elif chat_df.loc[i, 'type_name'] == '文本':
            if ('1\d{10}' in content or '\d{18}' in content or '\w+@\w+' in content or 
                'http' in content or r'\\xa0' in content or r'\\u' in content):
                chat_df = chat_df.drop(index=i)
                continue
            for word in blocked_words:
                if word in content:
                    chat_df = chat_df.drop(index=i)
                    break
        else:
            if chat_df.loc[i, 'type_name'] not in ['图片', '卡片式链接', '视频', '语音', '分享的小程序']:
                chat_df.loc[i, 'content'] = ''

    chat_df = chat_df[['is_sender', 'type_name', 'content', 'CreateTime']]
    chat_df = chat_df.dropna()
    chat_df['CreateTime'] = pd.to_datetime(chat_df['CreateTime'])

    # 合并相同发送者连续消息
    res_df = []
    if len(chat_df) == 0:
        return pd.DataFrame()
        
    last_is_sender = chat_df.iloc[0]['is_sender']
    last_content = chat_df.iloc[0]['content']
    last_CreateTime = chat_df.iloc[0]['CreateTime']
    skip_list = ['图片', '卡片式链接', '合并转发的聊天记录', '视频', '语音', '未知', '分享的小程序']

    for i, row in chat_df.iterrows():
        # 直接忽略skip_list类型的消息
        if row['type_name'] in skip_list:
            continue

        # 只处理文本和引用回复
        if row['type_name'] in ['文本', '引用回复']:
            if last_content == '':
                last_content = row['content']
                last_is_sender = row['is_sender']
                last_CreateTime = row['CreateTime']
                continue

            if row['is_sender'] == last_is_sender:
                if row['CreateTime'] - last_CreateTime > pd.Timedelta('1h'):
                    res_df.append({'is_sender': last_is_sender, 'content': last_content, 'CreateTime': last_CreateTime})
                    last_content = row['content']
                    last_CreateTime = row['CreateTime']
                    continue
                if last_content and last_content[-1] not in ['。', '！', '？', '…', '，']:
                    last_content += '，'
                last_content += row['content']
                last_CreateTime = row['CreateTime']
            else:
                res_df.append({'is_sender': last_is_sender, 'content': last_content, 'CreateTime': last_CreateTime})
                last_is_sender = row['is_sender']
                last_content = row['content']
                last_CreateTime = row['CreateTime']

    if last_content:
        res_df.append({'is_sender': last_is_sender, 'content': last_content, 'CreateTime': last_CreateTime})

    return pd.DataFrame(res_df)


def split_long_dialog(dialog, max_rounds=5):
    """对超过指定轮数的对话进行对半拆分"""
    max_messages = max_rounds * 2
    if len(dialog) <= max_messages:
        return [dialog]
    
    mid_point = len(dialog) // 2
    if mid_point % 2 != 0:
        mid_point -= 1
        if mid_point <= 0:
            mid_point = 2
    
    first_half = dialog[:mid_point]
    second_half = dialog[mid_point:]
    
    result = []
    result.extend(split_long_dialog(first_half, max_rounds))
    result.extend(split_long_dialog(second_half, max_rounds))
    return result


def ensure_human_start(dialog):
    """确保对话以human开头"""
    if not dialog:
        return []
    start_idx = 0
    while start_idx < len(dialog) and dialog[start_idx]['from'] != 'human':
        start_idx += 1
    return dialog[start_idx:] if start_idx < len(dialog) else []


def merge_consecutive_messages(dialog):
    """合并连续相同发送者的消息"""
    if not dialog:
        return []
    
    dialog = ensure_human_start(dialog)
    merged_dialog = []
    current_sender = None
    current_content = ""
    
    for i in range(len(dialog)):
        msg = dialog[i]
        
        if current_sender is None:
            current_sender = msg['from']
            current_content = msg['value']
        elif msg['from'] == current_sender:
            if current_content and current_content[-1] not in ['。', '！', '？', '…', '，']:
                current_content += '，'
            current_content += msg['value']
        else:
            merged_dialog.append({'from': current_sender, 'value': current_content})
            current_sender = msg['from']
            current_content = msg['value']
    
    if current_content and current_sender:
        merged_dialog.append({'from': current_sender, 'value': current_content})
    
    if len(merged_dialog) % 2 != 0 and len(merged_dialog) > 0:
        merged_dialog = merged_dialog[:-1]
    
    return ensure_human_start(merged_dialog)


def make_sharegpt_dataset():
    # 处理所有CSV文件
    csv_concat = []
    for chat_obj_folder in os.listdir(csv_folder):
        chat_obj_folder_path = os.path.join(csv_folder, chat_obj_folder)
        if not os.path.isdir(chat_obj_folder_path):
            continue
        for csvfile in os.listdir(chat_obj_folder_path):
            if not csvfile.endswith('.csv'):
                continue
            csvfile_path = os.path.join(chat_obj_folder_path, csvfile)
            try:
                df = handle_sft_csv(csvfile_path)
                if not df.empty:
                    csv_concat.append(df)
            except Exception as e:
                print(f"处理文件 {csvfile_path} 出错：{e}")

    if not csv_concat:
        print("没有可处理的聊天记录")
        return

    csv_concat = pd.concat(csv_concat, ignore_index=True)

    # 构建对话序列 - 只在时间间隔过长时分隔对话
    all_dialogs = []
    current_dialog = []
    last_time = None

    for _, row in csv_concat.iterrows():
        sender = 'gpt' if row['is_sender'] == 1 else 'human'
        content = row['content']

        # 只在时间间隔过长时分隔对话
        if last_time and row['CreateTime'] - last_time > pd.Timedelta('4h'):
            if current_dialog:
                all_dialogs.append(current_dialog)
                current_dialog = []

        current_dialog.append({'from': sender, 'value': content})
        last_time = row['CreateTime']

    if current_dialog:
        all_dialogs.append(current_dialog)

    # 处理对话格式和拆分
    final_conversations = []
    system_prompt = "请你扮演一个名叫\"……\"的人类进行对话，不要说自己是人工智能或大模型。"
    
    for dialog in all_dialogs:
        dialog = merge_consecutive_messages(dialog)
        
        if not dialog or len(dialog) < 2:
            continue
            
        split_dialogs = split_long_dialog(dialog, max_rounds=4)
        for split_dialog in split_dialogs:
            cleaned_split = merge_consecutive_messages(split_dialog)
            if len(cleaned_split) >= 2 and cleaned_split[0]['from'] == 'human':
                final_conversations.append({
                    'conversations': cleaned_split,
                    'system': system_prompt
                })

    # 保存结果
    output_path = '../LLaMA-Factory/data/chat_sharegpt.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_conversations, f, ensure_ascii=False, indent=2)

    print(f"✅ 已保存 ShareGPT 格式数据集到：{output_path}，共 {len(final_conversations)} 条对话")


if __name__ == '__main__':
    make_sharegpt_dataset()