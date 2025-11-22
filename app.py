# FIXED FULL SYSTEM – ONLY BD ALLOWED
# by ChatGPT

from flask import Flask, request, jsonify
import asyncio
import json, requests, aiohttp, binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf.json_format import MessageToDict, MessageToJson

import like_pb2
import like_count_pb2
import uid_generator_pb2

app = Flask(__name__)

# -------------------------------------
# SERVER SETTINGS (ONLY BD ALLOWED)
# -------------------------------------
ALLOWED_SERVER = "BD"

# -------------------------------------
# LOAD TOKENS (BD ONLY)
# -------------------------------------
def load_bd_tokens():
    try:
        with open("token_bd.json", "r") as f:
            data = json.load(f)
        if not data:
            return None
        return data
    except:
        return None

# -------------------------------------
# ENCRYPT FUNCTION
# -------------------------------------
def encrypt(data):
    key = b'Yg&tc%DEuh6%Zc^8'
    iv  = b'6oyZDr22E3ychjM%'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(data, AES.block_size)
    enc = cipher.encrypt(padded)
    return binascii.hexlify(enc).decode()

# -------------------------------------
# PROTOBUF FOR LIKE
# -------------------------------------
def create_like_proto(uid):
    msg = like_pb2.like()
    msg.uid = int(uid)
    msg.region = "BD"
    return msg.SerializeToString()

# -------------------------------------
# PROTOBUF FOR PROFILE FETCH
# -------------------------------------
def create_uid_proto(uid):
    msg = uid_generator_pb2.uid_generator()
    msg.krishna_ = int(uid)
    msg.teamXdarks = 1
    return msg.SerializeToString()

# -------------------------------------
# FETCH PROFILE (BEFORE/AFTER)
# -------------------------------------
def fetch_profile(uid, token):
    enc_uid = encrypt(create_uid_proto(uid))

    url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
    edata = bytes.fromhex(enc_uid)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    r = requests.post(url, data=edata, headers=headers, verify=False)
    binary = r.content

    try:
        obj = like_count_pb2.Info()
        obj.ParseFromString(binary)
        return MessageToDict(obj)
    except:
        return None

# -------------------------------------
# SEND SINGLE LIKE
# -------------------------------------
async def send_like(enc_uid, token):
    url = "https://clientbp.ggblueshark.com/LikeProfile"
    edata = bytes.fromhex(enc_uid)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=edata, headers=headers) as r:
            return r.status

# -------------------------------------
# SEND 100 LIKES
# -------------------------------------
async def send_100(uid, tokens):
    enc_uid = encrypt(create_like_proto(uid))

    tasks = []
    for i in range(100):
        token = tokens[i % len(tokens)]["token"]
        tasks.append(send_like(enc_uid, token))

    return await asyncio.gather(*tasks)

# -------------------------------------
# MAIN API
# -------------------------------------
@app.route("/like")
def like_api():
    uid = request.args.get("uid")
    srv = request.args.get("server_name", "").upper()

    if not uid or not srv:
        return jsonify({"error": "UID and server_name required"}), 400

    if srv != ALLOWED_SERVER:
        return jsonify({"error": "Only BD server allowed"}), 403

    tokens = load_bd_tokens()
    if not tokens:
        return jsonify({"error": "No BD tokens available"}), 500

    token = tokens[0]["token"]

    # BEFORE LIKE
    before = fetch_profile(uid, token)
    if not before:
        return jsonify({"error": "Failed to fetch before-like info"}), 500

    before_like = int(before["AccountInfo"].get("Likes", 0))

    # SEND LIKES
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_100(uid, tokens))
    except:
        return jsonify({"error": "Async system error"}), 500

    # AFTER LIKE
    after = fetch_profile(uid, token)
    if not after:
        return jsonify({"error": "Failed to fetch after-like info"}), 500

    after_like = int(after["AccountInfo"]["Likes"])
    name       = after["AccountInfo"].get("PlayerNickname", "Unknown")
    uid_final  = after["AccountInfo"].get("UID", uid)

    given = after_like - before_like

    return jsonify({
        "LikesGivenByAPI": given,
        "LikesafterCommand": after_like,
        "LikesbeforeCommand": before_like,
        "PlayerNickname": name,
        "UID": uid_final,
        "status": 1 if given > 0 else 2
    })


# -------------------------------------
# LOCAL RUN
# -------------------------------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
