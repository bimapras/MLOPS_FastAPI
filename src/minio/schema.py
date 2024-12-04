from fastapi import UploadFile
from pydantic import BaseModel

class ImageRespond(BaseModel):
    id: int
    image_name: str
    file_url: str
    prediction : str
    confidence : float
    
class CreateImage(BaseModel):
    file : UploadFile
    