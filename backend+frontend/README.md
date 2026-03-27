# 📹 Kids Monitoring System - Frontend UI

A premium, modern, and real-time frontend dashboard for building a **Kids Monitoring System** in college campuses. This system is designed to integrate with AI-based face recognition and tracking backends (Python + MongoDB + InsightFace).

![Dashboard Preview](https://img.icons8.com/color/144/000000/baby-grow.png)

## 🌟 Key Features

*   **📊 Live Dashboard**: Real-time stats, system health, and summary of currently detected kids.
*   **🎥 Smart Live Feed**: Full-screen CCTV monitoring with simulated AI bounding boxes and tracking labels.
*   **🧒 Precise Kid Profiles**: Individual profiles showing age, status, entry/last-seen timestamps, and a movement history timeline.
*   **🔔 Security Alerts**: Color-coded alerts for unidentified persons or kids exiting safe zones.
*   **🎨 Premium UI/UX**: Soft colors, modern typography (Inter/Outfit), and responsive design (Desktop + Tablet).
*   **⚙️ System Status**: Dynamic "Active" indicators and notification popups for critical events.

---

## 🏗️ Technology Stack

- **Backend**: Python (Flask)
- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript (Vanilla)
- **Templating**: Jinja2
- **Icons**: FontAwesome 6.4.0
- **Typography**: Google Fonts API (Inter & Outfit)

---

## 📂 Project Structure

```text
/Kids_Monitoring_System
├── app.py              # Main Flask server with mock API
├── static/
│   ├── css/
│   │   └── styles.css  # Modern UI styling
│   └── js/
│       └── script.js   # Global UI interactions
├── templates/
│   ├── base.html       # Layout and sidebar
│   ├── dashboard.html  # Main summary page
│   ├── live.html       # Video monitoring page
│   ├── alerts.html     # Security logs
│   └── kid.html        # Detailed profile page
├── venv/               # Virtual Environment (Generated)
└── requirements.txt    # Project dependencies
```

---

## 🚀 Getting Started

### 1. Requirements
*   Python 3.8+
*   Flask

### 2. Setup
Clone or copy the files, then create a virtual environment and install dependencies:

```powershell
# Create venv
python -m venv venv

# Activate venv (Windows)
.\venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Run the App
```powershell
python app.py
```
Open `http://127.0.0.1:5000` in your web browser.

---

## 🛠️ Integration Points

- **Live Stream**: Update `<img src="/video_feed">` in `dashboard.html` and `live.html` with your real MJPEG stream endpoint.
- **Backend API**: The system correctly uses `fetch()` to call `/api/kids`. Replace the mock endpoints in `app.py` with calls to your MongoDB/InsightFace backend.

---

## 💖 Design Credits
Built with a "Kid-friendly but Professional" aesthetic using modern web standards.
