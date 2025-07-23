import streamlit as st
import os
from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.serpapi_tools import SerpApiTools
from dotenv import load_dotenv
load_dotenv()

# Load API keys securely from environment (backend)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")

# Check for API keys and show error early if missing
if not GROQ_API_KEY or not SERP_API_KEY:
    st.error("API keys are missing. Please configure GROQ_API_KEY and SERP_API_KEY in your environment.")
    st.stop()

# Set environment variables for internal usage (if needed)
os.environ["GROQ_API_KEY"] = GROQ_API_KEY
os.environ["SERP_API_KEY"] = SERP_API_KEY

# Page config
st.set_page_config(
    page_title="AI Travel Planner 🌍",
    page_icon="🌎",
    layout="wide"
)

# Stylish Custom CSS
st.markdown("""
    <style>
    :root {
        --primary: #3498db;
        --accent: #e74c3c;
        --bg: #f4f6f7;
        --text: #2c3e50;
        --highlight: #2ecc71;
    }

    html, body, [data-testid="stAppViewContainer"] {
    overflow: auto !important;
    }

    .main {
        padding: 2rem;
        max-width: 1200px;
        margin: auto;
    }

    .stButton > button {
        width: 100%;
        border-radius: 10px;
        padding: 0.8rem;
        background-color: var(--accent) !important;
        color: white !important;
        font-weight: 600;
        transition: all 0.3s ease-in-out;
    }

    .stButton > button:hover {
        background-color: #c0392b !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 14px rgba(0,0,0,0.15);
    }

    .stSidebar .element-container {
        padding: 1rem;
        background-color: var(--bg);
        border-radius: 10px;
    }

    .travel-box {
        background-color: white;
        border-left: 6px solid var(--primary);
        padding: 1.5rem;
        margin: 2rem 0;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }

    h1, h2, h4 {
        color: var(--primary);
    }

    .spinner-text {
        font-size: 1.2rem;
        font-weight: bold;
        color: var(--primary);
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/airplane-take-off.png", use_column_width=True)
    st.title("Trip Preferences")
    
    destination = st.text_input("🌍 Destination")
    duration = st.number_input("📅 Duration (days)", 1, 30, 5)
    budget = st.select_slider("💰 Budget", ["Budget", "Moderate", "Luxury"], value="Moderate")
    travel_style = st.multiselect(
        "🎯 Travel Style",
        ["Culture", "Nature", "Adventure", "Relaxation", "Food", "Shopping"],
        default=["Culture", "Nature"]
    )

# Session state
st.session_state.setdefault("travel_plan", None)
st.session_state.setdefault("qa_expanded", False)

# Initialize Travel Agent
travel_agent = Agent(
    name="AI Travel Planner",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[SerpApiTools()],
    # instructions=[
    #     "You are a travel planning assistant.",
    #     "Use real-time web search to recommend hotels and attractions.",
    #     "Always include links and verify the info is current.",
    #     "Format the response in markdown with clear sections and bullet points."
    # ],
    instructions=[
    "You are a travel planning assistant.",
    "Use real-time web search to recommend hotels and attractions.",
    "When recommending a hotel, include 2–3 recent user reviews (if available).",
    "Format the response in markdown with sections.",
    "Use bullet points. Keep it clean and readable."
     ],
    show_tool_calls=True,
    markdown=True
)

# Header
st.title("🌎 AI Travel Planner")
st.markdown(f"""
    <div class="travel-box">
        <h4>Plan your dream trip in seconds ✈️</h4>
        <p><b>Destination:</b> {destination or "Not specified"}</p>
        <p><b>Duration:</b> {duration} day(s)</p>
        <p><b>Budget:</b> {budget}</p>
        <p><b>Style:</b> {', '.join(travel_style)}</p>
    </div>
""", unsafe_allow_html=True)

# Generate button
if st.button("✨ Generate Travel Plan"):
    if not destination:
        st.warning("Please enter a destination.")
    else:
        with st.spinner("🔍 Generating your personalized travel plan..."):
            try:
                prompt = f"""
                Plan a {duration}-day trip to {destination} with the following:
                - Budget level: {budget}
                - Travel style: {', '.join(travel_style)}
                
                Provide:
                1. Best time to visit
                2. Hotel recommendations with links and adrress link.
                3. Include 2 short real user reviews per hotel (if possible).
                4. For each review, say if it's positive, neutral, or negative. And also mention where the review is posted and it is taken from
4. Format nicely in markdown.
                5. Daily itinerary
                6. Local food suggestions and adrress links of restuarants
                7. Travel tips (transport, safety, etiquette)
                8. Estimated total cost
                
                Make sure to include reliable links and format nicely using markdown.
                """
                result = travel_agent.run(prompt)
                final_output = getattr(result, "content", str(result)).replace("∣", "|")
                st.session_state.travel_plan = final_output
                st.markdown(final_output)
            except Exception as err:
                st.error(f"An error occurred while generating your plan: {err}")

# Divider and Q&A section
st.divider()

qa_expander = st.expander("❓ Ask follow-up questions", expanded=st.session_state.qa_expanded)
with qa_expander:
    st.session_state.qa_expanded = True
    question = st.text_input("Your question:", placeholder="e.g., Is Uber available there?")
    if st.button("Get Answer", key="qa_button"):
        if not st.session_state.travel_plan:
            st.warning("Please generate a travel plan first.")
        elif question:
            with st.spinner("🔎 Searching for your answer..."):
                try:
                    context_question = f"""
                    Based on this travel plan for {destination}:
                    {st.session_state.travel_plan}

                    Please answer: {question}
                    """
                    followup = travel_agent.run(context_question)
                    st.markdown(getattr(followup, "content", str(followup)))
                except Exception as e:
                    st.error(f"Error fetching answer: {e}")
        else:
            st.warning("Please enter a question.")

from textblob import TextBlob
import re

# # Find bullet-pointed reviews (basic heuristic)
# review_lines = re.findall(r"- (.*)", st.session_state.travel_plan)

# st.markdown("### 🧠 Sentiment Analysis of Reviews")
# for review in review_lines:
#     blob = TextBlob(review)
#     polarity = blob.sentiment.polarity
#     if polarity > 0.2:
#         sentiment = "🟢 Positive"
#     elif polarity < -0.2:
#         sentiment = "🔴 Negative"
#     else:
#         sentiment = "🟡 Neutral"
#     st.markdown(f"- {review} → **{sentiment}**")

if st.session_state.travel_plan and isinstance(st.session_state.travel_plan, str):
    review_lines = re.findall(r"- .*?Review[:\-] (.*)", st.session_state.travel_plan)

    # st.markdown("### 🧠 Sentiment Analysis of Reviews")
    # for review in review_lines:
    #     blob = TextBlob(review)
    #     polarity = blob.sentiment.polarity
    #     if polarity > 0.2:
    #         sentiment = "🟢 **Positive**"
    #     elif polarity < -0.2:
    #         sentiment = "🔴 **Negative**"
    #     else:
    #         sentiment = "🟡 **Neutral**"
    #     st.markdown(f"- ✍️ *{review}* → {sentiment}")

st.markdown("---")
st.header("💬 Chat with the Travel Planner")

# Initialize history if not already
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Show previous messages
for i, msg in enumerate(st.session_state.chat_history):
    if msg.startswith("User:"):
        st.markdown(f"**🧑 You:** {msg[6:]}")
    elif msg.startswith("Planner:"):
        st.markdown(f"**🤖 Planner:** {msg[9:]}")

# Input for new user message
user_msg = st.text_input("Type your message", key="chat_input")

if st.button("Send", key="send_chat"):
    if not user_msg.strip():
        st.warning("Please type a message.")
    else:
        context = "\n".join(st.session_state.chat_history)
        full_prompt = f"{context}\nUser: {user_msg}\nPlanner:"

        with st.spinner("✍️ Planner is replying..."):
            try:
                reply = travel_agent.run(full_prompt)
                reply_text = getattr(reply, "content", str(reply))

                # Save chat history
                st.session_state.chat_history.append(f"User: {user_msg}")
                st.session_state.chat_history.append(f"Planner: {reply_text}")
                # Optional: clear input manually (Streamlit will rerun everything)
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Chat error: {e}")

if st.button("🗑️ Clear Chat History"):
    st.session_state.chat_history = []
    st.experimental_rerun()



