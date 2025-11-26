from flask import Flask, request, render_template_string
import requests, re, os

app = Flask(__name__)

HTML = """
<!doctype html>
<html>
<head>
<title>Instagram Multi UID Lookup</title>
<style>
body{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin:40px;
    background:#f0f2f5;
}
h2{
    text-align:center;
    color:#333;
}
input,textarea{
    width:100%;
    padding:12px;
    font-size:14px;
    margin-top:10px;
    border-radius:8px;
    border:1px solid #ccc;
    box-sizing:border-box;
}
button{
    padding:12px 25px;
    font-size:16px;
    margin-top:15px;
    cursor:pointer;
    border:none;
    border-radius:8px;
    background: #007bff;
    color:white;
    transition:0.3s;
}
button:hover{
    background:#0056b3;
}
.box{
    background:white;
    padding:15px;
    border-radius:12px;
    border-left:5px solid #007bff;
    box-shadow:0 4px 6px rgba(0,0,0,0.1);
    margin-top:15px;
}
.box a{
    color:#007bff;
    text-decoration:none;
}
.box a:hover{
    text-decoration:underline;
}
hr{
    margin:30px 0;
    border:0;
    height:1px;
    background:#ccc;
}
</style>
</head>
<body>
<h2>Instagram UID Lookup (Cookie Login)</h2>

<b>Enter Login Cookie:</b>
<input id="cookie" placeholder="Paste sessionid cookie here">

<b>Enter UID list (one per line):</b>
<textarea id="uids" placeholder="123456789\\n987654321\\n456789123"></textarea><br>

<button onclick="send()">Check UID List</button>

<hr>

<b>Enter Accounts (number|password|cookie):</b>
<textarea id="accs" placeholder="9999999999|pass123|sessionid=xxxxxx"></textarea><br>

<button onclick="checkByCookie()">Detect UIDs & Check</button>

<div id="result"></div>

<script>
function send(){
    fetch('/check', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({
            cookie: document.getElementById('cookie').value,
            uids: document.getElementById('uids').value
        })
    }).then(r=>r.text()).then(d=>{
        document.getElementById('result').innerHTML = d;
    });
}

function checkByCookie(){
    fetch('/cookieCheck', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({
            accs: document.getElementById('accs').value
        })
    }).then(r=>r.text()).then(d=>{
        document.getElementById('result').innerHTML = d;
    });
}
</script>
</body></html>
"""

# ---------------- INSTAGRAM LOOKUP --------------------

def get_info(uid, cookie):
    headers = {
        "User-Agent": "Instagram 297.0.0.34.109 Android",
        "Accept": "*/*",
        "Cookie": "ds_user_id=51850321845;sessionid=51850321845%3APhgBmvhV0MSejg%3A16%3AAYj06XUakX5qV0sS4GC49JUgJUh_m_UVjzvTTsiuUw"
    }
    url = f"https://i.instagram.com/api/v1/users/{uid}/info/"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200 and "user" in r.json():
            u = r.json()["user"]
            return {
                "username": u.get("username"),
                "name": u.get("full_name"),
                "private": u.get("is_private"),
                "verified": u.get("is_verified"),
                "followers": u.get("follower_count"),
                "following": u.get("following_count"),
                "bio": u.get("biography"),
                "dp": u.get("hd_profile_pic_url_info",{}).get("url")
            }
    except:
        return None
    return None

def extract_uid(cookie):
    m = re.search(r"ds_user_id=(\d+)", cookie)
    return m.group(1) if m else None

def save_to_file(uid, username=""):
    """हर बार नई file बनाकर UID save करेगा"""
    if not os.path.exists("saved"):
        os.makedirs("saved")
    # नई फाइल नंबर निर्धारित करना
    existing = [int(f.replace("anox","").replace(".txt","")) for f in os.listdir("saved") if f.startswith("anox")]
    next_num = max(existing)+1 if existing else 1
    filename = f"saved/anox{next_num}.txt"
    with open(filename,"w", encoding="utf-8") as f:
        f.write(f"{uid} | {username}\n")
    return filename

# ---------------- ROUTES --------------------

@app.route("/")
def home():
    return HTML

@app.route("/check", methods=["POST"])
def check():
    cookie = request.json.get("cookie","").strip()
    uids = request.json.get("uids","").strip().splitlines()
    final = ""

    for uid in uids:
        uid = uid.strip()
        if not uid.isdigit():
            final += f"<div class='box'>❌ Invalid UID: {uid}</div>"
            continue

        data = get_info(uid, cookie)
        if data:
            save_to_file(uid, data['username'])
            final += show(uid, data)
        else:
            final += f"<div class='box'>❌ Blocked/Private/Invalid: {uid}</div>"

    return final

@app.route("/cookieCheck", methods=["POST"])
def cookieCheck():
    accounts = request.json.get("accs","").strip().splitlines()
    final = ""

    for acc in accounts:
        parts = acc.split("|")
        if len(parts) != 3:
            final += f"<div class='box'>❌ Invalid Format: {acc}</div>"
            continue

        number, pwd, cookie = parts
        uid = extract_uid(cookie)

        if not uid:
            final += f"<div class='box'>⚠️ Cookie UID Not Detect: {acc}</div>"
            continue

        data = get_info(uid, cookie)
        if data:
            save_to_file(uid, data['username'])
            final += show(uid, data)
        else:
            final += f"<div class='box'>❌ Failed: {uid}</div>"

    return final

def show(uid, data):
    return f"""
    <div class='box'>
    <b>UID:</b> {uid}<br>
    <b>Username:</b> {data['username']}<br>
    <b>Name:</b> {data['name']}<br>
    <b>Followers:</b> {data['followers']} | <b>Following:</b> {data['following']}<br>
    <b>Private:</b> {data['private']} | <b>Verified:</b> {data['verified']}<br>
    <b>Bio:</b> {data['bio']}<br>
    <b>DP:</b> <a href='{data['dp']}' target='_blank'>Open Photo</a>
    </div>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2202)
