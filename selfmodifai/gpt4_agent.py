import os
import re
import json
from transformers import pipeline
import openai
from openai.error import InvalidRequestError
from selfmodifai.handle_too_long_context import handle_too_long_context
from selfmodifai.helpers import update_messages, format_nbl, detect_non_bash_code, conv_history_to_str

def gpt4_agent():
    openai.api_key = os.environ.get("OPENAI_API_KEY")

    messages_path = "/selfmodifai/selfmodifai/prompts/messages.json"

    with open(messages_path) as json_file:
        messages = json.load(json_file)

    bash_response = "Create bash commands that do that. Give me them one by one."
    while True:

        try:
            response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
            )
        except InvalidRequestError as e:
            if "maximum context length" not in str(e):
                # Re-raise the exception if it's not what we're looking for
                raise e

            response, messages = handle_too_long_context(messages)

            with open(messages_path, 'w') as outfile:
                json.dump(messages, outfile)

        response_content = response["choices"][0]["message"]["content"]

        messages = update_messages(response_content, "assistant", messages, messages_path)

        bash_matches = re.findall(r'```bash\n(.*?)\n```', response_content, re.DOTALL)

        non_bash_languages = detect_non_bash_code(response_content)

        if bash_matches:
            content = ""
        # matches is now a list of all bash commands in the string
            for bash_command in bash_matches:

                if bash_command.startswith('cd '):
                    os.chdir(bash_command[3:])
                    continue

                content += f"{bash_command}:\n"
                stream = os.popen(bash_command)

                content += stream.read()


            if len(content) > 3900:
                content = "That file is too long to send to you. I only want to send you 25 lines of code at a time. Write bash commands to extract the contents from it in smaller chunks."

            elif non_bash_languages:
                nbl_str = format_nbl(non_bash_languages)

                content += f"Those are the outputs from those bash commands. Can you write bash commands to implement the {nbl_str} code?"

            elif not content:
                content = "Ok, did that"

        elif non_bash_languages:
            languages = format_nbl(non_bash_languages)
            content = f"Write bash commands to implement those changes in the {languages} files."

        elif "?" not in response_content:
            content = bash_response

        else:
            classifier = pipeline("zero-shot-classification")
            labels = ["suggestion for what to do next", "inquisitive question", "asking somebody to do something"]
            results = classifier(sequences=response_content, candidate_labels=labels, hypothesis_template="This text is a {}")

            if results["labels"][0] == "suggestion for what to do next":
                full_context = "This is a conversation between you and an language model-powered AI agent:\n"
                full_context = conv_history_to_str(messages, full_context, user_name="you", assistant_name="AI agent")
                full_context = f"{full_context}\n\n Write a message to the agent directing them to do what they are trying to help us do. They will accomplish their task by writing bash commands that our computer will execute."

                mananager_agent_messages = [{"role": "system", "content": "You are trying to help an AI agent improve the language model Alpaca-LoRA."}, {"role": "user", "content": full_context}]

                manager_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=mananager_agent_messages
                )

                content = manager_response["choices"][0]["message"]["content"]


            else:
                content = "My goal is to improve the model architecture of Alpaca-LoRA to make it a more powerful language model, without just making the model larger. Find the answer to that question in that context. If you can't, try another step in improving the language model."


        messages = update_messages(content, "user", messages, messages_path)