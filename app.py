import ipaddress
import os
import socket
import time

import paramiko
from flask import Flask, jsonify, render_template, request


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

DEFAULT_ROUTER_IP = os.getenv("ROUTER_IP", "192.168.40.129")
ROUTER_USERNAME = os.getenv("ROUTER_USERNAME", "admin")
ROUTER_PASSWORD = os.getenv("ROUTER_PASSWORD", "")
SSH_TIMEOUT = int(os.getenv("SSH_TIMEOUT", "10"))


def valid_ip(value: str) -> str:
    return str(ipaddress.ip_address(value.strip()))


def run_router_command(host: str, command: str) -> str:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=host,
            port=22,
            username=ROUTER_USERNAME,
            password=ROUTER_PASSWORD,
            timeout=SSH_TIMEOUT,
            banner_timeout=SSH_TIMEOUT,
            auth_timeout=SSH_TIMEOUT,
            look_for_keys=False,
            allow_agent=False,
        )
        channel = client.invoke_shell(width=200, height=1000)
        channel.settimeout(1.0)
        channel.send("terminal length 0\n")
        time.sleep(0.5)
        while channel.recv_ready():
            channel.recv(65535)

        channel.send(command + "\n")
        output = []
        deadline = time.monotonic() + SSH_TIMEOUT
        quiet_since = None
        while time.monotonic() < deadline:
            if channel.recv_ready():
                output.append(channel.recv(65535).decode("utf-8", errors="replace"))
                quiet_since = time.monotonic()
            elif quiet_since and time.monotonic() - quiet_since >= 0.8:
                break
            else:
                time.sleep(0.1)
        return "".join(output).strip()
    finally:
        client.close()


@app.get("/")
def index():
    return render_template("index.html", default_ip=DEFAULT_ROUTER_IP)


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/api/execute")
def execute():
    payload = request.get_json(silent=True) or {}
    command = str(payload.get("command", "")).strip()
    try:
        host = valid_ip(str(payload.get("ip", "")))
    except ValueError:
        return jsonify(error="IP address ไม่ถูกต้อง"), 400
    if not command or len(command) > 500:
        return jsonify(error="Command ต้องมีความยาว 1-500 ตัวอักษร"), 400
    if "\n" in command or "\r" in command:
        return jsonify(error="รองรับครั้งละหนึ่ง command เท่านั้น"), 400
    if not ROUTER_PASSWORD:
        return jsonify(error="Server ยังไม่ได้ตั้งค่า ROUTER_PASSWORD"), 500
    try:
        result = run_router_command(host, command)
        return jsonify(output=result or "(command completed with no output)")
    except (paramiko.SSHException, socket.error, TimeoutError) as exc:
        app.logger.warning("Router SSH failed for %s: %s", host, exc)
        return jsonify(error=f"SSH connection failed: {exc}"), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
