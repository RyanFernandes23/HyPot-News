import os
import shutil
import logging
from fastapi import APIRouter, HTTPException, Depends
from src.core.config import settings
from src.db.supabase import supabase_service
from src.services.storage.s3 import s3_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin"])

@router.post("/admin/dev-cleanup")
async def dev_cleanup():
    """
    Cleans up all development data: 
    - Empties news_articles table in Supabase
    - Deletes all objects in S3/B2 bucket
    - Empties local temp_audio directory
    """
    if not settings.ALLOW_DEV_CLEANUP:
        raise HTTPException(
            status_code=403, 
            detail="Development cleanup is disabled in this environment. Set ALLOW_DEV_CLEANUP=true to enable."
        )

    results = {
        "supabase": 0,
        "s3": 0,
        "local": False
    }

    try:
        # 1. Supabase: Delete all articles
        # Supabase client delete() requires a filter. We'll use a filter that matches everything.
        # Assuming ID is UUID, or we just want everything.
        response = supabase_service.table("news_articles").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        results["supabase"] = len(response.data) if response.data else 0
        logger.info(f"[Admin] Deleted {results['supabase']} articles from Supabase.")

        # 2. S3/B2: Delete all objects
        results["s3"] = s3_service.delete_all_objects()
        logger.info(f"[Admin] Deleted {results['s3']} objects from S3.")

        # 3. Local Temp files
        temp_dir = settings.TEMP_DIR
        if os.path.exists(temp_dir):
            for entry in os.listdir(temp_dir):
                path = os.path.join(temp_dir, entry)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            results["local"] = True
            logger.info(f"[Admin] Emptied local temporary directory: {temp_dir}")

        return {
            "status": "success",
            "message": "Development cleanup completed successfully.",
            "details": results
        }

    except Exception as e:
        logger.error(f"[Admin] Cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")
