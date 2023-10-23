import json
import re

def update_messages(content, role, messages, messages_file):
    new_message = {"role": role, "content": content}
    messages.append(new_message)
    with open(messages_file, 'w') as outfile:
        json.dump(messages, outfile)

    step = f"Step: {content}"
    print(step)
    
    with open('logs.txt', 'a') as f:
        f.write(step)

    return messages

def format_nbl(non_bash_languages):
    if len(non_bash_languages) == 1:
        nbl_str = non_bash_languages[0].title()

    if len(non_bash_languages) == 2:
        first_lang = non_bash_languages[0]
        sec_lang = non_bash_languages[1]

        nbl_str = f"{first_lang} and {sec_lang}"

    else:
        nbl_str = "".join(f"{nbl}, " for nbl in non_bash_languages[:-1])
        last_lang = non_bash_languages[-1]
        nbl_str += f"and {last_lang}"

    return nbl_str

def detect_non_bash_code(chatgpt_output):
    # Pattern to match code blocks
    pattern = r'```(\w+)\n(.*?)```'

    matches = re.findall(pattern, chatgpt_output, re.DOTALL)

    non_bash_languages = []

    for nb_match in matches:
        language = nb_match[0]

        # Check if the language is not bash
        if language.lower() != 'bash':
            non_bash_languages.append(language)

    return non_bash_languages

def conv_history_to_str(messages, full_context, user_name="user", assistant_name="assistant"):
    for message in messages[1:]:
        
        if message["role"] == "user":
            role = user_name
        elif message["role"] == "assistant":
            role = assistant_name
            
        content = message["content"]

        full_context += (f"{role}: {content}\n\n")
    
    return full_context