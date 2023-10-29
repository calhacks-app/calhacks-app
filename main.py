import discord
from discord.app_commands import CommandTree
import random
import together
import time
import io
import os
import asyncio
import functools
import PIL
from PIL import Image
import glob
from dotenv import load_dotenv

load_dotenv(".env")

together.api_key = os.getenv("TOGETHER_AI_API_KEY")
bot_token = os.getenv("BOT_TOKEN")

# User ID
#   - task_complete | Today's Task Completion [bool]
#   - resets | Daily Resets [int]
#   - today_task | Today's Task [Str]
#   - today_task_reasoning | Today's Task Reasoning [Str]
#   - puzzle | Puzzle Status [list]
#   - past_days | Past Day Goals [dict]
#   - goal | Goal [Str]
data = {}

allowed_mentions = discord.AllowedMentions(everyone=False, users=True, roles=True, replied_user=False)
intents = discord.Intents.all()
intents.presences = False
intents.members = False

puzzle_list = {}

async def setup_hook():
    for filename in glob.glob('./puzzle/*.png'):
        im=Image.open(filename)
        name_proc = filename.split("/")[-1].replace(".png", "").split("_")
        puzzle_list[(int(name_proc[0]), int(name_proc[1]))] = im


client = discord.AutoShardedClient(intents=intents, allowed_mentions=allowed_mentions, chunk_guilds_at_startup=False)
# client.activity = discord.Activity(
#         name='Activity', 
#         type=discord.ActivityType.watching,)

client.setup_hook = setup_hook
client.tree = CommandTree(client)

@client.event
async def on_ready():
    print("Bot started")

@client.event
async def on_message(message):
    global data

    if message.author.bot:
        return
    
    if message.author.id == 396545298069061642 and message.content.lower() == "!reloadcmd":
        await client.tree.sync(guild=None)
        await message.reply("Reloaded global")

    if message.content.lower() == "!reset":
        data = {}
        await message.delete()

    if message.author.id == 396545298069061642 and message.content.lower() == "!openlifepuzzlebutton":
        embed=discord.Embed(title="Open LifePuzzle", description="Click the button below to open LifePuzzle.", color=0xfc766a)
        embed.set_author(name="LifePuzzle")
        buttons = discord.ui.View()
        buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.green, label="Open LifePuzzle", row=1, custom_id="display_task_button", disabled=False))
        await message.channel.send(embed=embed, view=buttons)

    if message.content.lower() == "!demodata":
        data[message.author.id] = {
            "task_complete": False,
            "resets": 1,
            "today_task": None,
            "today_task_reasoning": None,
            "puzzle": [True] * 27,
            "past_days": {},
            "goal": "eat healthier, talk to people more, be more fit"
        }
        await message.delete()

    if message.content.lower() == "!demooops":
        data[message.author.id] = {
            "task_complete": True,
            "resets": 1,
            "today_task": "Take your dog out for a walk after lunch.",
            "today_task_reasoning": "Taking your dog out after lunch will give you the opportunity to spend quality time with your dog, therefore achieving your goal of spending more time with your dog.",
            "puzzle": [True] * 16 + [False] + [True] * 11,
            "past_days": {},
            "goal": "spend more time with my dog"
        }
        await message.delete()

    if message.content.lower() == "!demohalf":
        data[message.author.id] = {
            "task_complete": True,
            "resets": 1,
            "today_task": None,
            "today_task_reasoning": None,
            "puzzle": [True] * 16,
            "past_days": {},
            "goal": "spend more time with my dog"
        }
        await message.delete()

    return

async def together_prompt(prompt):
    return await client.loop.run_in_executor(None, functools.partial(
        together.Complete.create,
        prompt = prompt, 
        model = "togethercomputer/llama-2-7b-chat", 
        max_tokens = 256,
        temperature = 0.8,
        top_k = 60,
        top_p = 0.6,
        repetition_penalty = 1.1,
        stop = ['<human>', '\n\n']
        ))

async def generate_puzzle(completion):
    canvas = Image.new('RGBA', (1890, 1080), (0,0,0,0))
    for y in range(4):
        for x in range(7):
            id = 7 * y + x
            if len(completion) < id + 1 or completion[id] == False:
                continue
            else:
                im = puzzle_list[(x, y)]
                canvas.paste(im, (x * 270, y * 270))
    
    return canvas


async def set_goal(interaction):
    user_id = interaction.user.id
    embed=discord.Embed(title="Set Goal", description=("Your current goal: " + data[user_id]["goal"] + "\n\nIf you want to change your goal, please enter it in chat!" if data[user_id]["goal"] != None else "Set a couple goals that you want to achieve. It's recommended that you set multiple goals.") + "\n\nSome great examples:\n- Eat healthier\n- Exercise more\n- Be more thankful", color=0xfc766a)
    embed.set_author(name="LifePuzzle")
    buttons = discord.ui.View()
    buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.grey, label="Waiting for Chat Input", row=1, custom_id="chatinputindicator", disabled=True))
    if data[user_id]["goal"] != None:
        buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.red, label="Cancel", row=1, custom_id="cancel", disabled=False))
    msg = await interaction.followup.send(embed=embed, view=buttons)

    def check_msg(m):
        return m.channel.id == interaction.channel.id and m.author.id == user_id
    def check_interaction(m):
        return m.type not in [discord.InteractionType.application_command, discord.InteractionType.autocomplete] and m.user.id == user_id and m.message.id == msg.id
    done, pending = await asyncio.wait([
                asyncio.create_task(client.wait_for('message', timeout=120.0, check=check_msg)),
                asyncio.create_task(client.wait_for('interaction', timeout=121.0, check=check_interaction))
            ], return_when=asyncio.FIRST_COMPLETED)
    try:
        result = done.pop().result()
    except asyncio.TimeoutError:
        for future in done:
            future.exception()
        for future in pending:
            future.cancel()
        return msg
    
    for future in done:
        future.exception()
    for future in pending:
        future.cancel()

    if type(result) == discord.Interaction:
        await result.response.defer()
        return msg
    
    asyncio.create_task(result.delete())
    
    goal = result.content.strip().replace('"', "").replace("\n", ", ").replace("   ", " ").replace("  ", " ")

    prompt = """
    The user has stated that they want their goal to be: "[GOAL PLACEHOLDER]"
    """.replace("[GOAL PLACEHOLDER]", goal)

    prompt += """
    Is this a good long-term goal? Is this goal realistic, achievable, positive and clear?

    RESPONSE FORMAT, STRICTLY FOLLOW THIS FORMAT WITH THE RESULT AND REASONING HEADERS:
    Result: ["True" if the goal meets the criteria, or "False" if it doesn't.]
    Reasoning: [Message sent to the user explaining why the goal meets/doesn't meet the criteria, be personal and considerate when talking to the user. Format the message in a concise and easy to read manner, and use "{nl}" to start a new line whenever appropriate.]

    RESPONSE IN ABOVE FORMAT ONLY:
    """

    asyncio.create_task(msg.delete())
    embed=discord.Embed(title="Goal Loading...", description="Please wait.", color=0xfc766a)
    embed.set_author(name="LifePuzzle")
    msg = await result.reply(embed=embed)

    output = await together_prompt(prompt)
    result = output['output']['choices'][0]['text'].split("Result: ")[1]
    reasoning = result.split("Reasoning: ")[1].strip().replace("{nl}", "\n\n")
    result = result.split("Reasoning: ")[0].upper().replace("TRUE", "T").replace("Y", "T").replace("YES", "T").strip()

    if result != "T":
        embed=discord.Embed(title="Issue with Your Goal", description=reasoning, color=0xfc766a)
        embed.set_author(name="LifePuzzle")

        buttons = discord.ui.View()
        buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.green, label="Enter a New Goal", custom_id="newgoal", disabled=False))
        buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.red, label="Continue", custom_id="continue", disabled=False))
        await msg.edit(embed=embed, view=buttons)

        def check(m):
            return m.type not in [discord.InteractionType.application_command, discord.InteractionType.autocomplete] and m.channel.id == interaction.channel.id and m.message.id == msg.id
        try:
            interactionResponse = await client.wait_for('interaction', timeout=60, check=check)
        except asyncio.TimeoutError:
            await msg.edit(view=None)
            return
        
        if interactionResponse.data['custom_id'] == "newgoal":
            asyncio.create_task(msg.delete())
            await set_goal(interaction)
            return
        
    data[user_id]["goal"] = goal
    asyncio.create_task(msg.delete())

async def show_task(interaction: discord.Interaction):
    msg = None
    await interaction.response.defer()

    user_id = interaction.user.id
    if user_id not in data:
        data[user_id] = {
            "task_complete": False,
            "puzzle": [],
            "resets": 1,
            "past_days": {},
            "goal": None,
            "today_task": None,
            "today_task_reasoning": None
        }

    if data[user_id]["goal"] == None:
        msg = await set_goal(interaction)

        if data[user_id]["goal"] == None:
            return
    
    
    if data[user_id]["today_task"] == None:
        embed=discord.Embed(title="Today's Task", description="Your task of the day is being prepared...", color=0xfc766a)
        embed.set_author(name="LifePuzzle")
        msg = await interaction.followup.send(embed=embed)

        prompt = """
        Your goal is to generate a simple task for the user to do today. The task should not be complicated, should take very little time, should clearly assist with the user's goals and should easily fit into the user's schedule for the day. The user has previously indicated their long-term goal(s) to be the following: "[GOAL PLACEHOLDER]"
        """.replace("[GOAL PLACEHOLDER]", data[user_id]["goal"])

        if len(data[user_id]["past_days"]) > 0:
            successes = 0
            fails = 0
            try:
                random.shuffle(data[user_id]["past_days"])
            except Exception:
                pass
            data[user_id]["past_days"] = {x[0]:x[1] for x in list(data[user_id]["past_days"].items()) if (x[1] and successes <= 3) or (fails <= 3)}

            prompt += "\n\nPrevious goals the user has been instructed to complete in the past:\n" + '\n'.join([x[0] + " (" + ("SUCCEEDED" if x[1] else "FAILED") + ")" for x in list(past_goals.items())]) + "\nAvoid repeating tasks the user previously failed to complete, unless they are really beneficial.\n"

        prompt += """
        RESPONSE FORMAT:
        Task: [The task for the user to complete, keep the description very concise.]
        Reasoning: [Describe to the user how this task can help them achieve their goal.]

        RESPONSE IN ABOVE FORMAT:
        """

        output = await together_prompt(prompt)

        task = output['output']['choices'][0]['text'].split("Task: ")[1].strip()
        reasoning = task.split("Reasoning: ")[1].strip()
        task = task.split("Reasoning: ")[0]

        data[user_id]["today_task"] = task
        data[user_id]["today_task_reasoning"] = reasoning

    while True:
        embed=discord.Embed(title="Today's Task: " + data[user_id]["today_task"], description=data[user_id]["today_task_reasoning"], color=(0x90ee90 if data[user_id]["task_complete"] else 0xfc766a))
        if data[user_id]["task_complete"]:
            embed.add_field(name="Daily Task Complete!", value="You got 1 puzzle piece today! Keep it up!")
        embed.set_author(name="LifePuzzle")

        buttons = discord.ui.View()
        buttons.add_item(discord.ui.Button(style=(discord.ButtonStyle.green if data[user_id]["task_complete"] else discord.ButtonStyle.grey), emoji="✅", custom_id="complete", disabled=False))
        buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.red, emoji="🔄", custom_id="reset", disabled=data[user_id]["resets"] == 0 or data[user_id]["task_complete"]))
        buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.blurple, emoji="🧩", label="My LifePuzzle", custom_id="puzzle"))
        buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.grey, emoji="📍", label="Change Goal", custom_id="goal"))

        if msg == None:
            msg = await interaction.followup.send(embed=embed, view=buttons)
        else:
            await msg.edit(embed=embed, view=buttons, attachments=[])


        def check(m):
            return m.type not in [discord.InteractionType.application_command, discord.InteractionType.autocomplete] and m.channel.id == interaction.channel.id and m.message.id == msg.id and m.user.id == user_id
        try:
            interactionResponse = await client.wait_for('interaction', timeout=20, check=check)
        except asyncio.TimeoutError:
            await msg.delete()
            return
        
        await interactionResponse.response.defer()
        
        if interactionResponse.data['custom_id'] == "complete":
            data[user_id]["task_complete"] = not data[user_id]["task_complete"]
            data[user_id]["puzzle"].append(True)

            

        elif interactionResponse.data['custom_id'] == "reset":
            asyncio.create_task(msg.delete())
            data[user_id]["today_task"] = None
            data[user_id]["today_task_reasoning"] = None
            data[user_id]["task_complete"] = False
            data[user_id]["resets"] -= 1

            embed=discord.Embed(title="Task Reset!", description="Run /task to see your new task for today!", color=0xfc766a)
            embed.set_author(name="LifePuzzle")
            msg = await interactionResponse.followup.send(embed=embed)

            await asyncio.sleep(5)
            await msg.delete()
            return
        
        elif interactionResponse.data['custom_id'] == "puzzle":
            final_img = await generate_puzzle(data[user_id]["puzzle"])
            file_name = "generate" + str(random.randint(1,99999999)) + ".png"
            image_bytes = io.BytesIO()
            await client.loop.run_in_executor(None, functools.partial(final_img.save, image_bytes, "PNG", compress_level=4))
            await client.loop.run_in_executor(None, image_bytes.seek, 0)

            embed=discord.Embed(title="Your LifePuzzle", description=("You missed " + str(data[user_id]["puzzle"].count(False)) + " puzzle pieces, and you still have the chance to get " + str(28 - len(data[user_id]["puzzle"])) + " more pieces!" if data[user_id]["puzzle"].count(False) > 0 else str(28 - len(data[user_id]["puzzle"])) + " more puzzle pieces are waiting for you to collect them! Complete daily tasks to complete your collection!"), color=0xfc766a)
            embed.set_author(name="LifePuzzle")
            embed.set_image(url="attachment://" + file_name)
            asyncio.create_task(msg.delete())
            buttons = discord.ui.View()
            buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.grey, emoji="↩️", label="Back", custom_id="back"))
            msg = await interactionResponse.followup.send(embed=embed, file=discord.File(fp=image_bytes, filename=file_name), view=buttons)

            def check(m):
                return m.type not in [discord.InteractionType.application_command, discord.InteractionType.autocomplete] and m.channel.id == interaction.channel.id and m.message.id == msg.id and m.user.id == user_id
            try:
                interactionResponse = await client.wait_for('interaction', timeout=30, check=check)
            except asyncio.TimeoutError:
                await msg.delete()
                return
            
            await interactionResponse.response.defer()

        elif interactionResponse.data['custom_id'] == "goal":
            asyncio.create_task(msg.delete())
            msg = await set_goal(interactionResponse)
            
            if msg == None:
                data[user_id]["today_task"] = None
                data[user_id]["today_task_reasoning"] = None
                data[user_id]["task_complete"] = False

                embed=discord.Embed(title="Goal Changed!", description="Run /task to see your new task for today!", color=0xfc766a)
                embed.set_author(name="LifePuzzle")
                msg = await interactionResponse.followup.send(embed=embed)

                await asyncio.sleep(5)
                await msg.delete()
                return


    
    return

@client.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.data['custom_id'] == "display_task_button":
        await show_task(interaction)

@client.tree.command(name="task", description="Get your task of the day.", nsfw=False, auto_locale_strings=True)
async def task_slash(interaction: discord.Interaction):
    await show_task(interaction)
    return

if __name__ == "__main__":
    client.run(bot_token)