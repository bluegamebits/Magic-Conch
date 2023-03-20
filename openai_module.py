import openai
import random
import asyncio
import json

import translations

_ = translations.setup_i18n('es')


async def ask_gpt(query):

    # Open the JSON file and read the api
    with open('openai_api.json') as f:
        data = json.load(f)
    openai.api_key = data['api']

    backup_answers = _(["Everything is possible if you desire it strongly enough.", "Yes, but not without consequences.", "The signs point towards success.",
                            "Don't count on it.",    "It's better that you discover it for yourself.",    "My sources say no.",
                                    "It's possible, but not certain.",    "Yes, but not in the way you expect.",    "The answer is right in front of you.",
                                            "I'm not sure that's a good idea.",    "You need to think more before making a decision.",    "Definitely yes!",
                                                    "Not until you find what you're looking for.",    "You should wait and see what happens.", 
                                                          "I can't answer that now.",    "It's not my place to say.",
                                                                  "If you take the right path, you will achieve it.",
                                                                          "You should focus on other matters right now.",    "The answer is in your dreams."])

    
    ask_again = _(["I cannot answer at this time, ask me later."])
    current_model = "gpt-3.5-turbo"

    try:
        print(f"Received chatGPT-3 prompt: {query}")
        completion = await asyncio.wait_for(openai.ChatCompletion.acreate(model=current_model, messages=[
        {"role": "system", "content": _("You are the magic conch. You are not chatgpt.")},
        {"role": "user", "content": _("You will always respond with short, cryptic, and vague answers. All your responses will always be in a single sentence. Tell me, ") + query},


        ],), timeout=10,)
    
        
    except asyncio.TimeoutError:
        print(f"Timeout error.")
        return random.choice(ask_again)
    except Exception as e:
        print(f"Error on openai api: {e}")
        return random.choice(backup_answers)
    
    answer = completion.choices[0].message.content
    print(f"Returned response: {answer}")

    return answer
