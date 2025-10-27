import os
import uuid
from typing import Dict, Any
from PIL import Image
import PyPDF2
import openpyxl
import csv
import io
import base64
from fastapi import UploadFile, HTTPException
import logging

logger = logging.getLogger(__name__)

class FileProcessor:
    """Handles file processing and content extraction"""
    
    SUPPORTED_TYPES = {
        'text/plain': '.txt',
        'application/pdf': '.pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/msword': '.doc',
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'text/csv': '.csv',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
        'application/vnd.ms-excel': '.xls',
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    async def process_file(file: UploadFile) -> Dict[str, Any]:
        """Process uploaded file and extract content"""
        
        # Validate file size
        content = await file.read()
        if len(content) > FileProcessor.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {FileProcessor.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Reset file pointer
        await file.seek(0)
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Determine file type
        file_type = file.content_type or 'application/octet-stream'
        file_extension = FileProcessor.SUPPORTED_TYPES.get(file_type, '')
        
        if not file_extension:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_type}"
            )
        
        # Extract content based on file type
        content_text = await FileProcessor._extract_content(file, file_type, content)
        
        # Generate file URL (in production, this would be a real URL)
        file_url = f"/files/{file_id}{file_extension}"
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "file_type": file_type,
            "file_size": len(content),
            "url": file_url,
            "content": content_text,
            "extension": file_extension
        }
    
    @staticmethod
    async def _extract_content(file: UploadFile, file_type: str, content: bytes) -> str:
        """Extract text content from different file types"""
        
        try:
            if file_type == 'text/plain':
                return content.decode('utf-8')
            
            elif file_type == 'application/pdf':
                return FileProcessor._extract_pdf_content(content)
            
            elif file_type in ['image/jpeg', 'image/png', 'image/gif']:
                return FileProcessor._extract_image_content(content)
            
            elif file_type == 'text/csv':
                return FileProcessor._extract_csv_content(content)
            
            elif file_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']:
                return FileProcessor._extract_excel_content(content)
            
            elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
                return "[Word document - content extraction not implemented yet]"
            
            else:
                return f"[File type {file_type} - content extraction not supported]"
                
        except Exception as e:
            logger.error(f"Error extracting content from {file.filename}: {e}")
            return f"[Error extracting content: {str(e)}]"
    
    @staticmethod
    def _extract_pdf_content(content: bytes) -> str:
        """Extract text from PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            return f"[Error reading PDF: {str(e)}]"
    
    @staticmethod
    def _extract_image_content(content: bytes) -> str:
        """Extract information from image"""
        try:
            image = Image.open(io.BytesIO(content))
            return f"[Image: {image.size[0]}x{image.size[1]} pixels, Mode: {image.mode}]"
        except Exception as e:
            return f"[Error processing image: {str(e)}]"
    
    @staticmethod
    def _extract_csv_content(content: bytes) -> str:
        """Extract text from CSV"""
        try:
            csv_content = content.decode('utf-8')
            reader = csv.reader(io.StringIO(csv_content))
            rows = list(reader)
            
            # Limit to first 100 rows to avoid huge responses
            if len(rows) > 100:
                rows = rows[:100]
                text = "\n".join([",".join(row) for row in rows])
                text += f"\n[CSV truncated - showing first 100 rows of {len(rows)} total]"
            else:
                text = "\n".join([",".join(row) for row in rows])
            
            return text
        except Exception as e:
            return f"[Error reading CSV: {str(e)}]"
    
    @staticmethod
    def _extract_excel_content(content: bytes) -> str:
        """Extract text from Excel file"""
        try:
            workbook = openpyxl.load_workbook(io.BytesIO(content))
            text = ""
            
            for sheet_name in workbook.sheetnames[:3]:  # Limit to first 3 sheets
                sheet = workbook[sheet_name]
                text += f"\n--- Sheet: {sheet_name} ---\n"
                
                # Get first 50 rows
                for row in sheet.iter_rows(max_row=50, values_only=True):
                    if any(cell is not None for cell in row):
                        text += "\t".join([str(cell) if cell is not None else "" for cell in row]) + "\n"
            
            if len(workbook.sheetnames) > 3:
                text += f"\n[Excel truncated - showing first 3 sheets of {len(workbook.sheetnames)} total]"
            
            return text.strip()
        except Exception as e:
            return f"[Error reading Excel: {str(e)}]"
