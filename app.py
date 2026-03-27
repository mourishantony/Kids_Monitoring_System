from flask import Flask, render_template, jsonify, Response
import time
import random

app = Flask(__name__)

# Mock database
KIDS_DB = {
    "KID001": {"id": "KID001", "name": "Aryan Sharma", "age": 8, "status": "Safe", "last_seen": "11:45 AM", "entry": "09:00 AM", "image": "https://i.pravatar.cc/150?u=KID001"},
    "KID002": {"id": "KID002", "name": "Sanya Iyer", "age": 6, "status": "Safe", "last_seen": "11:50 AM", "entry": "09:15 AM", "image": "https://i.pravatar.cc/150?u=KID002"},
    "KID003": {"id": "KID003", "name": "Kabir Ali", "age": 10, "status": "Alert", "last_seen": "11:55 AM", "entry": "08:45 AM", "image": "https://i.pravatar.cc/150?u=KID003"},
    "KID004": {"id": "KID004", "name": "Ananya Reddy", "age": 7, "status": "Safe", "last_seen": "11:58 AM", "entry": "09:30 AM", "image": "https://i.pravatar.cc/150?u=KID004"},
}

ALERTS = [
    {"id": 1, "type": "warning", "message": "Unknown person detected near Gate A", "time": "11:55 AM", "critical": False},
    {"id": 2, "type": "danger", "message": "Child (Kabir Ali) exited safe zone", "time": "11:58 AM", "critical": True},
    {"id": 3, "type": "info", "message": "New kid entry: Ananya Reddy", "time": "09:30 AM", "critical": False},
]

# --- PAGES ---

@app.route('/')
def dashboard():
    return render_template('dashboard.html', kids_count=len(KIDS_DB), alerts_count=len(ALERTS))

@app.route('/live')
def live_monitoring():
    return render_template('live.html')

@app.route('/alerts')
def alerts_page():
    return render_template('alerts.html', alerts=ALERTS)

@app.route('/kid/<kid_id>')
def kid_details(kid_id):
    kid = KIDS_DB.get(kid_id)
    if not kid:
        return "Kid not found", 404
    return render_template('kid.html', kid=kid)

# --- API ENDPOINTS ---

@app.route('/api/kids')
def get_kids():
    return jsonify(list(KIDS_DB.values()))

@app.route('/api/alerts')
def get_alerts():
    return jsonify(ALERTS)

@app.route('/api/kid/<kid_id>')
def get_kid(kid_id):
    return jsonify(KIDS_DB.get(kid_id, {}))

@app.route('/video_feed')
def video_feed():
    # Placeholder for a video feed stream
    # In a real app, this would be a generator function with MJPEG
    return Response(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + b'',
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
