# Adding Progress Tracking - Quick Fix

## The Problem
Video generation takes 3-5 minutes but the UI just hangs with no feedback.

## The Solution
I've created `app_with_progress.py` which:
- Runs long tasks in background threads
- Exposes `/api/progress` endpoint
- Updates progress state in real-time

## How to Use

### Step 1: Stop current server
In your terminal where `python app.py` is running:
- Press `Ctrl+C`

### Step 2: Start new server
```bash
cd /Users/shadman/Documents/Vibe\ Coding/ai-cli-sandbox/karaoke-maker
python app_with_progress.py
```

### Step 3: Test it
1. Open http://localhost:5001
2. Try generating your karaoke video
3. Open browser console (F12) and run:
   ```javascript
   // Poll for progress
   setInterval(() => {
       fetch('/api/progress')
           .then(r => r.json())
           .then(data => console.log(data));
   }, 1000);
   ```

You should see progress updates in the console!

## What You'll See
```javascript
{
    "task": "generate",
    "status": "running",  // or "complete", "error"
    "progress": 30,        // 0-100
    "message": "Creating lyric segments...",
    "error": null,
    "result": null
}
```

## Next Step: Update the UI
To show a nice progress bar in the UI, I need to modify `templates/app.html`.
Should I do that now, or do you want to test the backend progress first?

## Quick Test Script
Save this as `test_progress.html` and open it while generation is running:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Progress Monitor</title>
    <style>
        body { font-family: monospace; padding: 20px; background: #1a1a1a; color: #0f0; }
        .progress { background: #333; height: 40px; margin: 20px 0; border: 2px solid #0f0; }
        .bar { background: #0f0; height: 100%; transition: width 0.3s; }
    </style>
</head>
<body>
    <h1>🎤 Karaoke Maker - Progress Monitor</h1>
    <div id="status"></div>
    <div class="progress">
        <div class="bar" id="progressBar"></div>
    </div>
    <pre id="log"></pre>

    <script>
        setInterval(async () => {
            const res = await fetch('http://localhost:5001/api/progress');
            const data = await res.json();

            document.getElementById('status').textContent =
                `Task: ${data.task || 'idle'} | Status: ${data.status} | ${data.progress}%`;
            document.getElementById('progressBar').style.width = data.progress + '%';
            document.getElementById('log').textContent =
                JSON.stringify(data, null, 2);
        }, 500);
    </script>
</body>
</html>
```
