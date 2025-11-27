from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize model and tokenizer
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"  # or "Qwen/Qwen2.5-3B-Instruct"
print(f"Loading model: {MODEL_NAME}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto"
)

print("Model loaded successfully!")

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        history = data.get('history', [])
        
        # Build conversation history
        messages = []
        
        # Add system prompt for Mongolian
        messages.append({
            "role": "system",
            "content": "Та монгол хэл дээр ярьдаг туслах юм. Хэрэглэгчид монгол хэлээр хариулт өгнө үү."
        })
        
        # Add conversation history
        for msg in history[-10:]:  # Keep last 10 messages for context
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Generate response
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
        
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        
        generated_ids = [
            output_ids[len(input_ids):] 
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        
        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        return jsonify({
            'response': response,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'response': f'Алдаа гарлаа: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'online',
        'message': 'Mongolian Chatbot API is running! 🇲🇳',
        'endpoints': {
            '/': 'GET - This page',
            '/chat': 'POST - Send chat messages',
            '/health': 'GET - Check server health'
        },
        'model': MODEL_NAME,
        'usage': {
            'example': {
                'url': '/chat',
                'method': 'POST',
                'body': {
                    'message': 'Сайн байна уу?',
                    'history': []
                }
            }
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'model': MODEL_NAME})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)