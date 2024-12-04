from src.minio.schema import CreateImage
from sqlalchemy.future import select
from src.database.db_model import Image as ImageDB
from uuid import uuid4
from dotenv import load_dotenv
from typing import List
from fastapi import HTTPException
import tensorflow as tf
import numpy as np
import io
import os

class_list = ['Bean',
 'Bitter_Gourd',
 'Bottle_Gourd',
 'Brinjal',
 'Broccoli',
 'Cabbage',
 'Capsicum',
 'Carrot',
 'Cauliflower',
 'Cucumber',
 'Papaya',
 'Potato',
 'Pumpkin',
 'Radish',
 'Tomato'
]

class UtilService:
    def __init__(self, session, minio_client):
        self.load_env = load_dotenv()
        self.session = session
        self.minio_client = minio_client
        self.model = tf.keras.models.load_model(os.getenv('MODEL_PATH'))
        
    async def get_image(self, image_id: str) -> ImageDB:
        image = await self.session.get(ImageDB, image_id)
        return image
    
    async def get_all_images(self) -> List[ImageDB]:
        stmt = select(ImageDB)
        result = await self.session.execute(stmt)  # Sesuaikan dengan nama tabel di database
        return result.scalars().all()
    
    async def preprocess_image(self, file) -> np.ndarray:
        image = tf.image.decode_image(file)
        image = tf.image.resize(image, [150, 150]) # Resize image to 150x150
        image = tf.cast(image, tf.float32) / 255.0 # Normalize image
        image = tf.expand_dims(image, 0) # Add batch dimension
        return image
    
    async def predict_image(self, file: io.BytesIO) -> dict:
        image = await self.preprocess_image(file)
        prediction = self.model.predict(image)
        predicted_class_index = np.argmax(prediction, axis=1)[0]
        predicted_class_name = class_list[predicted_class_index]
        confidence = float(np.max(prediction))  # Get the confidence score of the predicted class
        return {'class_name': predicted_class_name, 'confidence': confidence}
    
    async def upload_image(self, create_image : CreateImage) -> ImageDB:
        file = create_image.file
        filename = f"{uuid4()}_{file.filename}"
        
        content = await file.read()
        content_io = io.BytesIO(content)
        
        # Predict image
        prediction = await self.predict_image(content)
        
        # Upload image to Minio
        self.minio_client.put_object(os.getenv('MINIO_BUCKET'), filename, content_io, len(content))
        
        # Generate presigned URL
        file_url = self.minio_client.presigned_get_object(os.getenv('MINIO_BUCKET'), filename)
        
        # Upload image to Postgre
        image = ImageDB(
            image_name=filename,
            file_url=file_url,
            prediction=prediction['class_name'],
            confidence=prediction['confidence']
        )
        
        self.session.add(image)
        await self.session.commit()
            
        return image
    
    async def upload_images(self, create_images: List[CreateImage]) -> List[ImageDB]:
        uploaded_images = []
        for create_image in create_images:
            uploaded_image = await self.upload_image(create_image)
            uploaded_images.append(uploaded_image)
        return uploaded_images
    
    # async def delete_image(self, image_id: str) -> ImageDB:
    #     image = await self.get_image(image_id)
    #     self.minio_client.remove_object(os.getenv('MINIO_BUCKET'), image.image_name)
    #     self.session.delete(image)
    #     await self.session.commit()
    #     return image
    
    async def delete_image(self, image_id: int) -> None:
        try:
            # Ambil gambar dari database
            image = await self.get_image(image_id)
            
            if not image:
                raise HTTPException(status_code=404, detail="Image not found")
            
            # Hapus gambar dari MinIO
            self.minio_client.remove_object(os.getenv('MINIO_BUCKET'), image.image_name)
            
            # Hapus gambar dari database
            await self.session.delete(image)
            await self.session.commit()  # Commit perubahan ke database
            
            # Logging untuk memastikan commit berhasil
            print(f"Image with ID {image_id} successfully deleted from database.")
        
        except Exception as e:
            # Jika terjadi kesalahan, rollback transaksi
            await self.session.rollback()
            print(f"Failed to delete image with ID {image_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete image")
