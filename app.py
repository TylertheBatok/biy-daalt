from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch
import gradio as gr



model_name = "Qwen/Qwen2.5-3B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=quantization_config,
    device_map="auto",
    trust_remote_code=True
)

model.eval()


def respond(message, history):
    
    messages = []
    for user_msg, assistant_msg in history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": assistant_msg})
    messages.append({"role": "user", "content": message})
    
    text = tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    inputs = tokenizer([text], return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
            use_cache=True
        )
    
    response = tokenizer.decode(
        outputs[0][inputs.input_ids.shape[1]:], 
        skip_special_tokens=True
    )
    
    return response

demo = gr.ChatInterface(
    respond,
    title="Qwen2.5-3B Chatbot",
    description="Local chatbot powered by Qwen2.5-3B-Instruct (Optimized)",
    examples=["Hello!", "What is AI?", "Write a short story."],
    cache_examples=False
)

demo.launch(
    server_name="127.0.0.1",
    server_port=7860,
    share=False
)