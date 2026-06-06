"""Check what RAGAS needs and what's available."""
try:
    import ragas
    print("ragas version:", ragas.__version__)
except Exception as e:
    print("ragas import failed:", e)

try:
    from langchain_groq import ChatGroq
    print("langchain_groq: OK")
except Exception as e:
    print("langchain_groq failed:", e)

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    print("langchain_openai: OK")
except Exception as e:
    print("langchain_openai failed:", e)

try:
    from groq import AsyncGroq
    print("groq async: OK")
except Exception as e:
    print("groq async failed:", e)

print("Done")
