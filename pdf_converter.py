#!/usr/bin/env python3
"""
PDF Converter Module
Converts images of various formats to PDF documents
"""

import os
import tempfile
import logging
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image, ImageOps
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4, legal
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader

# Configure logging
logger = logging.getLogger(__name__)

class PDFConverter:
    """
    A class for converting images to PDF format with various configuration options
    """
    
    # Supported image formats
    SUPPORTED_FORMATS = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'
    }
    
    # Page size configurations (width, height in points)
    PAGE_SIZES = {
        'A4': A4,
        'Letter': letter,
        'Legal': legal
    }
    
    # Maximum file size (10MB per image)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self):
        """Initialize the PDF converter"""
        pass
    
    def validate_image_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate an image file for PDF conversion
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary with validation results
            
        Raises:
            ValueError: If file is invalid
        """
        if not os.path.exists(file_path):
            raise ValueError(f"File does not exist: {file_path}")
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large: {file_size / (1024*1024):.1f}MB (max: {self.MAX_FILE_SIZE / (1024*1024)}MB)")
        
        if file_size == 0:
            raise ValueError("File is empty")
        
        # Check file extension
        _, ext = os.path.splitext(file_path.lower())
        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {ext}. Supported: {', '.join(self.SUPPORTED_FORMATS)}")
        
        # Try to open and validate the image
        try:
            with Image.open(file_path) as img:
                # Verify image can be loaded
                img.verify()
                
                # Reopen for getting info (verify() closes the image)
                with Image.open(file_path) as img_info:
                    width, height = img_info.size
                    mode = img_info.mode
                    format_name = img_info.format

                    return {
                        'valid': True,
                        'width': width,
                        'height': height,
                        'mode': mode,
                        'format': format_name,
                        'file_size': file_size
                    }
                    
        except Exception as e:
            raise ValueError(f"Invalid or corrupted image file: {str(e)}")
    
    def calculate_image_dimensions(self, img_width: int, img_height: int, 
                                 page_size: Tuple[float, float], 
                                 fit_mode: str = 'fit') -> Tuple[float, float, float, float]:
        """
        Calculate optimal image dimensions and position on PDF page
        
        Args:
            img_width: Original image width
            img_height: Original image height
            page_size: Page size tuple (width, height)
            fit_mode: 'fit' (maintain aspect ratio) or 'fill' (stretch to fill)
            
        Returns:
            Tuple of (x, y, width, height) for image placement
        """
        page_width, page_height = page_size
        
        # Leave margins (0.5 inch on each side)
        margin = 0.5 * inch
        available_width = page_width - (2 * margin)
        available_height = page_height - (2 * margin)
        
        if fit_mode == 'fill':
            # Stretch to fill available space
            new_width = available_width
            new_height = available_height
        else:  # fit mode - maintain aspect ratio
            # Calculate scaling factor to fit within available space
            width_scale = available_width / img_width
            height_scale = available_height / img_height
            scale = min(width_scale, height_scale)
            
            new_width = img_width * scale
            new_height = img_height * scale
        
        # Center the image on the page
        x = (page_width - new_width) / 2
        y = (page_height - new_height) / 2
        
        return x, y, new_width, new_height
    
    def convert_single_image_to_pdf(self, image_path: str, output_path: str,
                                  page_size: str = 'A4', fit_mode: str = 'fit') -> Dict[str, Any]:
        """
        Convert a single image to PDF
        
        Args:
            image_path: Path to input image
            output_path: Path for output PDF
            page_size: Page size ('A4', 'Letter', 'Legal')
            fit_mode: How to fit image ('fit' or 'fill')
            
        Returns:
            Dictionary with conversion results
        """
        start_time = time.time()
        
        try:
            # Validate input
            validation_result = self.validate_image_file(image_path)
            
            if page_size not in self.PAGE_SIZES:
                raise ValueError(f"Unsupported page size: {page_size}. Supported: {', '.join(self.PAGE_SIZES.keys())}")
            
            page_dimensions = self.PAGE_SIZES[page_size]
            
            # Create PDF
            c = canvas.Canvas(output_path, pagesize=page_dimensions)
            
            # Open and process image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (for JPEG compatibility)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparent images
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate dimensions and position
                x, y, width, height = self.calculate_image_dimensions(
                    img.width, img.height, page_dimensions, fit_mode
                )
                
                # Create ImageReader object for reportlab
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='JPEG', quality=95)
                img_buffer.seek(0)
                img_reader = ImageReader(img_buffer)
                
                # Draw image on PDF
                c.drawImage(img_reader, x, y, width=width, height=height)
                
            # Save PDF
            c.save()
            
            processing_time = time.time() - start_time
            output_size = os.path.getsize(output_path)

            return {
                'success': True,
                'input_file': image_path,
                'output_file': output_path,
                'processing_time': processing_time,
                'input_size': validation_result['file_size'],
                'output_size': output_size,
                'page_size': page_size,
                'fit_mode': fit_mode,
                'image_info': validation_result
            }
            
        except Exception as e:
            logger.error(f"PDF conversion failed: {str(e)}")
            raise
    
    def convert_multiple_images_to_pdf(self, image_paths: List[str], output_path: str,
                                     page_size: str = 'A4', fit_mode: str = 'fit') -> Dict[str, Any]:
        """
        Convert multiple images to a single PDF with multiple pages
        
        Args:
            image_paths: List of paths to input images
            output_path: Path for output PDF
            page_size: Page size ('A4', 'Letter', 'Legal')
            fit_mode: How to fit images ('fit' or 'fill')
            
        Returns:
            Dictionary with conversion results
        """
        start_time = time.time()
        
        try:
            if not image_paths:
                raise ValueError("No image paths provided")
            
            if page_size not in self.PAGE_SIZES:
                raise ValueError(f"Unsupported page size: {page_size}. Supported: {', '.join(self.PAGE_SIZES.keys())}")
            
            page_dimensions = self.PAGE_SIZES[page_size]
            
            # Validate all images first
            validation_results = []
            total_input_size = 0
            
            for image_path in image_paths:
                validation_result = self.validate_image_file(image_path)
                validation_results.append(validation_result)
                total_input_size += validation_result['file_size']
            
            # Create PDF with multiple pages
            c = canvas.Canvas(output_path, pagesize=page_dimensions)
            
            processed_images = []
            
            for i, (image_path, validation_result) in enumerate(zip(image_paths, validation_results)):
                try:
                    # Open and process image
                    with Image.open(image_path) as img:
                        # Convert to RGB if necessary
                        if img.mode in ('RGBA', 'LA', 'P'):
                            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                            img = rgb_img
                        elif img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # Calculate dimensions and position
                        x, y, width, height = self.calculate_image_dimensions(
                            img.width, img.height, page_dimensions, fit_mode
                        )
                        
                        # Create ImageReader object
                        img_buffer = io.BytesIO()
                        img.save(img_buffer, format='JPEG', quality=95)
                        img_buffer.seek(0)
                        img_reader = ImageReader(img_buffer)
                        
                        # Draw image on current page
                        c.drawImage(img_reader, x, y, width=width, height=height)
                        
                        processed_images.append({
                            'path': image_path,
                            'success': True,
                            'page_number': i + 1
                        })
                        
                        # Add new page if not the last image
                        if i < len(image_paths) - 1:
                            c.showPage()
                            
                except Exception as e:
                    logger.error(f"Failed to process image {image_path}: {str(e)}")
                    processed_images.append({
                        'path': image_path,
                        'success': False,
                        'error': str(e),
                        'page_number': None
                    })
                    
                    # Still add a page for consistency, but with error message
                    c.drawString(100, 400, f"Error processing image: {os.path.basename(image_path)}")
                    c.drawString(100, 380, f"Error: {str(e)}")
                    
                    if i < len(image_paths) - 1:
                        c.showPage()
            
            # Save PDF
            c.save()
            
            processing_time = time.time() - start_time
            output_size = os.path.getsize(output_path)
            
            successful_images = [img for img in processed_images if img['success']]
            failed_images = [img for img in processed_images if not img['success']]

            return {
                'success': len(failed_images) == 0,
                'partial_success': len(successful_images) > 0 and len(failed_images) > 0,
                'output_file': output_path,
                'processing_time': processing_time,
                'total_input_size': total_input_size,
                'output_size': output_size,
                'page_size': page_size,
                'fit_mode': fit_mode,
                'total_images': len(image_paths),
                'successful_images': len(successful_images),
                'failed_images': len(failed_images),
                'processed_images': processed_images
            }
            
        except Exception as e:
            logger.error(f"Multi-image PDF conversion failed: {str(e)}")
            raise

# Import time for timing measurements
import time
