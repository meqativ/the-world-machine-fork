import json
import re
from interactions import Message, User
from utilities.shop.fetch_shop_data import reset_shop_data
from config_loader import load_config
import database
import ast
from aioconsole import aexec
import traceback

async def get_collection(collection: str, _id: str):
    key_to_collection: dict[str, database.Collection] = {
        'user': database.UserData(_id),
        'nikogotchi': database.Nikogotchi(_id),
        'nikogotchi_old': database.NikogotchiData(_id),
        'server': database.ServerData(_id)
    }
    
    return key_to_collection[collection]

import sys
import io
from contextlib import redirect_stdout
from asyncio import iscoroutinefunction
async def redir_prints(method, code):
    output_capture = io.StringIO()
    
    with redirect_stdout(output_capture):
        if iscoroutinefunction(method):
            await method(code)
        else: 
            method(code)
        
    return output_capture.getvalue()

async def execute_dev_command(message: Message):
    
    if message.author.bot:
        return
    
    if not str(message.author.id) in load_config('dev-command-user-list'):
        return
    
    if not message.content:
        return
    
    # This is not a valid command if brackets do not surround the message.
    if not (message.content[0] == '{' or message.content[-1] == '}'):
        return
    
    # Remove the brackets
    command_content = message.content[1:-1].strip()
    
    # Split the command into parts
    args = command_content.split(" ")
    
    name = args[0]
    
    match name:
        case "eval":
            method = args[1]
            async def remove_codebloque(content: str, graceful = False):
                await message.reply("received: \`\`\`py\n"+content+"\`\`\`")
                if content.startswith("```py\n") and content.endswith("```"):
                    return content[5:-3].strip()
                else:
                    if graceful:
                        return content
                    raise ValueError("Codeblock required")

            result = None
            try:
                match method:
                    case "exec":
                        result = await redir_prints(exec, await remove_codebloque(command_content.split("eval exec ")[1]))
                    case "aexec":
                        result = await redir_prints(aexec, await remove_codebloque(command_content.split("eval aexec ")[1]))
                    case _: 
                        result = eval(await remove_codebloque(command_content.split("eval ")[1], True))
            except ValueError as e:
                if (str(e) == "Codeblock required"):
                    result = f"Codeblock required. e.g. \\`\\`\\`py\\n{{code}}\\`\\`\\`"
            except Exception as e:
                result = f"Exception raised: {str(e)}"
            
            await message.reply(result)
        case "shop":
        
            action = args[1]
            
            items = await database.fetch_items()
            shop = items['shop']
            
            if action == 'view':
                result = '```\n'
                    
                for key in shop.keys():
                    result += f'{key}: {str(shop[key])}\n'
                    
                result += '```'
                
                await message.reply(result)
            
            if action == 'reset':
                await reset_shop_data('en-US')
                
                await message.reply(
                    f'`[ Successfully reset shop. ]`'
                )
        case "db":
            try:
                action = args[1]
                
                if action == 'set':
                    
                    pattern = r'\{(?:[^{}]*|\{[^{}]*\})*\}'
                    
                    matches = re.findall(pattern, command_content)
                    
                    collection = args[2]
                    _id = args[3]
                    str_data = matches[0]

                    data = json.loads(str_data)

                    collection = await database.fetch_from_database(await get_collection(collection, _id))
                    
                    await collection.update(**data)
                    
                    await message.reply(
                        f'`[ Successfully updated value(s). ]`'
                    )
                    
                if action == 'view':
                    collection = args[2]
                    _id = args[3]
                    value = args[4]
                    
                    if collection == 'shop':
                        collection = await get_collection(collection, 0)
                    else:
                        collection = await database.fetch_from_database(await get_collection(collection, _id))
                    
                    await message.reply(
                        f'`[ The value of {value} is {str(collection.__dict__[value])}. ]`'
                    )
                    
                if action == 'view_all':
                    collection = args[2]
                    _id = args[3]
                    
                    collection = await database.fetch_from_database(await get_collection(collection, _id))
                    
                    data = collection.__dict__
                    
                    result = '```\n'
                    
                    for key in data.keys():
                        result += f'{key}: {str(data[key])}\n'
                        
                    result += '```'
                    
                    await message.reply(result)
                    
                    
                if action == 'wool':
                    _id = args[2]
                    amount = int(args[3])
                    
                    collection: database.UserData = await database.fetch_from_database(await get_collection('user', _id))
                    
                    await collection.manage_wool(amount)
                    
                    await message.reply(
                        f'`[ Successfully modified wool, updated value is now {collection.wool}. ]`'
                    )
                    
            except Exception as e:
                await message.reply(
                    f'`[ Error with command. ({e}) ]`'
                )
        case _:
            await message.reply("else condition triggered")
    print(f"Logs - eval - - - - - - - - - - -\n{message.author.mention} ({message.author.username}) ran:\n{command_content}")

