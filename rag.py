# import os
# from dotenv import load_dotenv
# from langchain.prompts import PromptTemplate
# # ⚠️ We replace RetrievalQA with LLMChain for explicit input control
# from langchain.chains import LLMChain 
# from dataLoading import vectorstore  # Load cached vectorstore!
# from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
# from typing import Literal

# load_dotenv()

# # Define the valid pace options
# Pace = Literal["low", "moderate", "advance"]

# def initialize_hf_llm():
#     """Initializes the LLM from HuggingFace."""
#     token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
#     if not token:
#         raise EnvironmentError(
#             "HUGGINGFACEHUB_API_TOKEN is not set. Please get a token and set it in your .env file."
#         )
        
#     print("DEBUG: Initializing HuggingFace LLM...")
#     base_llm = HuggingFaceEndpoint(
#         repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
#         huggingfacehub_api_token=token,
#         temperature=0.3,
#         max_new_tokens=1500,
#     )

#     llm = ChatHuggingFace(llm=base_llm)
#     print("DEBUG: HuggingFace LLM initialized successfully.")
#     return llm

# # Initialize the LLM globally
# llm = None
# try:
#     llm = initialize_hf_llm()
# except Exception as e:
#     print(f"\n❌ CRITICAL LLM INITIALIZATION ERROR: {e}")
#     print("Please check your .env file and ensure HUGGINGFACEHUB_API_TOKEN is correct.")


# def create_components(vectorstore, llm):
#     """
#     Creates the necessary RAG components (retriever and LLM chain).
#     """
#     if vectorstore is None or llm is None:
#         return None

#     # This prompt requires four input variables: context, topic, level, and pace.
#     prompt_template = """
#     You are an AI mathematics tutor for a student in Sierra Leone's Senior Secondary School (SSS).
#     Your task is to generate a comprehensive, personalized lesson on a specific topic based on the provided curriculum context.

#     Curriculum Context (This defines WHAT should be taught):
#     ---
#     {context}
#     ---

#     User Request Details:
#     - **Topic:** {topic}
#     - **SSS Level:** {level}
#     - **Learning Pace:** {pace}

#     **INSTRUCTIONS for Lesson Tailoring (Based on Learning Pace):**
#     1. **Structure:** Start with a brief Introduction, followed by Detailed Notes, and conclude with Practice Exercises.
#     2. **Pace Adjustment:**
#         - If **'low' (Beginner)**: Focus on **basic concepts and fundamentals**. Use very simple analogies. Provide **many, highly detailed, step-by-step solved examples**. Use short paragraphs and frequent bullet points.
#         - If **'moderate'**: Provide a balanced explanation, covering both concepts and standard applications. Include a few key examples.
#         - If **'advance' (Advanced)**: Offer a **quick theory recap**. The main focus should be on **complex problem-solving**, advanced applications, and questions that require critical thinking or proof.

#     Generate the complete, tailored lesson notes now. The output must be educational and structured clearly.
#     """
    
#     CUSTOM_PROMPT = PromptTemplate(
#         template=prompt_template, 
#         input_variables=["context", "topic", "level", "pace"]
#     )
    
#     # ⚠️ Use LLMChain directly to ensure all custom variables are passed.
#     llm_chain = LLMChain(prompt=CUSTOM_PROMPT, llm=llm)

#     return {
#         "retriever": vectorstore.as_retriever(search_kwargs={"k": 3}),
#         "llm_chain": llm_chain
#     }

# # Initialize RAG components globally
# rag_components = create_components(vectorstore, llm)
# print(f"DEBUG: RAG Chain initialized status: {'READY' if rag_components else 'FAILED'}") 


# def generate_lesson(topic: str, level: str, pace: Pace):
#     """
#     Generates a personalized lesson by manually orchestrating retrieval and generation.
#     """
#     if rag_components is None:
#         print("\n❌ RAG system not initialized. Cannot generate lesson. Check LLM and Vectorstore status.")
#         return

#     print(f"\n⚙️ Generating lesson for Topic: {topic} | Level: {level} | Pace: {pace}...")
    
#     retriever = rag_components["retriever"]
#     llm_chain = rag_components["llm_chain"]
#     source_documents = [] # Initialize empty list for source documents
    
#     try:
#         # 1. Retrieval Step: Retrieve relevant curriculum chunks
#         retrieval_query = f"SSS {level} Mathematics syllabus content for the topic: {topic}"
#         source_documents = retriever.get_relevant_documents(retrieval_query)
        
#         # 2. Context Formatting
#         context_text = "\n---\n".join([doc.page_content for doc in source_documents])

#         # 3. Generation Step: Pass ALL required inputs to the LLMChain.
#         input_data = {
#             "context": context_text,
#             "topic": topic,
#             "level": level,
#             "pace": pace
#         }
        
#         # 4. Invoke the LLMChain
#         result = llm_chain.invoke(input_data)
        
#         # The result from llm_chain.invoke is a dictionary containing the generated text under the 'text' key.
#         lesson_text = result['text']

#         # --- Display Results ---
#         print("\n" + "=" * 80)
#         print("✨ PERSONALIZED LESSON GENERATED ✨")
#         print("=" * 80)
#         print(lesson_text) 

#         print("\n" + "=" * 80)
#         print("📚 CURRICULUM SOURCES USED (For Contextual Generation)")
#         print("=" * 80)
        
#         if source_documents:
#             for i, doc in enumerate(source_documents, 1):
#                 page_info = doc.metadata.get('page', 'N/A')
#                 # If page is an integer, add 1 to make it human-readable (1-indexed)
#                 page_display = page_info + 1 if isinstance(page_info, int) else page_info
                
#                 print(f"\n--- Source Document {i} (Page {page_display}) ---")
#                 print(doc.page_content.strip())
#         else:
#             print("\n⚠️  No specific curriculum sources were found to augment the lesson.")

#     except Exception as e:
#         print(f"\n❌ Error during lesson generation: {str(e)}")


# def show_welcome_message():
#     """Display welcome message and instructions"""
#     print("\n" + "=" * 80)
#     print("🎓 AI-DRIVEN PERSONALIZED TUTOR (SSS MATH)")
#     print("=" * 80)
#     print("Welcome! I will generate a lesson based on your specified topic,")
#     print("SSS level, and the student's learning pace.")
#     print("Valid Paces: low, moderate, advance")
#     print("\nType 'exit' or 'quit' to leave.")
#     print("=" * 80)


# if __name__ == "__main__":
#     if rag_components is None:
#         print("\n🔴 System not fully ready. Fix initialization errors above before continuing.")
#     else:
#         show_welcome_message()

#         while True:
#             try:
#                 # 1. Get Topic
#                 topic = input("\n📝 Enter Lesson Topic (e.g., Trigonometry): ").strip()
#                 if topic.lower() in ["exit", "quit", "q"]:
#                     break
#                 if not topic:
#                     print("⚠️ Please enter a topic.")
#                     continue

#                 # 2. Get SSS Level
#                 level = input("🧑‍🎓 Enter SSS Level (1, 2, or 3): ").strip()
#                 if level.lower() in ["exit", "quit", "q"]:
#                     break
#                 if level not in ["1", "2", "3"]:
#                     print("⚠️ SSS Level must be 1, 2, or 3.")
#                     continue

#                 # 3. Get Pace
#                 pace = input("🏃‍♀️ Enter Learning Pace (low, moderate, advance): ").strip().lower()
#                 if pace.lower() in ["exit", "quit", "q"]:
#                     break
#                 if pace not in ["low", "moderate", "advance"]:
#                     print("⚠️ Pace must be 'low', 'moderate', or 'advance'.")
#                     continue
                    
#                 # Generate the lesson
#                 generate_lesson(topic, f"SSS {level}", pace)

#             except Exception as e:
#                 print(f"An unexpected error occurred: {e}")
#                 break

#         print("\n👋 Thank you for using the Personalized Tutor. Goodbye!")


import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain 
from dataLoading import initialize_vectorstore, get_available_subjects # Import new initialization functions
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from typing import Literal, Dict, Any, Optional

load_dotenv()

# Define the valid pace options
Pace = Literal["low", "moderate", "advance"]

# Global store for active components
LLM = None
RAG_COMPONENTS: Dict[str, Any] = {} # Store components keyed by subject name

def initialize_hf_llm():
    """Initializes the LLM from HuggingFace."""
    global LLM
    token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not token:
        raise EnvironmentError(
            "HUGGINGFACEHUB_API_TOKEN is not set. Please get a token and set it in your .env file."
        )
        
    print("DEBUG: Initializing HuggingFace LLM...")
    base_llm = HuggingFaceEndpoint(
        repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
        huggingfacehub_api_token=token,
        temperature=0.3,
        max_new_tokens=800,
    )

    LLM = ChatHuggingFace(llm=base_llm)
    print("DEBUG: HuggingFace LLM initialized successfully.")
    return LLM

def create_rag_components(subject_name: str, vectorstore, llm):
    """
    Creates the necessary RAG components (retriever and LLM chain) for a specific subject.
    """
    if vectorstore is None or llm is None:
        return None

    prompt_template = """
    You are an AI tutor specializing in {subject_name} for a student in Sierra Leone's Senior Secondary School (SSS).
    Your task is to generate a comprehensive, personalized lesson on a specific topic based on the provided curriculum context.

    Curriculum Context (This defines WHAT should be taught):
    ---
    {context}
    ---

    User Request Details:
    - **Subject:** {subject_name}
    - **Topic:** {topic}
    - **SSS Level:** {level}
    - **Learning Pace:** {pace}

    **INSTRUCTIONS for Lesson Tailoring (Based on Learning Pace):**
    1. **Structure:** Start with a brief Introduction, followed by Detailed Notes, and conclude with Practice Exercises.
    2. **Pace Adjustment:**
        - If **'low' (Beginner)**: Focus on **basic concepts and fundamentals**. Use very simple analogies. Provide **many, highly detailed, step-by-step solved examples**. Use short paragraphs and frequent bullet points.
        - If **'moderate'**: Provide a balanced explanation, covering both concepts and standard applications. Include a few key examples.
        - If **'advance' (Advanced)**: Offer a **quick theory recap**. The main focus should be on **complex problem-solving**, advanced applications, and questions that require critical thinking or proof.

    Generate the complete, tailored lesson notes now. The output must be educational and structured clearly.
    """
    
    CUSTOM_PROMPT = PromptTemplate(
        template=prompt_template, 
        input_variables=["context", "topic", "level", "pace", "subject_name"]
    )
    
    llm_chain = LLMChain(prompt=CUSTOM_PROMPT, llm=llm)

    return {
        "retriever": vectorstore.as_retriever(search_kwargs={"k": 3}),
        "llm_chain": llm_chain
    }


def load_subject_components(subject_name: str, llm):
    """Initialize or load vectorstore and RAG components for a given subject."""
    global RAG_COMPONENTS
    
    # 1. Initialize Vectorstore (loads or builds)
    print(f"DEBUG: Attempting to initialize vectorstore for {subject_name}...")
    vectorstore, _ = initialize_vectorstore(subject_name)
    print(f"DEBUG: Vectorstore initialization result for {subject_name}: {'SUCCESS' if vectorstore else 'FAILURE'}")

    if vectorstore:
        # 2. Create RAG components
        components = create_rag_components(subject_name, vectorstore, llm)
        if components:
            RAG_COMPONENTS[subject_name] = components
            print(f"DEBUG: RAG Chain initialized status for {subject_name}: READY")
            return True
        
    print(f"DEBUG: RAG Chain initialized status for {subject_name}: FAILED")
    return False


def generate_lesson(subject_name: str, topic: str, level: str, pace: Pace):
    """
    Generates a personalized lesson by manually orchestrating retrieval and generation.
    """
    components = RAG_COMPONENTS.get(subject_name)

    if components is None:
        print(f"\n❌ RAG system not initialized for {subject_name}. Cannot generate lesson.")
        return

    print(f"\n⚙️ Generating lesson for Subject: {subject_name} | Topic: {topic} | Level: {level} | Pace: {pace}...")
    
    retriever = components["retriever"]
    llm_chain = components["llm_chain"]
    
    try:
        # 1. Retrieval Step: Retrieve relevant curriculum chunks
        retrieval_query = f"SSS {level} {subject_name} syllabus content for the topic: {topic}"
        source_documents = retriever.get_relevant_documents(retrieval_query)
        
        # 2. Context Formatting
        context_text = "\n---\n".join([doc.page_content for doc in source_documents])

        # 3. Generation Step: Pass ALL required inputs to the LLMChain.
        input_data = {
            "context": context_text,
            "topic": topic,
            "level": level,
            "pace": pace,
            "subject_name": subject_name # Pass subject name for the prompt
        }
        
        result = llm_chain.invoke(input_data)
        lesson_text = result['text']

        # --- Display Results ---
        print("\n" + "=" * 80)
        print(f"✨ PERSONALIZED LESSON GENERATED ({subject_name} - {level}, {pace.upper()}) ✨")
        print("=" * 80)
        print(lesson_text) 
        
        # ⚠️ REMOVED: Source documents display section

    except Exception as e:
        print(f"\n❌ Error during lesson generation: {str(e)}")


def show_welcome_message(available_subjects: list):
    """Display welcome message and instructions"""
    print("\n" + "=" * 80)
    print("🎓 AI-DRIVEN PERSONALIZED TUTOR (SSS CURRICULUM)")
    print("=" * 80)
    print("Welcome! I will generate a lesson based on your specified criteria.")
    print(f"Available Subjects: {', '.join(available_subjects) if available_subjects else 'None'}")
    print("Valid Paces: low, moderate, advance")
    print("\nType 'exit' or 'quit' to leave.")
    print("=" * 80)


if __name__ == "__main__":
    
    # 0. Initialize LLM once
    try:
        initialize_hf_llm()
    except Exception as e:
        print(f"🔴 System initialization failed: {e}")
        exit()

    # 1. Discover available subjects
    available_subjects = get_available_subjects()
    if not available_subjects:
        print(f"🔴 ERROR: No curriculum folders found in '{CURRICULUM_ROOT}/'. Please check the setup.")
        exit()

    show_welcome_message(available_subjects)
    
    # 2. Main interactive loop
    while True:
        try:
            # 2a. Get Subject
            subject = input(f"\n📚 Enter Subject ({'/'.join(available_subjects)}): ").strip()
            if subject.lower() in ["exit", "quit", "q"]:
                break
            
            # Capitalize the first letter for consistency with folder names
            subject = subject.strip().capitalize()
            if subject not in available_subjects:
                print(f"⚠️ Invalid subject. Please choose from: {', '.join(available_subjects)}")
                continue

            # 2b. Load components for the selected subject (only runs if not cached)
            if subject not in RAG_COMPONENTS:
                if not load_subject_components(subject, LLM):
                    print(f"🔴 Could not load or build components for {subject}. Please fix the errors above.")
                    continue
            
            # Proceed with lesson details
            topic = input("📝 Enter Lesson Topic: ").strip()
            if not topic:
                print("⚠️ Please enter a topic.")
                continue

            level = input("🧑‍🎓 Enter SSS Level (1, 2, or 3): ").strip()
            if level not in ["1", "2", "3"]:
                print("⚠️ SSS Level must be 1, 2, or 3.")
                continue

            pace = input("🏃‍♀️ Enter Learning Pace (low, moderate, advance): ").strip().lower()
            if pace not in ["low", "moderate", "advance"]:
                print("⚠️ Pace must be 'low', 'moderate', or 'advance'.")
                continue
                
            # Generate the lesson
            generate_lesson(subject, topic, f"SSS {level}", pace)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break

    print("\n👋 Thank you for using the Personalized Tutor. Goodbye!")