"""
Data Ingestion API routes
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Dict, Any
import uuid
from datetime import datetime, timezone

from services.data_ingestion import DataIngestionService
from services.s3_service import S3Service
from services.dynamodb_service import DynamoDBService
from config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/data", tags=["Data Ingestion"])


@router.post("/upload/csv/{data_type}")
async def upload_csv(data_type: str, file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload CSV or Excel file for data ingestion.

    Args:
        data_type: Type of data (sales, inventory, market_trends)
        file: CSV (.csv) or Excel (.xlsx / .xls) file

    Returns:
        Ingestion result
    """
    VALID_TYPES = ['sales', 'inventory', 'market_trends', 'enterprise']
    if data_type not in VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data type '{data_type}'. Must be one of: {VALID_TYPES}"
        )

    try:
        filename = file.filename or "upload.csv"
        content = await file.read()

        # S3 upload — non-blocking: failure logs but does not abort processing
        s3_result = S3Service().upload_file_bytes(content, filename, data_type)
        if not s3_result["success"]:
            logger.warning("S3 upload skipped for '%s': %s", filename, s3_result["error"])

        service = DataIngestionService()
        result = await service.ingest_csv(content, data_type, filename=filename)

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['errors'])

        # Attach S3 metadata to response when available
        if s3_result["success"]:
            result["s3_key"] = s3_result["s3_key"]
            result["s3_url"] = s3_result["s3_url"]

        # Save upload metadata to DynamoDB (non-blocking)
        DynamoDBService().put_item(
            settings.DYNAMO_TABLE_UPLOADS,
            {
                "ingestion_id": result.get("ingestion_id") or str(uuid.uuid4()),
                "filename": filename,
                "data_type": data_type,
                "records_count": result.get("records_count", 0),
                "s3_key": s3_result.get("s3_key") or "",
                "s3_url": s3_result.get("s3_url") or "",
                "uploaded_at": datetime.now(tz=timezone.utc).isoformat(),
            },
            hash_key="ingestion_id",
        )

        return result
    except StarletteHTTPException:
        # Re-raise FastAPI/Starlette HTTP exceptions unchanged (don't wrap as 500)
        raise
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/json/{data_type}")
async def upload_json(data_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upload JSON data for ingestion
    
    Args:
        data_type: Type of data (sales, inventory, market_trends)
        data: JSON data
    
    Returns:
        Ingestion result
    """
    VALID_TYPES = ['sales', 'inventory', 'market_trends', 'enterprise']
    if data_type not in VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data type '{data_type}'. Must be one of: {VALID_TYPES}"
        )
    
    try:
        service = DataIngestionService()
        result = await service.ingest_json(data, data_type)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['errors'])
        
        return result
    except Exception as e:
        logger.error(f"JSON upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
