from openai import OpenAI
from datetime import datetime
import json
import os
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key=os.getenv("OPENROUTER_API_KEY")
)

# ============================================
# TOOLS
# ============================================

def calculate(expression):
    try:
        result = eval(expression)
        return f"{expression} = {result}"
    except:
        return "Error: Invalid calculation"

def get_current_date():
    now = datetime.now()
    return f"Today is {now.strftime('%A, %d %B %Y')}. Time is {now.strftime('%I:%M %p')}."

def search_company(question):
    with open("company_data.txt", "r", encoding="utf-8") as f:
        company_data = f.read()

    lines = company_data.split("\n")
    question_words = set(question.lower().split())
    relevant_lines = []

    for line in lines:
        line_words = set(line.lower().split())
        if len(question_words.intersection(line_words)) > 0:
            relevant_lines.append(line)

    if relevant_lines:
        return "\n".join(relevant_lines[:8])
    return "No relevant company information found."

# ============================================
# AGENT BRAIN
# ============================================

def run_agent(user_question):

    tool_selector_prompt = """You are an AI agent with 3 tools:
1. calculate — for any maths or number calculations
2. get_date — for questions about today's date or time
3. search_company — for anything about TechNova company

Respond with ONLY one single JSON object. No explanation. No extra text. Just one JSON:
{"tool": "calculate", "input": "the expression"}
{"tool": "get_date", "input": ""}
{"tool": "search_company", "input": "the question"}"""

    tool_response = client.chat.completions.create(
        model="openrouter/auto",
        messages=[
            {"role": "system", "content": tool_selector_prompt},
            {"role": "user", "content": user_question}
        ]
    )

    raw = tool_response.choices[0].message.content.strip()

    # Take only the first line in case model returns multiple
    first_line = raw.split("\n")[0].strip()

    try:
        decision = json.loads(first_line)
        tool_name = decision["tool"]
        tool_input = decision["input"]
    except:
        return "Sorry, I couldn't process that question. Try rephrasing it!"

    # Use the right tool
    if tool_name == "calculate":
        tool_result = calculate(tool_input)
    elif tool_name == "get_date":
        tool_result = get_current_date()
    elif tool_name == "search_company":
        tool_result = search_company(tool_input)
    else:
        tool_result = "Unknown tool."

    # Get final answer
    final_response = client.chat.completions.create(
        model="openrouter/auto",
        messages=[
            {"role": "system", "content": "You are a helpful TechNova assistant. Answer the user's question using the tool result. Be friendly and concise. Max 3 sentences."},
            {"role": "user", "content": f"Question: {user_question}\nTool Result: {tool_result}"}
        ]
    )

    return final_response.choices[0].message.content

# ============================================
# MAIN LOOP
# ============================================

print("🤖 TechNova AI Agent ready! Type 'quit' to stop.")
print("I can calculate, check dates, and answer company questions!")
print("-" * 50)

while True:
    user_input = input("You: ")

    if user_input.lower() in ["quit", "exit", "bye"]:
        print("👋 Goodbye!")
        break

    print("⏳ Thinking...")
    answer = run_agent(user_input)
    print(f"Agent: {answer}")
    print("-" * 50)