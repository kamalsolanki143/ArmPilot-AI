"""
ArmPilot-AI — Chat Completion Example
Demonstrates loading a model and using the OpenAI-compatible chat API.
"""

from app.services.inference_service import inference_service
from app.schemas.inference import ChatCompletionRequest, ChatMessage


def main() -> None:
    model_id = "llama-3.2-1b-instruct"

    # List available models
    print("Available models:")
    for m in inference_service.list_models():
        print(f"  {m.id} — {m.name} ({m.size_mb:.0f} MB)" if m.size_mb else f"  {m.id} — {m.name}")
    print()

    # Load the model
    print(f"Loading model '{model_id}'...")
    try:
        inference_service.load_model(model_id, n_threads=4)
    except Exception as e:
        print(f"Failed to load model: {e}")
        print("Place a .gguf model file in the models/ directory and try again.")
        return
    print(f"Model loaded.\n")

    # Simple completion
    print("--- Simple Completion ---")
    request = ChatCompletionRequest(
        model=model_id,
        messages=[
            ChatMessage(role="system", content="You are a helpful ARM64 hardware expert."),
            ChatMessage(role="user", content="What are the key advantages of ARM64 for AI inference?"),
        ],
        max_tokens=256,
        temperature=0.7,
    )

    response = inference_service.chat_completion(request)
    print(f"Response: {response.choices[0].message.content}")
    print(f"Tokens: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}")
    print()

    # Multi-turn conversation
    print("--- Multi-Turn Conversation ---")
    messages = [
        ChatMessage(role="system", content="You are a helpful AI assistant specialized in Arm processors."),
    ]

    prompts = [
        "What is the Neoverse architecture?",
        "How does it compare to x86 for inference workloads?",
        "What is SVE2 and why does it matter for AI?",
    ]

    for user_msg in prompts:
        messages.append(ChatMessage(role="user", content=user_msg))
        print(f"User: {user_msg}")

        request = ChatCompletionRequest(
            model=model_id,
            messages=messages,
            max_tokens=256,
            temperature=0.7,
        )

        response = inference_service.chat_completion(request)
        assistant_msg = response.choices[0].message.content
        messages.append(ChatMessage(role="assistant", content=assistant_msg))

        print(f"Assistant: {assistant_msg}")
        print(f"  [{response.usage.total_tokens} tokens]\n")

    # Streaming example
    print("--- Streaming Completion ---")
    stream_request = ChatCompletionRequest(
        model=model_id,
        messages=[ChatMessage(role="user", content="List 3 reasons to use ARM64 for edge AI.")],
        max_tokens=128,
        temperature=0.7,
        stream=True,
    )

    print("User: List 3 reasons to use ARM64 for edge AI.")
    print("Assistant: ", end="", flush=True)

    for chunk in inference_service.chat_completion_stream(stream_request):
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n")

    # Cleanup
    inference_service.unload()
    print("Model unloaded.")


if __name__ == "__main__":
    main()
