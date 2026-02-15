# AI Logger

A voice-enabled web application to capture daily ideas and schedule events, powered by AI.

## Features
- **Voice Input:** Record your thoughts or events directly from the browser.
- **AI Processing:** Automatically transcribes and structures your data.
  - **Events:** Extracts title, start time, and end time.
  - **Ideas:** Summarizes content and creates a concise title.
- **Notion Integration:** Saves directly to your Notion "Agenda" and "Journal" databases.
- **Review Mode:** Edit the AI-generated draft before saving.

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration:**
   Ensure your `.env` file contains:
   - `SUPER_MIND_API_KEY`
   - `NOTION_API_KEY`
   - `AGENDA_DATABASE_ID`
   - `JOURNAL_DATABASE_ID`

3. **Run the Server:**
   ```bash
   ./start.sh
   ```
   Or manually:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access:**
   Open your browser at `http://localhost:8000`.

## Security & Remote Access

### 1. Basic Authentication
The application is protected by a username and password. Add these to your `.env` file:
```bash
AUTH_USERNAME=your_username
AUTH_PASSWORD=your_password
```

### 2. Mobile Access (Tailscale)
To access this app from your phone securely:
1.  Install **Tailscale** on both your PC (WSL) and Phone.
2.  Run `sudo tailscale up --hostname=ai-logger` in your WSL terminal.
3.  On your phone, visit: `http://ai-logger:8000`.

### 3. Fixing Microphone Permissions
Browsers block microphone access on non-https sites (except localhost). To fix this on your phone:
1.  Open **Edge** or **Chrome** on your phone.
2.  Go to `edge://flags` or `chrome://flags`.
3.  Search for **"Insecure origins treated as secure"**.
4.  Enable it and add your URL (e.g., `http://ai-logger:8000`).
5.  Relaunch the browser.

## Usage
1. Select "Add Event" or "Record Idea".
2. Click and hold the microphone button to record.
3. Release to stop recording and wait for AI processing.
4. Review the drafted entry in the modal.
5. Click "Confirm & Save" to push to Notion.
