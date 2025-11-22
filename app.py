# FIXED VERSION – ONLY BD ALLOWED
# by ChatGPT

from flask import Flask, request, jsonify
import asyncio
import json, random
import requests
import aiohttp
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf.json_format import MessageToJson, MessageToDict
import binascii

import like_pb2
import like_count_pb2
import uid_generator_pb2

app = Flask(__name__)

# ==============================
#  ONLY BD SERVER ALLOWED
# ==============================
ALLOWED_SERVER = "BD"

# ==============================
# TOKEN LOADER (BD ONLY)
# ==============================
def load_bd_tokens():
    try:
        with open("token_bd.json", "r") as f:
            tokens = json.load(f)
        if not tokens:
            return None
        return tokens
    except:
        return None


# ==============================
# ENCRYPT FUNCTION
# ==============================
def encrypt_message(data):
    key = b'Yg&tc%DEuh6%Zc^8'
    iv  = b'6oyZDr22E3ychjM%'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(data, AES.block_size)
    encrypted = cipher.encrypt(padded)
    return binascii.hexlify(encrypted).decode()


# ==============================
# CREATE LIKE PROTOBUF
# ==============================
def create_like_proto(uid):
    msg = like_pb2.like()
    msg.uid = int(uid)
    msg.region = "BD"
    return msg.SerializeToString()


# ==============================
# UID GENERATOR PROTOBUF
# ==============================
def create_uid_proto(uid):
    msg = uid_generator_pb2.uid_generator()
    msg.krishna_ = int(uid)
    msg.teamXdarks = 1
    return msg.SerializeToString()


# ==============================
# GET PLAYER INFO (Before / After)
# ==============================
def get_player_info(uid, token):
    encrypted_uid = encrypt_message(create_uid_proto(uid))
    url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"

    edata = bytes.fromhex(encrypted_uid)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "FF-API",
    }

    resp = requests.post(url, data=edata, headers=headers, verify=False)
    binary = resp.content

    try:
        obj = like_count_pb2.Info()
        obj.ParseFromString(binary)
        return MessageToDict(obj)
    except:
        return None


# ==============================
# SEND LIKE REQUEST
# ==============================
async def send_like_request(encrypted_uid, token):
    url = "https://clientbp.ggblueshark.com/LikeProfile"
    edata = bytes.fromhex(encrypted_uid)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "FF-API"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=edata, headers=headers) as r:
            return r.status


async def send_multiple(uid, tokens):
    encrypted_uid = encrypt_message(create_like_proto(uid))
    
    tasks = []
    for i in range(100):
        token = tokens[i % len(tokens)]["token"]
        tasks.append(send_like_request(encrypted_uid, token))

    return await asyncio.gather(*tasks)


# ==============================
# MAIN API ROUTE
# ==============================
@app.route("/like")
def like_api():
    uid = request.args.get("uid")
    server = request.args.get("server_name", "").upper()

    if not uid or not server:
        return jsonify({"error": "UID and server_name are required"}), 400

    # ----- ONLY BD ALLOWED -----
    if server != ALLOWED_SERVER:
        return jsonify({"error": "Only BD server allowed"}), 403

    tokens = load_bd_tokens()
    if not tokens:
        return jsonify({"error": "No BD tokens available"}), 500

    token = tokens[0]["token"]

    # BEFORE LIKE
    before = get_player_info(uid, token)
    if not before:
        return jsonify({"error": "Failed to fetch before-like info"}), 500

    before_likes = int(before["AccountInfo"].get("Likes", 0))

    # SEND 100 LIKE REQUESTS
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_multiple(uid, tokens))
    except:
        return jsonify({"error": "Async error"}), 500

    # AFTER LIKE
    after = get_player_info(uid, token)
    if not after:
        return jsonify({"error": "Failed to fetch after-like info"}), 500

    after_likes = int(after["AccountInfo"].get("Likes", 0))
    name = after["AccountInfo"].get("PlayerNickname", "Unknown")
    uid_val = after["AccountInfo"].get("UID", uid)

    given = after_likes - before_likes

    result = {
        "LikesGivenByAPI": given,
        "LikesafterCommand": after_likes,
        "LikesbeforeCommand": before_likes,
        "PlayerNickname": name,
        "UID": uid_val,
        "status": 1 if given > 0 else 2
    }

    return jsonify(result)


# ==============================
# RUN (LOCAL)
# ==============================
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
