#!/usr/bin/env python3
"""
Production-Ready ID Card Straightening API Service
FastAPI-based REST API for auto-rotation and straightening of ID documents
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, status, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import tempfile
import base64
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
import cv2
import numpy as np
from PIL import Image
import io
import logging

# Import our optimized straightener
from optimized_straightener import OptimizedRotationDetector, OptimizedSkewCorrector

# Import PDF converter
from pdf_converter import PDFConverter

# Background removal
from rembg import remove

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Image Processing API",
    description="Production-ready API for image processing: ID card straightening and image-to-PDF conversion",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
rotation_detector = OptimizedRotationDetector()
skew_corrector = OptimizedSkewCorrector()
pdf_converter = PDFConverter()

# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

class ProcessingStats:
    """Class to track processing statistics"""
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_processing_time = 0.0

        # PDF conversion stats
        self.pdf_conversion_requests = 0
        self.pdf_conversion_successful = 0
        self.pdf_conversion_failed = 0
        self.total_images_converted = 0
        self.total_pdf_processing_time = 0.0

        self.start_time = datetime.now()

stats = ProcessingStats()

def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file"""
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {file.size} exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
        )

    # Check file extension
    if file.filename:
        file_ext = os.path.splitext(file.filename.lower())[1]
        if file_ext not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format {file_ext}. Supported formats: {', '.join(SUPPORTED_FORMATS)}"
            )

def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string"""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

def process_image_pipeline(image_path: str) -> Dict[str, Any]:
    """Complete image processing pipeline"""
    start_time = time.time()

    try:
        # Step 1: Rotation detection
        rotation_result = rotation_detector.detect_best_rotation(image_path)
        best_angle = rotation_result["best_angle"]
        rotation_confidence = rotation_result["confidence"]

        # Apply rotation if needed
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Could not read image file")

        rotation_applied = False
        if best_angle != 0:
            if best_angle == 90:
                img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            elif best_angle == 180:
                img = cv2.rotate(img, cv2.ROTATE_180)
            elif best_angle == 270:
                img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            rotation_applied = True

        # Step 2: Skew correction
        straightened_img, skew_angle = skew_corrector.straighten_image(img)
        skew_applied = abs(skew_angle) > 0.3

        # Save final result
        output_path = image_path.replace('.jpg', '_straightened.jpg')
        cv2.imwrite(output_path, straightened_img)

        processing_time = time.time() - start_time

        return {
            "success": True,
            "output_path": output_path,
            "processing_time": processing_time,
            "rotation": {
                "angle_applied": best_angle,
                "confidence": rotation_confidence,
                "applied": rotation_applied
            },
            "skew_correction": {
                "angle_detected": skew_angle,
                "applied": skew_applied
            },
            "ocr_results": rotation_result.get("all_results", {}).get(best_angle, {})
        }

    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image processing failed: {str(e)}"
        )

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with basic API information"""
    return {
        "service": "Image Processing API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "straighten": "/straighten",
            "convert-to-pdf": "/convert-to-pdf",
            "remove-background": "/remove-background",
            "stats": "/stats",
            "docs": "/docs"
        }
    }



@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    uptime = datetime.now() - stats.start_time
    return {
        "status": "healthy",
        "uptime_seconds": uptime.total_seconds(),
        "total_requests": stats.total_requests,
        "success_rate": (stats.successful_requests / max(stats.total_requests, 1)) * 100
    }

@app.get("/stats", tags=["Monitoring"])
async def get_stats():
    """Get processing statistics"""
    uptime = datetime.now() - stats.start_time
    avg_processing_time = (stats.total_processing_time / max(stats.successful_requests, 1))

    # PDF conversion stats
    avg_pdf_processing_time = (stats.total_pdf_processing_time / max(stats.pdf_conversion_successful, 1))

    return {
        "uptime_seconds": uptime.total_seconds(),
        "total_requests": stats.total_requests,
        "successful_requests": stats.successful_requests,
        "failed_requests": stats.failed_requests,
        "success_rate_percent": (stats.successful_requests / max(stats.total_requests, 1)) * 100,
        "average_processing_time_seconds": avg_processing_time,
        "total_processing_time_seconds": stats.total_processing_time,

        # PDF conversion statistics
        "pdf_conversion": {
            "total_requests": stats.pdf_conversion_requests,
            "successful_requests": stats.pdf_conversion_successful,
            "failed_requests": stats.pdf_conversion_failed,
            "success_rate_percent": (stats.pdf_conversion_successful / max(stats.pdf_conversion_requests, 1)) * 100,
            "total_images_converted": stats.total_images_converted,
            "average_processing_time_seconds": avg_pdf_processing_time,
            "total_processing_time_seconds": stats.total_pdf_processing_time
        }
    }

@app.post("/straighten", tags=["Image Processing"])
async def straighten_image(
    file: UploadFile = File(...),
    return_format: str = "base64"  # "base64" or "file"
):
    """
    Straighten an ID card image by detecting rotation and correcting skew

    Parameters:
    - file: Image file (JPG, PNG, BMP, TIFF, WEBP)
    - return_format: "base64" (default) or "file"

    Returns:
    - Straightened image and processing metadata
    """
    stats.total_requests += 1

    try:
        # Validate input
        validate_image_file(file)

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            # Read and save uploaded file
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Process the image
            result = process_image_pipeline(temp_path)

            # Update stats
            stats.successful_requests += 1
            stats.total_processing_time += result["processing_time"]

            # Prepare response
            response_data = {
                "success": True,
                "filename": file.filename,
                "processing_time_seconds": result["processing_time"],
                "rotation": result["rotation"],
                "skew_correction": result["skew_correction"],
                "ocr_confidence": result["ocr_results"].get("avg_confidence", 0),
                "keywords_detected": result["ocr_results"].get("keyword_count", 0)
            }

            if return_format == "base64":
                # Return base64 encoded image
                image_base64 = image_to_base64(result["output_path"])
                response_data["image_base64"] = image_base64
                response_data["image_format"] = "base64"

                # Cleanup
                os.unlink(temp_path)
                os.unlink(result["output_path"])

                return JSONResponse(content=response_data)

            elif return_format == "file":
                # Return file download
                response_data["image_format"] = "file"

                # Cleanup temp input file
                os.unlink(temp_path)

                return FileResponse(
                    path=result["output_path"],
                    filename=f"straightened_{file.filename}",
                    media_type="image/jpeg",
                    headers={"X-Processing-Stats": str(response_data)}
                )

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid return_format. Use 'base64' or 'file'"
                )

        finally:
            # Cleanup temp file if it still exists
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except HTTPException:
        stats.failed_requests += 1
        raise
    except Exception as e:
        stats.failed_requests += 1
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )



@app.post("/remove-background", tags=["Image Processing"])
async def remove_background(
    file: UploadFile = File(...),
    return_format: str = "file"  # "file" (default) or "base64"
):
    """
    Remove background from an uploaded image using AI (rembg)

    Parameters:
    - file: Image file (JPG, PNG, BMP, TIFF, WEBP)
    - return_format: "file" (default) or "base64"

    Returns:
    - PNG image with background removed
    """
    stats.total_requests += 1

    try:
        # Validate input
        validate_image_file(file)

        # Read file bytes
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded"
            )

        # Decode image
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file"
            )

        # Convert BGR to RGB
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        try:
            # Apply background removal
            output = remove(rgb_img)
        except Exception as e:
            logger.error(f"Background removal failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Background removal failed: {str(e)}"
            )

        # Convert to PNG bytes
        pil_img = Image.fromarray(output)
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # Return as base64 JSON
        if return_format == "base64":
            png_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
            stats.successful_requests += 1
            return JSONResponse(content={
                "success": True,
                "filename": file.filename,
                "image_format": "base64",
                "image_base64": png_base64
            })

        # Or return as file download
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_out:
            tmp_out.write(img_byte_arr.getvalue())
            output_path = tmp_out.name

        stats.successful_requests += 1
        return FileResponse(
            path=output_path,
            filename=(os.path.splitext(file.filename or "image")[0] + "_no_bg.png"),
            media_type="image/png"
        )

    except HTTPException:
        stats.failed_requests += 1
        raise
    except Exception as e:
        stats.failed_requests += 1
        logger.error(f"Unexpected background removal error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during background removal"
        )

@app.post("/convert-to-pdf", tags=["PDF Conversion"])


async def convert_images_to_pdf(
    files: List[UploadFile] = File(...),
    return_format: str = Form("file"),  # "file" (default) or "base64"
    page_size: str = Form("A4"),  # "A4", "Letter", "Legal"
    fit_mode: str = Form("fit")  # "fit" (maintain aspect ratio) or "fill"
):
    """
    Convert one or more images to PDF format

    Parameters:
    - files: One or more image files (JPG, PNG, GIF, BMP, TIFF, WEBP) - max 10MB each, up to 20 files
    - return_format: "file" (default) or "base64"
    - page_size: "A4" (default), "Letter", or "Legal"
    - fit_mode: "fit" (maintain aspect ratio, default) or "fill" (stretch to fill)

    Returns:
    - PDF file download or JSON with base64 encoded PDF and metadata
    """
    stats.pdf_conversion_requests += 1
    temp_files = []

    try:
        # Input validation
        if not files or len(files) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided"
            )

        if len(files) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many files. Maximum 20 files per request"
            )

        # Validate parameters
        valid_page_sizes = ["A4", "Letter", "Legal"]
        if page_size not in valid_page_sizes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid page_size '{page_size}'. Supported: {', '.join(valid_page_sizes)}"
            )

        valid_fit_modes = ["fit", "fill"]
        if fit_mode not in valid_fit_modes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid fit_mode '{fit_mode}'. Supported: {', '.join(valid_fit_modes)}"
            )

        valid_return_formats = ["file", "base64"]
        if return_format not in valid_return_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid return_format '{return_format}'. Supported: {', '.join(valid_return_formats)}"
            )

        # Validate and save uploaded files
        for i, file in enumerate(files):
            try:
                validate_image_file(file)

                # Create temporary file with proper extension
                file_ext = os.path.splitext(file.filename or '.jpg')[1].lower()
                if not file_ext:
                    file_ext = '.jpg'

                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                    content = await file.read()
                    if not content:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"File {i+1} is empty"
                        )
                    temp_file.write(content)
                    temp_files.append(temp_file.name)

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error processing file {i+1}: {str(e)}"
                )

        # Create output PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as pdf_temp:
            pdf_output_path = pdf_temp.name

        try:
            # Convert images to PDF
            if len(temp_files) == 1:
                result = pdf_converter.convert_single_image_to_pdf(
                    temp_files[0], pdf_output_path, page_size, fit_mode
                )
            else:
                result = pdf_converter.convert_multiple_images_to_pdf(
                    temp_files, pdf_output_path, page_size, fit_mode
                )

            # Check if conversion was successful
            if not result.get("success", True):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="PDF conversion failed"
                )

            # Update statistics
            stats.pdf_conversion_successful += 1
            stats.total_pdf_processing_time += result["processing_time"]
            stats.total_images_converted += len(temp_files)

            # Prepare response data
            response_data = {
                "success": True,
                "total_images": len(files),
                "processing_time_seconds": round(result["processing_time"], 4),
                "page_size": page_size,
                "fit_mode": fit_mode,
                "output_size_bytes": result.get("output_size", 0),
                "input_filenames": [f.filename for f in files]
            }

            # Add conversion details for multi-image PDFs
            if len(temp_files) > 1:
                response_data.update({
                    "successful_images": result.get("successful_images", len(temp_files)),
                    "failed_images": result.get("failed_images", 0),
                    "partial_success": result.get("partial_success", False)
                })

            if return_format == "base64":
                # Return base64 encoded PDF
                try:
                    with open(pdf_output_path, "rb") as pdf_file:
                        pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')

                    response_data["pdf_base64"] = pdf_base64

                    # Cleanup PDF file
                    os.unlink(pdf_output_path)

                    return JSONResponse(content=response_data)

                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to encode PDF: {str(e)}"
                    )

            else:  # return_format == "file"
                # Generate appropriate filename
                if len(files) == 1:
                    base_name = os.path.splitext(files[0].filename or "image")[0]
                    output_filename = f"{base_name}.pdf"
                else:
                    output_filename = f"converted_{len(files)}_images.pdf"

                return FileResponse(
                    path=pdf_output_path,
                    filename=output_filename,
                    media_type="application/pdf",
                    headers={
                        "X-Processing-Time": str(response_data["processing_time_seconds"]),
                        "X-Total-Images": str(response_data["total_images"]),
                        "X-Output-Size": str(response_data["output_size_bytes"])
                    }
                )

        except Exception as e:
            logger.error(f"PDF generation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF generation failed: {str(e)}"
            )
        finally:
            # Cleanup temp image files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

    except HTTPException:
        stats.pdf_conversion_failed += 1
        raise
    except Exception as e:
        stats.pdf_conversion_failed += 1
        logger.error(f"Unexpected PDF conversion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during PDF conversion"
        )

if __name__ == "__main__":
    # Run the API server
    uvicorn.run(
        "api_service:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=bool(os.getenv("DEV_RELOAD", "")),
        log_level="info"
    )
