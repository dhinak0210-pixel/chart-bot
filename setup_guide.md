# Agentic AI Chatbot - Setup & Run Guide

Congratulations! Your zero-cost Agentic AI Chatbot project is fully built and ready to go. Below are the steps to get your free API keys, configure the application, install dependencies, and run the system.

---

## 🔑 1. How to Get Your Free API Keys

The chatbot supports three free-tier providers. You can get keys for any or all of them:

### Option A: NVIDIA API Key (Recommended - PRE-CONFIGURED)
We have already pre-configured the key you provided in your `.env` file!
If you ever need another key:
1. Go to [build.nvidia.com](https://build.nvidia.com/).
2. Select a model (e.g. Llama-3.3-70b-instruct) and click **Get API Key**.
3. Copy the key and place it in the `.env` file under `NVIDIA_API_KEY`.

### Option B: Groq API Key
1. Navigate to the [Groq Console](https://console.groq.com/).
2. Log in or create a free account.
3. Go to the **API Keys** section in the sidebar.
4. Click **Create API Key**, name it, and copy it immediately.

### Option C: Google Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Log in with your standard Google Account.
3. Click on the **Get API Key** button in the top left.
4. Click **Create API Key** and copy it.

---

## 📁 2. Configuration (`.env`)

A `.env` file has been created for you in the project directory (`/home/dhina/ai agent hackthon`). It contains:
```env
# Groq API Key
GROQ_API_KEY=

# Google Gemini API Key
GEMINI_API_KEY=

# NVIDIA API Key (PRE-CONFIGURED WITH YOUR KEY)
NVIDIA_API_KEY=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
```

*Note: You can also enter/overwrite keys directly in the Streamlit web interface sidebar.*

---

## 📦 3. Install Dependencies

Install the required packages using `pip`:
```bash
pip install -r requirements.txt
```

---

## 🚀 4. How to Start the App

Since dependencies have been installed in a Python virtual environment (`venv`), start the Streamlit development server using the virtual environment's executable:
```bash
venv/bin/streamlit run app.py
```
Or by activating the virtual environment first:
```bash
source venv/bin/activate
streamlit run app.py
```
This will start the server and output the local URL (usually `http://localhost:8501`) to open in your web browser.

---

## 🧠 5. How the ReAct Loop Works Under the Hood

When you submit a query, the agent performs the following steps:

1. **Thought**: The agent decides what it needs to do to answer the user query.
2. **Action**: If it needs external data, it outputs a strict JSON formatting block, e.g.:
   `Action: {"tool_name": "search_wikipedia", "parameters": {"query": "Mars"}}`
3. **Observation**: The Python system intercepts this JSON block, executes the corresponding function from `tools.py` safely, and returns the output as an `Observation` back to the LLM.
4. **Final Answer**: Once the agent has sufficient information, it delivers the answer to the screen. All intermediate thoughts and actions are printed in real-time in the **Thought Process Log** in the sidebar.
