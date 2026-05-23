from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import time
import secrets

# =========================
# 🚀 APP CONFIG
# =========================
app = Flask(__name__)
CORS(app)

DB_NAME = "licenses.db"

# =========================
# 🧱 DATABASE INIT
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            license_key TEXT PRIMARY KEY,
            hwid TEXT,
            expires INTEGER
        )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# 🔑 GENERATE LICENSE KEY
# =========================
def generate_license_key():
    return "LIC-" + secrets.token_hex(8).upper()

# =========================
# ➕ CREATE LICENSE
# =========================
@app.route("/create_license", methods=["POST"])
def create_license():

    data = request.json or {}

    days = int(data.get("days", 30))

    license_key = generate_license_key()

    expires = int(time.time()) + (days * 86400)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO licenses
        (license_key, hwid, expires)
        VALUES (?, ?, ?)
        """,
        (license_key, None, expires)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "license": license_key,
        "expires": expires,
        "days": days
    })

# =========================
# 🔐 CHECK LICENSE + HWID
# =========================
@app.route("/check", methods=["POST"])
def check_license():

    data = request.json or {}

    license_key = data.get("license")
    hwid = data.get("hwid")

    # ❌ données manquantes
    if not license_key or not hwid:
        return jsonify({
            "success": False,
            "status": "missing_data"
        }), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT hwid, expires
        FROM licenses
        WHERE license_key = ?
        """,
        (license_key,)
    )

    result = cursor.fetchone()

    # ❌ licence invalide
    if not result:
        conn.close()

        return jsonify({
            "success": False,
            "status": "invalid_license"
        }), 403

    stored_hwid, expires = result

    # ❌ licence expirée
    if int(time.time()) > expires:
        conn.close()

        return jsonify({
            "success": False,
            "status": "license_expired"
        }), 403

    # ✅ première activation
    if stored_hwid is None:

        cursor.execute(
            """
            UPDATE licenses
            SET hwid = ?
            WHERE license_key = ?
            """,
            (hwid, license_key)
        )

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "status": "activated"
        })

    # ❌ mauvais HWID
    if stored_hwid != hwid:
        conn.close()

        return jsonify({
            "success": False,
            "status": "hwid_mismatch"
        }), 403

    # ✅ licence valide
    conn.close()

    return jsonify({
        "success": True,
        "status": "valid"
    })

# =========================
# ❤️ HOME ROUTE
# =========================
@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "server": "TuneSoft License Server",
        "status": "online"
    })

# =========================
# 🚀 START SERVER
# =========================
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
