# from fastapi import APIRouter, Request
# from app.services import Query

# router = APIRouter()

# @router.post("/")
# async def query_docs(request: Request):
#     body = await request.json()
#     query = body.get("query")
#     results = Query.query_documents(query, k=5)
#     return {"results": results}


from fastapi import APIRouter, Body
from app.services import Query
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/")
async def query_endpoint(query: str = Body(..., embed=True)):
    try:
        results = Query.query_documents(query)
        logger.info(f"✅ Found {results} results.")
        return {"results": results}
    except Exception as e:
        
        logger.error(f"❌ Error processing query: {str(e)}")
        return {"error": "Something went wrong."}
