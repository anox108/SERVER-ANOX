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
.redbox{
    background:#ffe5e5;
    padding:15px;
    border-radius:12px;
    border-left:5px solid red;
    box-shadow:0 4px 6px rgba(0,0,0,0.1);
    margin-top:15px;
}
.dupbox{
    background:#fff3cd;
    padding:15px;
    border-radius:12px;
    border-left:5px solid #ff9800;
    box-shadow:0 4px 6px rgba(0,0,0,0.1);
    margin-top:15px;
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
        "Cookie": cookie
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
    if not os.path.exists("saved"):
        os.makedirs("saved")
    existing = [int(f.replace("anox","").replace(".txt","")) for f in os.listdir("saved") if f.startswith("anox")]
    next_num = max(existing)+1 if existing else 1
    filename = f"saved/anox{next_num}.txt"
    with open(filename,"w", encoding="utf-8") as f:
        f.write(f"{uid} | {username}\n")
    return filename

# ---------------- UID RESULT BOX --------------------

def show(uid, data, red=False, duplicate=False):
    box_class = "box"
    if red:
        box_class = "redbox"
    if duplicate:
        box_class = "dupbox"

    return f"""
    <div class='{box_class}'>
    <b>UID:</b> {uid}<br>
    <b>Username:</b> {data['username']}<br>
    <b>Name:</b> {data['name']}<br>
    <b>Followers:</b> {data['followers']} | <b>Following:</b> {data['following']}<br>
    <b>Private:</b> {data['private']} | <b>Verified:</b> {data['verified']}<br>
    <b>Bio:</b> {data['bio']}<br>
    <b>DP:</b> <a href='{data['dp']}' target='_blank'>Open Photo</a>
    </div>
    """

# ---------------- ROUTES --------------------

@app.route("/")
def home():
    return HTML

@app.route("/check", methods=["POST"])
def check():
    cookie = request.json.get("cookie","").strip()
    uids = request.json.get("uids","").strip().splitlines()

    final = ""
    seen = set()

    total = len(uids)
    valid = 0
    invalid = 0
    duplicate = 0

    final += f"<div class='box'><b>Total Input UID:</b> {total}</div>"

    for uid in uids:
        uid = uid.strip()
        if not uid.isdigit():
            invalid += 1
            final += f"<div class='box'>❌ Invalid UID: {uid}</div>"
            continue

        if uid in seen:
            duplicate += 1
            final += f"<div class='dupbox'>⚠️ Duplicate UID: {uid}</div>"
            continue

        seen.add(uid)

        data = get_info(uid, cookie)
        if data:
            valid += 1
            save_to_file(uid, data['username'])

            # follower > 5000 => RED BOX
            red = data["followers"] >= 5000
            final += show(uid, data, red=red)

        else:
            invalid += 1
            final += f"<div class='box'>❌ Blocked/Private/Invalid: {uid}</div>"

    final = f"""
        <div class='box'>
        <b>Total:</b> {total}<br>
        <b>Valid:</b> {valid}<br>
        <b>Invalid:</b> {invalid}<br>
        <b>Duplicate:</b> {duplicate}<br>
        </div>
    """ + final

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

            red = data['followers'] >= 5000
            final += show(uid, data, red=red)
        else:
            final += f"<div class='box'>❌ Failed: {uid}</div>"

    return final

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=21062)
