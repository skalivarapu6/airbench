# AirBench Quick Start Guide

Get your experiment tracker running in 5 minutes!

## Prerequisites Check

```bash
# Check Python version (need 3.9+)
python --version

# Check Node.js version (need 18+)
node --version

# Check PostgreSQL
psql --version
```

## 1. Database Setup (2 minutes)

```bash
# Create database
createdb airbench

# Test connection
psql airbench -c "SELECT version();"
```

## 2. Backend Setup (1 minute)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start backend server
cd backend
uvicorn main:app --reload
```

✅ Backend should be running at http://localhost:8000

## 3. Frontend Setup (1 minute)

```bash
# In a new terminal
cd frontend

# Install dependencies (if not already done)
npm install

# Start frontend
npm run dev
```

✅ Frontend should be running at http://localhost:5173

## 4. Test the Application (1 minute)

### Create a test dataset:

1. Open http://localhost:5173
2. Go to "Datasets" page
3. Click "+ New Dataset"
4. Fill in:
   - **Name**: `ml-basics`
   - **Description**: `Sample ML Q&A dataset`
   - **File Path**: `/absolute/path/to/sample_dataset.json`
     (Use the full path to the `sample_dataset.json` file in the project root)
5. Click "Create Dataset"

### Create a test experiment:

1. Go to "Experiments" page
2. Click "+ New Experiment"
3. Fill in:
   - **Name**: `test-experiment-1`
   - **Base Model**: `gpt2-small`
   - **Dataset**: Select `ml-basics`
   - **Compute Provider**: `local`
   - Keep default hyperparameters
4. Click "Create Experiment"

### Launch and monitor:

1. Click on the experiment you just created
2. Click "Launch Experiment"
3. Watch real-time updates:
   - Status changes from "queued" → "running" → "completed"
   - Live logs appear
   - Metrics chart updates as training progresses

## Troubleshooting

### Backend won't start

**Error: "database 'airbench' does not exist"**
```bash
createdb airbench
```

**Error: "ModuleNotFoundError"**
```bash
pip install -r requirements.txt
```

### Frontend won't start

**Error: "Cannot find module"**
```bash
cd frontend
npm install
```

**Error: "Failed to fetch"**
- Make sure backend is running on port 8000
- Check `.env` file in `frontend/` has `VITE_API_URL=http://localhost:8000`

### Dataset creation fails

**Error: "File not found"**
- Use absolute path, not relative path
- Example: `/Users/yourname/projects/airbench-llm-oneshot/sample_dataset.json`

### Experiment won't launch

**Error: "Failed to launch"**
- For local provider, make sure `example_train.py` is in the backend directory
- Check backend logs for detailed error messages

## Next Steps

### Try Different Compute Providers

To use RunPod, Lambda Labs, or Modal:

1. Get API credentials from the provider
2. When launching experiment, configure provider settings
3. See README.md for detailed provider configuration

### Create Your Own Training Script

1. Copy `backend/example_train.py` as a template
2. Replace the simulation code with actual model training
3. Use the `ExperimentLogger` class to log metrics
4. Update provider config to point to your script

### Monitor Multiple Experiments

1. Create several experiments with different hyperparameters
2. Launch them all
3. Compare metrics on the experiments list page
4. Click into each for detailed analysis

## API Documentation

Once backend is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Support

- Check README.md for detailed documentation
- Review backend logs in terminal where you ran `uvicorn`
- Check browser console for frontend errors (F12 → Console tab)

---

**Congratulations! 🎉** You now have a fully functional LLM experiment tracker!
