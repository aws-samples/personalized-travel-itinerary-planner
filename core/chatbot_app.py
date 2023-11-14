import streamlit as st #all streamlit commands will be available through the "st" alias
import travel_planner #reference to local lib script

st.set_page_config(page_title="Personalized Travel Itinerary Planner") #HTML title
st.title("Personalized Travel Itinerary Planner") #page title

human_icon = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
ai_icon = "https://cdn-icons-png.flaticon.com/512/9887/9887771.png"

def input_event():

    lc = st.session_state["llm_chain"]
    ch  = st.session_state["llm_app"]
    ip = st.session_state.input
    res, no_of_tokens = ch.exec_chain(lc, ip)
    question_chain = {
        "question": ip,
        "id": len(st.session_state.questions),
        "tokens": no_of_tokens,
    }
    st.session_state.questions.append(question_chain)

    st.session_state.answers.append(
        {"answer": res, "id": len(st.session_state.questions)}
    )
    st.session_state.input = ""

def op_human_message(query):
    col1, col2 = st.columns([1, 12])

    with col1:
       st.image(human_icon, use_column_width="always")
    with col2:
        st.warning(query["question"])

def write_user_id(user_id_text):
    col1, col2 = st.columns([1, 12])

    with col1:
       st.image(human_icon, use_column_width="always")
    with col2:
        st.warning(user_id_text)


def op_answer(answer):
    col1, col2 = st.columns([1, 12])
    with col1:
       st.image(ai_icon, use_column_width="always")
    with col2:
        st.info(answer["response"])


def op_ai_response(response):
    chat = st.container()
    with chat:
        op_answer(response["answer"])



input_user_id = None

if input_user_id is None:
   input_user_id = st.text_input(
        "Please enter your User ID.", key="user_id_input"
    )


if input_user_id: #run the code in this if block after the user submits a chat message
    write_user_id("User ID: " + str(input_user_id))
    

if input_user_id:
    if "user_id" in st.session_state:
        user_id = st.session_state["user_id"]
    else:
        user_id = input_user_id
        st.session_state["user_id"] = user_id

    if "questions" not in st.session_state:
        st.session_state.questions = []

    if "answers" not in st.session_state:
        st.session_state.answers = []

    if "input" not in st.session_state:
        st.session_state.input = ""

    if "llm_chain" not in st.session_state:
        if input_user_id:
            st.session_state["llm_app"] = travel_planner
            st.session_state["llm_chain"] = travel_planner.get_bedrock_chain(user_id)

    with st.container():
        for query, response in zip(st.session_state.questions, st.session_state.answers):
            op_human_message(query)
            op_ai_response(response)


    st.markdown("---")
    input = st.text_input(
        "Please enter your question here.", key="input", on_change=input_event
    )