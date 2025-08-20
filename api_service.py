#!/usr/bin/env python3
"""
Production-Ready ID Card Straightening API Service
FastAPI-based REST API for auto-rotation and straightening of ID documents
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, status, Form
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
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
import img2pdf
import logging

# Import our hardened straightener
from hardened_straightener import HardenedStraightener, hardened_straightener

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
straightener = hardened_straightener
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

def _flatten_alpha_to_rgb(pil_img: Image.Image, bg=(255, 255, 255)) -> Image.Image:
    """Remove transparency the right way to avoid black boxes in PDF."""
    if pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info):
        base = Image.new("RGB", pil_img.size, bg)
        base.paste(pil_img, mask=pil_img.split()[-1])  # composite by alpha
        return base
    return pil_img.convert("RGB")

def process_image_pipeline(image_path: str) -> Dict[str, Any]:
    """Complete image processing pipeline using hardened straightener"""
    start_time = time.time()

    try:
        result = straightener.straighten_image(image_path)
        if not result.get("success"):
            raise ValueError(result.get("error", "Unknown error during straightening"))

        # Save final result to disk (PNG for web-friendly streaming)
        output_path = image_path.replace('.jpg', '_straightened.png')
        # Convert PIL image to bytes
        img_bytes = io.BytesIO()
        result["image"].save(img_bytes, format="PNG")
        with open(output_path, 'wb') as f:
            f.write(img_bytes.getvalue())

        processing_time = result.get("processing_time", time.time() - start_time)

        return {
            "success": True,
            "output_path": output_path,
            "processing_time": processing_time,
            "rotation": result.get("orientation", {}),
            "skew_correction": result.get("skew_correction", {}),
            "ocr_results": {}
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
        "build_type": "full",
        "features": {
            "advanced_ocr": "PaddleOCR CNN-based orientation detection",
            "background_removal": "rembg with ONNX models",
            "pdf_conversion": "img2pdf with alpha channel handling",
            "auto_rotation": "EXIF + CNN + Hough line correction"
        },
        "endpoints": {
            "health": "/health",
            "straighten": "/straighten",
            "convert-to-pdf": "/convert-to-pdf",
            "remove-background": "/remove-background",
            "test-pdf-conversion": "/test-pdf-conversion",
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
    return_format: str = Form("file")  # "file" (default) or "base64"
):
    """
    Straighten an ID card image by detecting rotation and correcting skew

    Parameters:
    - file: Image file (JPG, PNG, BMP, TIFF, WEBP)
    - return_format: "file" (default) or "base64"

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
                # Return inline file using StreamingResponse as PNG (more web-friendly)
                response_data["image_format"] = "file"

                # Read the processed image into memory and stream it
                with open(result["output_path"], "rb") as f:
                    data = f.read()
                buf = io.BytesIO(data)
                buf.seek(0)

                # Cleanup temp input file (keep output until streamed)
                os.unlink(temp_path)

                headers = {"X-Processing-Stats": str(response_data),
                           "Content-Disposition": 'inline; filename="straightened.png"'}

                return StreamingResponse(buf, media_type="image/png", headers=headers)

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
async def convert_to_pdf(
    files: List[UploadFile] = File(...),
    # page sizing: "fit" (image-sized pages) or A4, Letter, 210mmx297mm, A4^T, etc.
    page_size: str = Form("fit"),
    # how to fit the image when using a fixed page_size (A4/Letter/etc.)
    fit_mode: str = Form("into"),  # into|fill|exact|shrink|enlarge (img2pdf)
    # optional white background (useful after BG removal)
    bg_color: str = Form("255,255,255"),  # "R,G,B"
):
    """
    Convert one or more images to PDF format with improved alpha handling

    Parameters:
    - files: One or more image files (JPG, PNG, GIF, BMP, TIFF, WEBP) - max 10MB each, up to 20 files
    - page_size: "fit" (image-sized pages, default), "A4", "Letter", "A4^T", "210mmx297mm", etc.
    - fit_mode: "into" (fit inside, default), "fill", "exact", "shrink", "enlarge" (img2pdf modes)
    - bg_color: Background color for alpha removal as "R,G,B" (default: "255,255,255" for white)

    Returns:
    - PDF file with proper alpha handling and configurable page sizing
    """
    stats.pdf_conversion_requests += 1

    try:
        # Validate number of files
        if len(files) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 20 files allowed per request"
            )

        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one file is required"
            )

        # Parse background color
        try:
            bg_rgb = tuple(map(int, bg_color.split(',')))
            if len(bg_rgb) != 3 or any(c < 0 or c > 255 for c in bg_rgb):
                raise ValueError()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="bg_color must be in format 'R,G,B' with values 0-255"
            )

        # Track processing start time
        start_time = time.time()

        # 1) Read & pre-process images (remove alpha)
        rgb_bytes_list: List[bytes] = []
        for i, f in enumerate(files):
            try:
                # Validate file
                validate_image_file(f)

                raw = await f.read()
                img = Image.open(io.BytesIO(raw))
                img = _flatten_alpha_to_rgb(img, bg_rgb)  # important: remove alpha
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=95)  # JPEG keeps PDFs tiny
                rgb_bytes_list.append(buf.getvalue())

            except HTTPException as e:
                raise HTTPException(
                    status_code=e.status_code,
                    detail=f"File {i+1} ({f.filename}): {e.detail}"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {i+1} ({f.filename}): Failed to process image - {str(e)}"
                )

        # 2) Build img2pdf layout
        # "fit" => page size equals image size (no margins). Otherwise use given page size.
        layout_fun = None
        if page_size.lower() != "fit":
            try:
                # Map fit_mode string to img2pdf.FitMode enum
                fit_mode_map = {
                    "into": img2pdf.FitMode.into,
                    "fill": img2pdf.FitMode.fill,
                    "exact": img2pdf.FitMode.exact,
                    "shrink": img2pdf.FitMode.shrink,
                    "enlarge": img2pdf.FitMode.enlarge
                }

                if fit_mode.lower() not in fit_mode_map:
                    raise ValueError(f"Invalid fit_mode: {fit_mode}")

                # Map common page sizes to point values (img2pdf uses points)
                page_size_map = {
                    "A4": (595.276, 841.890),  # A4 in points
                    "Letter": (612, 792),      # US Letter in points
                    "Legal": (612, 1008),      # US Legal in points
                    "A4^T": (841.890, 595.276)  # A4 landscape
                }

                if page_size in page_size_map:
                    pagesize_value = page_size_map[page_size]
                elif page_size.upper() in page_size_map:
                    pagesize_value = page_size_map[page_size.upper()]
                else:
                    # For custom sizes like "210mmx297mm", convert to points
                    # 1mm = 2.834645669 points
                    if 'mm' in page_size.lower() and 'x' in page_size.lower():
                        try:
                            dims = page_size.lower().replace('mm', '').split('x')
                            width_mm, height_mm = float(dims[0]), float(dims[1])
                            pagesize_value = (width_mm * 2.834645669, height_mm * 2.834645669)
                        except:
                            raise ValueError(f"Invalid custom page size format: {page_size}")
                    else:
                        raise ValueError(f"Unsupported page size: {page_size}")

                layout_fun = img2pdf.get_layout_fun(
                    pagesize=pagesize_value,
                    fit=fit_mode_map[fit_mode.lower()]
                )
            except (ValueError, KeyError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid page_size '{page_size}' or fit_mode '{fit_mode}': {str(e)}"
                )

        # 3) Convert (auto-orient uses EXIF to match page orientation)
        try:
            logger.info(f"Converting {len(rgb_bytes_list)} images to PDF with layout_fun={layout_fun}")

            # Call img2pdf.convert with or without layout_fun
            if layout_fun is not None:
                pdf_bytes = img2pdf.convert(
                    rgb_bytes_list,
                    layout_fun=layout_fun,
                    auto_orient=True
                )
            else:
                # For "fit" page size, use default behavior (image-sized pages)
                pdf_bytes = img2pdf.convert(
                    rgb_bytes_list,
                    auto_orient=True
                )

            logger.info(f"PDF conversion successful, size: {len(pdf_bytes)} bytes")
        except Exception as e:
            logger.error(f"PDF conversion error: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF conversion failed: {str(e)}"
            )

        processing_time = time.time() - start_time

        # Update stats
        stats.pdf_conversion_successful += 1
        stats.total_images_converted += len(files)
        stats.total_pdf_processing_time += processing_time

        # 4) Stream back the PDF
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'inline; filename="id-document.pdf"',
                "X-Processing-Time": str(processing_time),
                "X-Total-Images": str(len(files)),
                "X-Output-Size": str(len(pdf_bytes))
            }
        )

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

@app.post("/test-pdf-conversion", tags=["Testing"])
async def test_pdf_conversion():
    """
    Test the PDF conversion functionality with various scenarios

    This endpoint runs automated tests to verify:
    - Alpha channel handling (transparency removal)
    - Different page sizes and fit modes
    - Multi-page PDF generation
    - Error handling for invalid parameters

    Returns:
    - Comprehensive test results with success/failure status for each scenario
    """
    from PIL import Image, ImageDraw
    import tempfile
    import os

    test_results = {
        "test_summary": {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "test_timestamp": datetime.now().isoformat()
        },
        "test_cases": []
    }

    # Helper function to create test images
    def create_test_image(width=400, height=300, mode='RGB', bg_color=(255, 255, 255), has_alpha=False):
        if has_alpha and mode == 'RGB':
            mode = 'RGBA'
            bg_color = bg_color + (0,) if len(bg_color) == 3 else bg_color

        img = Image.new(mode, (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        # Draw some content
        draw.rectangle([50, 50, width-50, height-50],
                      fill=(100, 150, 200, 255) if has_alpha else (100, 150, 200),
                      outline=(0, 0, 0, 255) if has_alpha else (0, 0, 0),
                      width=3)
        draw.text((width//4, height//2-10), "TEST", fill=(255, 255, 255, 255) if has_alpha else (255, 255, 255))

        return img

    # Helper function to run a test case
    async def run_test_case(name, description, test_func):
        test_results["test_summary"]["total_tests"] += 1
        test_case = {
            "name": name,
            "description": description,
            "status": "failed",
            "error": None,
            "details": {}
        }

        try:
            result = await test_func()
            test_case["status"] = "passed"
            test_case["details"] = result
            test_results["test_summary"]["passed"] += 1
        except Exception as e:
            test_case["status"] = "failed"
            test_case["error"] = str(e)
            test_results["test_summary"]["failed"] += 1
            logger.error(f"Test case '{name}' failed: {str(e)}")

        test_results["test_cases"].append(test_case)

    # Test Case 1: Basic RGB image with fit page size
    async def test_basic_rgb():
        img = create_test_image()
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img.save(tmp.name, 'JPEG')

            # Simulate the conversion process
            raw = open(tmp.name, 'rb').read()
            pil_img = Image.open(io.BytesIO(raw))
            flattened = _flatten_alpha_to_rgb(pil_img)

            buf = io.BytesIO()
            flattened.save(buf, format="JPEG", quality=95)
            pdf_bytes = img2pdf.convert([buf.getvalue()], auto_orient=True)

            os.unlink(tmp.name)

            return {
                "input_mode": img.mode,
                "output_mode": flattened.mode,
                "pdf_size_bytes": len(pdf_bytes),
                "alpha_handled": flattened.mode == 'RGB'
            }

    # Test Case 2: PNG with alpha channel
    async def test_alpha_channel():
        img = create_test_image(mode='RGBA', bg_color=(0, 0, 0, 0), has_alpha=True)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name, 'PNG')

            raw = open(tmp.name, 'rb').read()
            pil_img = Image.open(io.BytesIO(raw))
            flattened = _flatten_alpha_to_rgb(pil_img, (255, 255, 255))

            buf = io.BytesIO()
            flattened.save(buf, format="JPEG", quality=95)
            pdf_bytes = img2pdf.convert([buf.getvalue()], auto_orient=True)

            os.unlink(tmp.name)

            return {
                "input_mode": img.mode,
                "input_has_alpha": img.mode in ('RGBA', 'LA'),
                "output_mode": flattened.mode,
                "pdf_size_bytes": len(pdf_bytes),
                "alpha_removed": flattened.mode == 'RGB'
            }

    # Test Case 3: A4 page size with layout function
    async def test_a4_layout():
        img = create_test_image()
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img.save(tmp.name, 'JPEG')

            raw = open(tmp.name, 'rb').read()
            pil_img = Image.open(io.BytesIO(raw))
            flattened = _flatten_alpha_to_rgb(pil_img)

            buf = io.BytesIO()
            flattened.save(buf, format="JPEG", quality=95)

            # Test A4 layout function
            layout_fun = img2pdf.get_layout_fun(
                pagesize=(595.276, 841.890),  # A4 in points
                fit=img2pdf.FitMode.into
            )
            pdf_bytes = img2pdf.convert([buf.getvalue()], layout_fun=layout_fun, auto_orient=True)

            os.unlink(tmp.name)

            return {
                "page_size": "A4",
                "fit_mode": "into",
                "pdf_size_bytes": len(pdf_bytes),
                "layout_applied": True
            }

    # Test Case 4: Multi-page PDF
    async def test_multipage():
        images = [
            create_test_image(400, 300),
            create_test_image(300, 400),  # Different aspect ratio
            create_test_image(200, 200, has_alpha=True, mode='RGBA', bg_color=(0, 0, 0, 0))
        ]

        rgb_bytes_list = []
        temp_files = []

        try:
            for i, img in enumerate(images):
                tmp = tempfile.NamedTemporaryFile(suffix=f'_{i}.png', delete=False)
                img.save(tmp.name, 'PNG')
                temp_files.append(tmp.name)

                raw = open(tmp.name, 'rb').read()
                pil_img = Image.open(io.BytesIO(raw))
                flattened = _flatten_alpha_to_rgb(pil_img)

                buf = io.BytesIO()
                flattened.save(buf, format="JPEG", quality=95)
                rgb_bytes_list.append(buf.getvalue())

            pdf_bytes = img2pdf.convert(rgb_bytes_list, auto_orient=True)

            return {
                "input_images": len(images),
                "pdf_size_bytes": len(pdf_bytes),
                "multipage_success": len(rgb_bytes_list) == len(images)
            }
        finally:
            for tmp_file in temp_files:
                if os.path.exists(tmp_file):
                    os.unlink(tmp_file)

    # Run all test cases
    await run_test_case(
        "basic_rgb_conversion",
        "Test basic RGB image conversion with fit page size",
        test_basic_rgb
    )

    await run_test_case(
        "alpha_channel_handling",
        "Test PNG with alpha channel transparency removal",
        test_alpha_channel
    )

    await run_test_case(
        "a4_page_layout",
        "Test A4 page size with into fit mode",
        test_a4_layout
    )

    await run_test_case(
        "multipage_pdf",
        "Test multi-page PDF generation with mixed image types",
        test_multipage
    )

    # Calculate success rate
    total = test_results["test_summary"]["total_tests"]
    passed = test_results["test_summary"]["passed"]
    test_results["test_summary"]["success_rate"] = f"{(passed/total*100):.1f}%" if total > 0 else "0%"

    return test_results

if __name__ == "__main__":
    # Run the API server
    uvicorn.run(
        "api_service:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=bool(os.getenv("DEV_RELOAD", "")),
        log_level="info"
    )
