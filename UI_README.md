# RanchEye Analysis - Web UI Guide

## 🚀 Quick Start

### 1. Start the Web Server

```bash
python web_server.py
```

The server will start on port 8080 by default.

### 2. Access the Dashboard

Open your browser and go to:
- **Dashboard**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

## 📊 Dashboard Features

### Real-time Monitoring
- **Live Stats**: Analyses today, weekly totals, active alerts, pending tasks, and daily costs
- **WebSocket Updates**: Stats refresh automatically every 10 seconds
- **Recent Images**: View the latest camera captures from your ranch

### Analysis Results
- View AI analysis results with confidence scores
- See which model was used (OpenAI, Gemini)
- Highlighted alerts for critical conditions

### Active Alerts
- Real-time alerts for:
  - Open gates
  - Low water levels
  - Empty feed bins
  - Unusual animal activity
- One-click acknowledgment

### Test Analysis
- Upload your own images for testing
- Select analysis type:
  - Gate Detection
  - Water Level
  - Feed Bin Status
  - Animal Detection
- See results immediately

## 🔧 API Endpoints

### Core Endpoints
- `GET /api/configs` - List analysis configurations
- `GET /api/images/recent` - Get recent images
- `GET /api/analysis/results` - Get analysis results
- `POST /api/analysis/analyze` - Start analysis for an image
- `GET /api/alerts` - Get active alerts
- `GET /api/stats/summary` - Get system statistics

### Upload & Test
- `POST /api/upload/analyze` - Upload and analyze an image directly

## 🎯 Testing the UI

### Method 1: Use Existing Images
1. Click "Analyze" on any image in the Recent Images table
2. Wait for results to appear in the Analysis Results section

### Method 2: Upload Test Image
1. Click "Choose File" in the Test Analysis section
2. Select a ranch camera image (gates, water troughs, etc.)
3. Choose the analysis type
4. Click "Upload & Analyze"
5. View results below

### Method 3: Simulate Alerts
1. Upload an image of an open gate
2. Select "Gate Detection" as analysis type
3. The system should detect the open gate and create an alert
4. Check the Active Alerts section

## 🐛 Troubleshooting

### WebSocket Not Connecting
- Check browser console for errors
- Ensure the server is running on the correct port
- Try refreshing the page

### No Images Showing
- Verify Supabase connection in .env
- Check that the `spypoint_images` table has data
- Look at server logs for errors

### Analysis Not Working
- Verify API keys are set in .env:
  - OPENAI_API_KEY
  - GEMINI_API_KEY
- Check server logs for API errors

## 🖼️ Sample Test Images

For testing, you can use images of:
- **Gates**: Open/closed ranch gates
- **Water**: Troughs at various fill levels
- **Feed Bins**: Full/empty feeders
- **Animals**: Cattle, horses, wildlife

The AI will analyze these and provide appropriate alerts.

## 📱 Mobile Access

The dashboard is mobile-responsive. Access it from your phone or tablet using your computer's IP address:
```
http://YOUR_COMPUTER_IP:8080
```

## 🔒 Security Note

This dashboard is meant for local testing. For production:
- Add authentication
- Use HTTPS
- Restrict CORS origins
- Implement proper access controls