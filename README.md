# AirBench - LLM Fine-Tuning Experiment Tracker

A full-stack application for orchestrating, launching, and tracking LLM fine-tuning experiments across multiple compute providers.

## Features

- **Experiment Management**: Create, track, and manage fine-tuning experiments
- **Real-Time Updates**: WebSocket-powered live status updates and log streaming
- **Multi-Provider Support**: Run experiments on Local, RunPod, Lambda Labs, or Modal
- **Dataset Management**: Upload and manage training datasets
- **Metrics Visualization**: Interactive Plotly.js charts for training metrics
- **Hyperparameter Tracking**: Configure and track hyperparameters per experiment

## Tech Stack

### Backend
- FastAPI (Python web framework)
- PostgreSQL (Database)
- SQLAlchemy (ORM)
- WebSockets (Real-time communication)

### Frontend
- React 18 + TypeScript
- Vite (Build tool)
- React Router (Navigation)
- Plotly.js (Metrics visualization)
- Axios (HTTP client)

## Architecture

```
backend/
├── main.py                 # FastAPI app & API endpoints
├── models.py              # SQLAlchemy database models
├── schemas.py             # Pydantic request/response schemas
├── database.py            # Database connection
├── orchestrator.py        # Experiment orchestration & WebSocket manager
└── providers/             # Compute provider integrations
    ├── base.py           # Abstract base provider
    ├── local.py          # Local execution
    ├── runpod.py         # RunPod integration
    ├── lambda_labs.py    # Lambda Labs integration
    └── modal_provider.py # Modal integration

frontend/
├── src/
│   ├── pages/            # Page components
│   ├── components/       # Reusable components
│   ├── api.ts            # Backend API client
│   └── types.ts          # TypeScript type definitions
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup

1. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database:**
   ```bash
   createdb airbench
   ```

4. **Update database credentials** (if needed) in `backend/database.py`:
   ```python
   DATABASE_URL = "postgresql://your_user:your_password@localhost:5432/airbench"
   ```

5. **Run the backend:**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   API docs at `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure API URL** (already set in `.env`):
   ```
   VITE_API_URL=http://localhost:8000
   ```

4. **Run the development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

## Usage Guide

### 1. Create a Dataset

1. Go to the "Datasets" page
2. Click "+ New Dataset"
3. Provide:
   - Dataset name
   - Description
   - File path (absolute path to .json or .csv file on the server)
4. Click "Create Dataset"

**Example dataset file (`data.json`):**
```json
[
  {"instruction": "What is AI?", "output": "AI stands for Artificial Intelligence..."},
  {"instruction": "Explain ML", "output": "Machine Learning is..."}
]
```

### 2. Create an Experiment

1. Go to "Experiments" page
2. Click "+ New Experiment"
3. Fill in:
   - Experiment name
   - Base model (e.g., `meta-llama/Llama-2-7b-hf`)
   - Dataset (select from dropdown)
   - Compute provider (Local, RunPod, Lambda Labs, Modal)
   - Hyperparameters (learning_rate, num_epochs, batch_size, etc.)
4. Click "Create Experiment"

### 3. Launch an Experiment

1. Click on an experiment from the list
2. Review the configuration
3. Click "Launch Experiment"
4. Monitor real-time logs and status updates
5. View metrics as they're logged

### 4. Monitor Progress

- **Status**: Shows current state (queued, running, completed, failed, cancelled)
- **Logs**: Real-time log streaming during execution
- **Metrics**: Interactive charts showing training/validation metrics
- **Hyperparameters**: View all configured hyperparameters

## Compute Provider Configuration

### Local Provider

Runs experiments on the same machine or SSH-accessible servers.

```python
# No additional config needed for local machine
# For SSH:
provider_config = {
    "ssh_host": "gpu-server.example.com",
    "ssh_user": "ubuntu",
    "working_dir": "/home/ubuntu/experiments",
    "python_path": "python"
}
```

### RunPod Provider

**Setup:**
1. Get API key from [RunPod](https://runpod.io)
2. Configure when launching experiment:
   ```python
   provider_config = {
       "api_key": "your_runpod_api_key",
       "gpu_type": "NVIDIA A100",
       "template_id": "optional_template_id"
   }
   ```

### Lambda Labs Provider

**Setup:**
1. Get API key from [Lambda Labs](https://lambdalabs.com)
2. Configure:
   ```python
   provider_config = {
       "api_key": "your_lambda_api_key",
       "instance_type": "gpu_1x_a100",
       "ssh_key_name": "your_ssh_key"
   }
   ```

### Modal Provider

**Setup:**
1. Get token from [Modal](https://modal.com)
2. Configure:
   ```python
   provider_config = {
       "token_id": "your_modal_token_id",
       "token_secret": "your_modal_token_secret",
       "gpu": "a100"
   }
   ```

## API Endpoints

### Experiments
- `GET /experiments` - List all experiments
- `GET /experiments/{id}` - Get experiment details
- `POST /new_experiment` - Create new experiment
- `PUT /experiments/{id}` - Update experiment
- `DELETE /experiments/{id}` - Delete experiment
- `POST /experiments/{id}/launch` - Launch experiment
- `POST /experiments/{id}/cancel` - Cancel running experiment

### Datasets
- `GET /datasets` - List all datasets
- `POST /new_dataset` - Create dataset

### Metrics
- `GET /experiments/{id}/metrics` - Get experiment metrics
- `POST /experiments/{id}/metrics` - Log a metric

### WebSocket
- `WS /ws/{experiment_id}` - Real-time updates for experiment

## Development

### Backend Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run with auto-reload
cd backend
uvicorn main:app --reload --port 8000
```

### Frontend Development

```bash
# Install dependencies
npm install

# Run dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Current MVP Status

✅ **Implemented:**
- Full CRUD for experiments and datasets
- WebSocket real-time updates
- Compute provider abstraction layer
- Local provider (fully functional)
- RunPod, Lambda Labs, Modal providers (template/structure ready)
- React frontend with routing
- Experiments list with status indicators
- Experiment detail page with Plotly charts
- Dataset management UI
- Real-time log streaming
- Metrics visualization

🚧 **Next Steps for Production:**
1. Complete compute provider API integrations (RunPod, Lambda, Modal SDKs)
2. Add authentication/authorization
3. Implement file upload for datasets (currently requires file path)
4. Add pagination for large lists
5. Add filtering and search
6. Error handling improvements
7. Add tests (backend and frontend)
8. Deploy to cloud infrastructure

## Contributing

This is currently an MVP. To extend functionality:

1. **Add a new compute provider:**
   - Create a new file in `backend/providers/`
   - Inherit from `BaseComputeProvider`
   - Implement all abstract methods
   - Add to `providers/__init__.py`

2. **Add new metrics:**
   - POST to `/experiments/{id}/metrics` with metric data
   - Frontend will automatically visualize new metrics

## License

MIT

## Support

For issues or questions, please open an issue on GitHub.
