# RanchEye-02-Analysis: AI-Powered Ranch Monitoring

**AI ASSISTANT CONTEXT**: This is a standalone Python service that analyzes images stored in Supabase by the camera-ingestion service (rancheye-01). This service does NOT handle SpyPoint API calls, image downloads, or camera management - it ONLY analyzes existing images using AI vision models.

## 🎯 Purpose

RanchEye-02-Analysis monitors ranch conditions by analyzing trail camera images to detect:
- **Gate Status**: Is the gate open or closed?
- **Water Levels**: Are water troughs low?
- **Animal Detection**: What animals are present?
- **Fence Integrity**: Are there breaks in fencing?
- **Equipment Status**: Is equipment in the expected location?
- **Custom Conditions**: Any user-defined monitoring scenarios

## 🏗️ Architecture

This service operates independently from the camera ingestion service (rancheye-01), communicating only through the shared Supabase database.

### Data Flow
```
[SpyPoint Cameras] → [rancheye-01] → [Supabase Storage/DB] → [rancheye-02-analysis] → [Analysis Results]
                                            ↑                          ↓
                                            └──────────────────────────┘
```

### Database Interface

**READS FROM** (created by rancheye-01):
- `spypoint_images` table:
  - `image_id` (TEXT, primary key)
  - `camera_name` (TEXT)
  - `storage_path` (TEXT) - path in Supabase storage bucket
  - `metadata` (JSONB)
  - `downloaded_at` (TIMESTAMP)

**WRITES TO** (created by this service):
- `analysis_configs` - Analysis rules and AI model configurations
- `analysis_tasks` - Queue of pending analysis jobs
- `image_analysis_results` - AI analysis results and detections
- `analysis_alerts` - Triggered alerts based on detection thresholds

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Access to the same Supabase project as rancheye-01
- API keys for AI providers (OpenAI, Anthropic, and/or Google Gemini)

### Installation

```bash
# Clone this repository
git clone <your-repo-url>
cd rancheye-02-analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file:

```bash
# Supabase Configuration (same as rancheye-01)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# AI Provider API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# Analysis Configuration
ANALYSIS_INTERVAL_MINUTES=30
BATCH_SIZE=10
DEFAULT_AI_PROVIDER=openai  # or 'anthropic' or 'gemini'

# Alert Configuration
ALERT_WEBHOOK_URL=https://your-webhook-endpoint.com
ALERT_EMAIL=ranch-alerts@example.com
```

### Database Setup

Run the initialization script to create required tables:

```bash
python scripts/setup_database.py
```

Or manually create tables using the SQL in `database/schema.sql`.

### 🤖 AI-Powered Database Access (MCP)

This project is configured to work with Claude's MCP (Model Context Protocol) for direct database access. This means Claude can help you with:

- Creating and modifying database records
- Running complex queries
- Generating reports
- Debugging data issues

**See the MCP guides for details:**
- [`MCP_INTEGRATION_SUMMARY.md`](MCP_INTEGRATION_SUMMARY.md) - Quick overview of MCP setup
- [`CLAUDE_DESKTOP_VS_CODE.md`](CLAUDE_DESKTOP_VS_CODE.md) - **Important: Differences between Claude Desktop and Claude Code**
- [`MCP_DATABASE_GUIDE.md`](MCP_DATABASE_GUIDE.md) - Comprehensive guide to using MCP
- [`MCP_QUICK_REFERENCE.md`](MCP_QUICK_REFERENCE.md) - Quick CRUD operation examples
- [`MCP_PYTHON_PATTERNS.md`](MCP_PYTHON_PATTERNS.md) - Python code generation patterns
- [`PUPPETEER_MCP_GUIDE.md`](PUPPETEER_MCP_GUIDE.md) - Browser automation for UI development
- [`PUPPETEER_QUICK_START.md`](PUPPETEER_QUICK_START.md) - Quick reference for browser control
- [`MCP_TROUBLESHOOTING.md`](MCP_TROUBLESHOOTING.md) - Troubleshooting MCP issues

## 📊 Analysis Types

### Pre-configured Analyses

1. **Gate Detection**
   - Detects if gates are open/closed
   - Configurable per camera location
   - Alert threshold: Gate open > 30 minutes

2. **Water Level Monitoring**
   - Analyzes water trough levels
   - Categories: Full, Adequate, Low, Empty
   - Alert threshold: Low or Empty

3. **Animal Detection**
   - Identifies animals in frame
   - Tracks wildlife vs livestock
   - Optional species identification

4. **Equipment Monitoring**
   - Verifies equipment presence/position
   - Detects unusual conditions

### Custom Analysis

Define custom analyses in the `analysis_configs` table or via API:

```python
{
    "name": "Feed Bin Monitor",
    "camera_name": "Barn Camera 1",
    "analysis_type": "custom",
    "model_provider": "openai",
    "model_name": "gpt-4-vision",
    "prompt_template": "Analyze this image of a feed bin. Estimate the fill level as a percentage. Look for: 1) Visible feed level, 2) Any damage to the bin, 3) Signs of pest activity.",
    "threshold": 20,  # Alert when below 20%
    "active": true
}
```

## 🏃 Running the Service

### Manual Execution

Process pending images once:
```bash
python -m src.analyzer --once
```

### Continuous Operation

Run as a service with automatic queue processing:
```bash
python -m src.analyzer
```

### Docker Deployment

```bash
docker build -t rancheye-analysis .
docker run -d --env-file .env rancheye-analysis
```

### Railway Deployment

The service is configured for Railway deployment:

```bash
# Deploy to Railway
railway up

# View logs
railway logs
```

## 📈 Monitoring & Observability

### Logs

- Application logs: `analysis.log`
- Structured JSON logging for aggregation
- Log levels: DEBUG, INFO, WARNING, ERROR

### Metrics

Track via Supabase queries:

```sql
-- Analysis performance
SELECT 
    model_provider,
    analysis_type,
    AVG(processing_time_ms) as avg_time,
    COUNT(*) as total_analyses,
    SUM(CASE WHEN alert_triggered THEN 1 ELSE 0 END) as alerts_triggered
FROM image_analysis_results
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY model_provider, analysis_type;

-- Pending tasks
SELECT 
    status,
    COUNT(*) as count
FROM analysis_tasks
GROUP BY status;
```

### Health Checks

- `GET /health` - Basic liveness check
- `GET /health/ready` - Readiness probe (checks DB and AI provider connections)
- `GET /metrics` - Prometheus-compatible metrics

## 🛠️ Development

### Project Structure

```
rancheye-02-analysis/
├── src/
│   ├── analyzer.py              # Main entry point
│   ├── ai_providers/           # AI integration modules
│   │   ├── base.py            # Abstract base class
│   │   ├── openai_vision.py   # OpenAI GPT-4 Vision
│   │   ├── anthropic_vision.py # Claude Vision
│   │   └── gemini_vision.py   # Google Gemini
│   ├── processors/             # Analysis processors
│   │   ├── gate_detector.py
│   │   ├── water_monitor.py
│   │   └── custom_analyzer.py
│   ├── database/               # Database operations
│   │   ├── models.py
│   │   ├── queries.py
│   │   └── connection.py
│   ├── alerts/                 # Alert system
│   │   ├── webhook.py
│   │   ├── email.py
│   │   └── manager.py
│   └── utils/                  # Utilities
│       ├── config.py
│       └── logging.py
├── scripts/
│   ├── setup_database.py       # DB initialization
│   ├── test_analysis.py        # Test single image
│   └── backfill.py            # Analyze historical images
├── tests/
│   ├── test_providers.py
│   ├── test_processors.py
│   └── test_integration.py
├── database/
│   └── schema.sql             # Database schema
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
├── Dockerfile                # Container definition
├── railway.json              # Railway config
└── README.md                 # This file
```

### Adding New Analysis Types

1. Create processor in `src/processors/`:
```python
from .base import BaseProcessor

class FenceIntegrityProcessor(BaseProcessor):
    def analyze(self, image_url: str, config: dict) -> dict:
        # Implementation
        pass
```

2. Register in `src/analyzer.py`
3. Add configuration to database
4. Test with sample images

### Testing

```bash
# Run all tests
pytest

# Test specific analysis
python scripts/test_analysis.py --image-id <id> --analysis-type gate_detection

# Test with local image
python scripts/test_analysis.py --local-image path/to/image.jpg
```

## 🔧 Configuration

### Analysis Configurations

Managed through the `analysis_configs` table:

| Field | Description | Example |
|-------|-------------|---------|
| name | Human-readable name | "North Gate Monitor" |
| camera_name | Must match rancheye-01 | "North Gate Cam" |
| analysis_type | Type of analysis | "gate_detection" |
| model_provider | AI provider | "openai" |
| model_name | Specific model | "gpt-4-vision" |
| prompt_template | Analysis instructions | "Detect if gate is open..." |
| threshold | Alert threshold | 0.8 |
| active | Enable/disable | true |

### Performance Tuning

```bash
# Process more images in parallel
BATCH_SIZE=20

# Reduce AI costs with caching
ENABLE_CACHE=true
CACHE_TTL_HOURS=24

# Use cheaper models for simple tasks
SIMPLE_TASK_MODEL=gpt-4o-mini
```

## 🚨 Alerts & Notifications

### Alert Types

1. **Immediate Alerts**: Critical conditions (open gates, empty water)
2. **Digest Alerts**: Daily summaries of non-critical findings
3. **Trend Alerts**: Patterns over time (decreasing water levels)

### Webhook Format

```json
{
    "alert_type": "immediate",
    "camera_name": "North Gate Cam",
    "analysis_type": "gate_detection",
    "result": {
        "gate_open": true,
        "confidence": 0.95,
        "duration_open": "45 minutes"
    },
    "image_url": "https://...",
    "timestamp": "2025-06-29T12:34:56Z"
}
```

## 🔒 Security

- All images remain in private Supabase storage
- AI providers receive temporary signed URLs
- No image data is stored by AI providers
- Results contain no PII
- Audit log of all analyses

## 📈 Cost Management

### Strategies

1. **Model Selection**: Use appropriate models for complexity
2. **Caching**: Cache results for identical conditions
3. **Batch Processing**: Group similar analyses
4. **Time-based**: Analyze during off-peak hours
5. **Motion Detection**: Only analyze when changes detected

### Monitoring Costs

```sql
-- Daily cost estimate
SELECT 
    DATE(created_at) as date,
    model_provider,
    model_name,
    COUNT(*) as analyses,
    COUNT(*) * 0.01 as estimated_cost -- Adjust per provider
FROM image_analysis_results
GROUP BY DATE(created_at), model_provider, model_name
ORDER BY date DESC;
```

## 🤝 Integration

### With rancheye-01

- Shared Supabase instance
- Reads from `spypoint_images` table
- Independent deployment and scaling

### With External Systems

- Webhook notifications
- REST API endpoints
- Prometheus metrics
- Database views for BI tools

## 📜 License

MIT License - See LICENSE file

## 🆘 Support

### Troubleshooting

1. **"No pending tasks"**
   - Check `analysis_configs` has active configurations
   - Verify new images exist in `spypoint_images`
   - Check task creation logs

2. **"AI provider error"**
   - Verify API keys are valid
   - Check rate limits
   - Review provider-specific errors in logs

3. **"Cannot access images"**
   - Verify Supabase credentials
   - Check storage bucket permissions
   - Ensure signed URLs are working

### Debug Mode

```bash
# Enable verbose logging
LOG_LEVEL=DEBUG python -m src.analyzer

# Test single image
python scripts/test_analysis.py --debug --image-id <id>
```

---

**RanchEye-02-Analysis** - Intelligence for your ranch monitoring system 🤖📷