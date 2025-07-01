# Developer Notes for RanchEye-02-Analysis

## AI Agent Context

**IMPORTANT**: This service is completely separate from rancheye-01. When working on this codebase:

1. **DO NOT** implement any SpyPoint API integration
2. **DO NOT** download images from SpyPoint
3. **DO NOT** manage camera settings or credentials
4. **ONLY** analyze images that already exist in Supabase

## Architecture Principles

### Separation of Concerns
- **rancheye-01**: Handles all camera/image ingestion
- **rancheye-02-analysis**: Handles all AI analysis
- **Communication**: Only through Supabase database

### Database Interface
```
rancheye-01 writes to:
  └── spypoint_images (we READ this)
  └── spypoint_telemetry (we ignore this)

rancheye-02-analysis writes to:
  └── analysis_configs
  └── analysis_tasks  
  └── image_analysis_results
  └── analysis_alerts
  └── analysis_cache
  └── analysis_costs
```

## Development Workflow

### 1. Setting Up Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Initialize database
python scripts/setup_database.py
```

### 2. Testing Analysis Locally

```bash
# Test with a specific image from the database
python scripts/test_analysis.py --image-id "abc123"

# Test with a local image file
python scripts/test_analysis.py --local-image /path/to/test.jpg --analysis-type gate_detection
```

### 3. Running the Service

```bash
# Process once and exit
python -m src.analyzer --once

# Run continuously
python -m src.analyzer

# Run with debug logging
LOG_LEVEL=DEBUG python -m src.analyzer
```

## Key Implementation Areas

### 1. AI Providers (`src/ai_providers/`)
Each provider should implement the base interface:
```python
class BaseAnalyzer(ABC):
    @abstractmethod
    async def analyze_image(self, image_url: str, prompt: str) -> dict:
        pass
```

### 2. Analysis Processors (`src/processors/`)
Specific analysis logic for different detection types:
- `gate_detector.py` - Gate open/closed detection
- `water_monitor.py` - Water level analysis
- `animal_identifier.py` - Animal detection and classification
- `custom_analyzer.py` - User-defined analysis

### 3. Task Processing Flow
```
1. Fetch pending tasks from analysis_tasks
2. Get image URL from spypoint_images
3. Generate signed URL for image access
4. Send to appropriate AI provider
5. Process and structure the response
6. Save to image_analysis_results
7. Check if alert should be triggered
8. Update task status
```

## Cost Optimization Strategies

1. **Caching**: Check `analysis_cache` before calling AI
2. **Model Selection**: Use cheaper models for simple tasks
3. **Batch Processing**: Group similar analyses
4. **Image Optimization**: Resize images if model allows
5. **Prompt Engineering**: Concise prompts use fewer tokens

## Testing Guidelines

### Unit Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_providers.py

# Run with coverage
pytest --cov=src
```

### Integration Tests
```bash
# Test database operations
pytest tests/test_database_integration.py

# Test AI provider integrations (uses real API)
INTEGRATION_TEST=true pytest tests/test_ai_integration.py
```

## Deployment Notes

### Railway Deployment
```bash
# Deploy to Railway
railway up

# Check logs
railway logs

# Set environment variables
railway variables set KEY=value
```

### Docker Deployment
```bash
# Build image
docker build -t rancheye-analysis .

# Run locally
docker run --env-file .env rancheye-analysis
```

## Common Issues and Solutions

### Issue: "No tasks found"
- Check that analysis_configs has active configurations
- Verify new images exist in spypoint_images
- Check logs for task creation errors

### Issue: "AI provider rate limit"
- Implement exponential backoff
- Use multiple API keys
- Consider caching more aggressively

### Issue: "High costs"
- Review model usage in analysis_costs table
- Switch to cheaper models for simple tasks
- Implement better caching

## Future Enhancements

1. **Motion Detection**: Only analyze when movement detected
2. **Differential Analysis**: Compare with previous image
3. **Multi-Model Consensus**: Use multiple AI providers for critical detections
4. **Learning System**: Improve prompts based on accuracy
5. **Edge Processing**: Pre-filter images before cloud analysis

## Monitoring Queries

```sql
-- Check processing performance
SELECT * FROM analysis_performance;

-- View pending work
SELECT * FROM pending_analysis_summary;

-- Recent alerts
SELECT * FROM analysis_alerts 
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- Cost tracking
SELECT 
    date,
    model_provider,
    SUM(analysis_count) as total_analyses,
    SUM(estimated_cost) as total_cost
FROM analysis_costs
WHERE date > CURRENT_DATE - 7
GROUP BY date, model_provider
ORDER BY date DESC;
```

## Contact

For questions about the analysis service architecture, please refer to the README.md or create an issue in the repository.