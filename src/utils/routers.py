from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request
from src.minio.schema import ImageRespond
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db_connection import get_session
from src.minio.minio_client import get_minio_client
from src.utils.service import UtilService
from src.minio.schema import CreateImage
from fastapi.templating import Jinja2Templates
from typing import List

image_router = APIRouter(
    prefix="/api/image",
)

templates = Jinja2Templates(directory="templates")

@image_router.get("/", response_class=HTMLResponse)
async def read_images(request: Request, session: AsyncSession = Depends(get_session), minio_client = Depends(get_minio_client)):
    service = UtilService(session, minio_client)
    images = await service.get_all_images()
    return templates.TemplateResponse("index.html", {"request": request, "images": images})

@image_router.post("/upload_image", response_model=ImageRespond)
async def upload_image(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    minio_client = Depends(get_minio_client)):
    
    service = UtilService(session, minio_client)
    image = CreateImage(file=file)
    upload_image = await service.upload_image(image)
    
    return upload_image

# upload multiple images
@image_router.post("/upload_images", response_class=RedirectResponse)
async def upload_images(
    files: List[UploadFile] = File(...),
    session: AsyncSession = Depends(get_session),
    minio_client = Depends(get_minio_client)):
    
    service = UtilService(session, minio_client)
    images = [CreateImage(file=file) for file in files]
    await service.upload_images(images)
    
    return RedirectResponse(url="/api/image/", status_code=303)

# delete image
@image_router.post("/delete_image/{image_id}", response_class=RedirectResponse)
async def delete_image(image_id: str, session: AsyncSession = Depends(get_session), minio_client = Depends(get_minio_client)):
    service = UtilService(session, minio_client)
    
    # Convert image_id to integer
    try:
        image_id = int(image_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image ID")
    
    await service.delete_image(image_id)
    
    return RedirectResponse(url="/api/image/", status_code=303)