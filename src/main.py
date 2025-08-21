import base64
import datetime
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Global State (for simplicity, will be replaced by a proper data store) ---
latest_signal: SignalResponse | None = None
analyzer: IAnalyzer | None = None


app = FastAPI(
    title="AI Trading Bot API",
    version="1.0.0",
    description="API for the AI Trading Bot system, integrating with MT5 and OpenAI.",
)

@app.on_event("startup")
async def startup_event():
    """
    On startup, create the analyzer instance.
    This makes it available for the lifetime of the application.
    """
    global analyzer
    try:
        from .analysis.openai_analyzer import OpenAIAnalyzer
        from .common.interfaces import IAnalyzer as IAnalyzer_ # prevent name clash
        analyzer = OpenAIAnalyzer()
        logger.info("OpenAIAnalyzer initialized successfully.")
    except (ValueError, ImportError) as e:
        logger.error(f"Failed to initialize OpenAIAnalyzer: {e}")
        # The app will run, but analysis endpoints will fail.
        analyzer = None

from .api.models import (
    ScreenshotPayload,
    SignalListResponse,
    SignalResponse,
)
from .common.interfaces import IAnalyzer


@app.get("/health", status_code=200)
async def health_check():
    """
    Health check endpoint to confirm the API is running.
    This is used by the EA to test the connection.
    """
    logger.info("Health check endpoint was called.")
    return {"status": "ok"}


@app.post("/api/v1/market-analysis/screenshot", status_code=202)
async def receive_screenshot(payload: ScreenshotPayload):
    """
    Receives a screenshot and market context, then triggers AI analysis.
    """
    global latest_signal
    logger.info(f"Received screenshot for {payload.symbol} on timeframe {payload.timeframe}")

    if not analyzer:
        raise HTTPException(status_code=503, detail="Analyzer service is not available.")

    try:
        image_bytes = base64.b64decode(payload.image_data)

        # Asynchronously run the analysis
        signal = await analyzer.analyze(image_bytes, payload.market_context.dict())

        if signal:
            latest_signal = signal
            logger.info(f"New signal generated and stored for {signal.symbol}")
            return {"message": "Analysis complete. Signal generated."}
        else:
            logger.info("Analysis complete. No signal generated.")
            return {"message": "Analysis complete. No signal generated."}

    except binascii.Error as e:
        logger.error(f"Failed to decode Base64 image: {e}")
        raise HTTPException(status_code=400, detail="Invalid Base64 data.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during analysis trigger: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


@app.get("/api/v1/market-analysis/signals", response_model=SignalListResponse)
async def get_signals():
    """
    Provides the latest generated trading signal to the MT5 EA.
    """
    global latest_signal
    logger.info("Signal endpoint was called by a client.")

    if latest_signal:
        # The EA expects a list of signals.
        response_data = {"signals": [latest_signal.dict()]}
        # Clear the signal after it has been fetched to avoid re-execution.
        latest_signal = None
        logger.info(f"Signal for {response_data['signals'][0]['symbol']} was provided and cleared.")
        return response_data
    else:
        # Return an empty list if there are no new signals.
        logger.info("No new signal available.")
        return {"signals": []}
