import random
import together
import time

together.api_key = "93620393f8368d94029be74aae01279d90adeb5ce407803ecaf974354af59263"

while True: 
    goal = input("What are some goals you want to achieve? ")

    prompt = """
    The user has stated that they want their goal to be: "[GOAL PLACEHOLDER]"
    """.replace("[GOAL PLACEHOLDER]", goal.strip())

    prompt += """
    Is this a good long-term goal? Is this goal realistic, achievable, positive and clear?

    RESPONSE FORMAT, STRICTLY FOLLOW THIS FORMAT:
    Result: ["T" or "F", signifying whether or not the goal meets the criteria]
    Reasoning: [Message to the user explaining why the goal meets/doesn't meet the criteria, be personal and considerate.]

    RESPONSE IN ABOVE FORMAT:
    """

    output = together.Complete.create(
        prompt = prompt, 
        model = "togethercomputer/llama-2-13b-chat", 
        max_tokens = 256,
        temperature = 0.8,
        top_k = 60,
        top_p = 0.6,
        repetition_penalty = 1.1,
        stop = ['<human>', '\n\n']
        )

    try:
        result = output['output']['choices'][0]['text'].split("Result: ")[1]
        reasoning = result.split("Reasoning: ")[1].strip()
        result = result.split("Reasoning: ")[0].upper().replace("TRUE", "T").replace("Y", "T").replace("YES", "T").strip()
    except Exception as e:
        print(str(e))
        print("Got bad response in task checker, skipping :(")
        break

    if result == "T":
        break
    else:
        print(reasoning)
        print()
        action = input("Retry? (Y/N)").upper()
        if action == "Y":
            continue
        else:
            break

past_goals = {}

errors = 0

while True:
    if errors > 2:
        print("TOO MANY ERRORS")
        break
    
    prompt = """
    Your goal is to generate a simple task for the user to do today. The task should not be complicated, should take very little time, should clearly assist with the user's goals and should easily fit into the user's schedule for the day. The user has previously indicated their goals to be the following: "[GOAL PLACEHOLDER]"
    """.replace("[GOAL PLACEHOLDER]", goal)

    if len(past_goals) > 0:
        successes = 0
        fails = 0
        try:
            random.shuffle(past_goals)
        except Exception:
            pass
        past_goals = {x[0]:x[1] for x in list(past_goals.items()) if (x[1] and successes <= 3) or (fails <= 3)}

        prompt += "\n\nPrevious goals the user has been instructed to complete in the past:\n" + '\n'.join([x[0] + " (" + ("SUCCEEDED" if x[1] else "FAILED") + ")" for x in list(past_goals.items())]) + "\nAvoid repeating tasks the user previously failed to complete, unless they are really beneficial.\n"

    prompt += """
    RESPONSE FORMAT:
    Task: [The task for the user to complete]
    Reasoning: [How this can help the user achieve their goal]

    RESPONSE:
    """

    output = together.Complete.create(
        prompt = prompt, 
        model = "togethercomputer/llama-2-7b-chat", 
        max_tokens = 256,
        temperature = 0.8,
        top_k = 60,
        top_p = 0.6,
        repetition_penalty = 1.1,
        stop = ['<human>', '\n\n']
        )

    try:
        task = output['output']['choices'][0]['text'].split("Task: ")[1].strip()
        reasoning = task.split("Reasoning: ")[1].strip()
        task = task.split("Reasoning: ")[0]
    except Exception:
        errors += 1
        print("Got bad response, retrying in 3...")
        time.sleep(3)
        continue

    print()
    print("Your task is: " + task)
    print()
    print(reasoning)
    action = input("(R)etry, (S)ucceeded, (F)ailed, (Any)Stop ").upper()
    if action == "R":
        continue
    elif action == "S":
        past_goals[task] = True
        continue
    elif action == "F":
        past_goals[task] = False
        continue
    break