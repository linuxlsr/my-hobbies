#!/usr/bin/env python3
"""FastAPI web application for PowerballAI Predictor"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from data_collector import PowerballDataCollector
from analyzer import PowerballAnalyzer
from predictor import PowerballPredictor

app = FastAPI(title="Powerball Statistical Edge", version="1.0.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

class PredictionRequest(BaseModel):
    tickets: int = 1
    strategy: str = "balanced"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    """Simple health check"""
    return {'status': 'ok', 'timestamp': str(datetime.now())}

@app.get("/ping")
async def ping():
    """Ultra simple ping"""
    return 'pong'

@app.get("/api/status")
async def api_status():
    """Get system status"""
    try:
        collector = PowerballDataCollector()
        summary = collector.get_data_summary()
        
        return {
            'status': 'ok',
            'database_connected': True,
            'total_drawings': summary['total_drawings'],
            'date_range': summary['date_range'],
            'data_quality': min(summary['total_drawings'] / 200, 1.0)
        }
    except Exception as e:
        return {
            'status': 'error',
            'database_connected': False,
            'error': str(e)
        }

@app.get("/api/analyze")
async def api_analyze():
    """Get statistical analysis"""
    try:
        analyzer = PowerballAnalyzer()
        analysis = analyzer.get_comprehensive_analysis()
        
        if 'error' in analysis:
            raise HTTPException(status_code=500, detail=analysis['error'])
        
        # Simplify for web display
        simplified = {
            'data_summary': analysis['data_summary'],
            'frequency_analysis': analysis['frequency_analysis'],
            'gap_analysis': analysis['gap_analysis'],
            'exclusive_groups': analysis.get('exclusive_groups', {})
        }
        
        return simplified
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict")
async def api_predict(request: PredictionRequest):
    """Generate predictions"""
    try:
        predictor = PowerballPredictor()
        results = predictor.generate_predictions(
            num_tickets=request.tickets, 
            strategy=request.strategy
        )
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update-data")
async def api_update_data():
    """Update historical data"""
    try:
        collector = PowerballDataCollector()
        collector.setup_database()
        collector.update_data()
        
        summary = collector.get_data_summary()
        return {
            'status': 'success',
            'total_drawings': summary['total_drawings'],
            'date_range': summary['date_range']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Production configuration
    port = int(os.environ.get('PORT', 5000))
    uvicorn.run(app, host='0.0.0.0', port=port)