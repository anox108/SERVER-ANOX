from flask import Flask, request, render_template_string
import os
import requests
import time

app = Flask(__name__)

def send_messages(token, convo_id, hater_name, message_file, time_interval):
    with open(message_file, 'r') as file:
        messages = file.readlines()

    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; Samsung Galaxy S9 Build/OPR6.170623.017; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.125 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
        'referer': 'www.google.com'
    }

    for message in messages:
        url = "https://graph.facebook.com/v17.0/{}/".format('t_' + convo_id)
        parameters = {'access_token': token, 'message': hater_name + ' ' + message.strip()}
        response = requests.post(url, json=parameters, headers=headers)

        if response.ok:
            print("[+] Message sent:", hater_name + ' ' + message.strip())
        else:
            print("[x] Failed to send message:", hater_name + ' ' + message.strip())
        time.sleep(time_interval)

@app.route('/')
def index():
    return open("index.html").read()

@app.route('/send_messages', methods=['POST'])
def handle_form():
    token = request.form['token']
    convo_id = request.form['convo']
    hater_name = request.form['hatersname']
    message_file = request.files['message']
    time_interval = int(request.form['time'])

    # Save the uploaded file temporarily
    file_path = os.path.join("/tmp", message_file.filename)
    message_file.save(file_path)

    # Call the send_messages function
    send_messages(token, convo_id, hater_name, file_path, time_interval)

    # Remove the temporary file
    os.remove(file_path)

    return "Messages sent successfully!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
