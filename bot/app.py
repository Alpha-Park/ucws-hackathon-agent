from flask import Flask, request, jsonify

from bot.services import AgentService

app = Flask(__name__)
service = AgentService()

@app.route('/chat', methods=['POST'])
async def chat():
    data = request.get_json()
    user_message = data.get('message', '')

    try:
        service = AgentService()
        user_id = "test_user"
        session_id = "test_session_1"  # 每次测试换一个 ID
        print(f"\nUser: {user_id}")

        # Use await to execute the async function
        response = await service.process_request(user_id, session_id, user_message)

        # response is a string (based on current services.py), so we use it directly
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True,port=3000)