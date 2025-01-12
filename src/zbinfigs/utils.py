"""
-----------------------------------------------------------------------------
Module Name: zbinfigs
Submodule Name: utils.py
Description: Utility functions for pdf analysis and file management.
Author: Isaac Spackman
Date Created: December 8, 2024
Last Modified: December 8, 2024
Version: 0.0.0
License: MIT
-----------------------------------------------------------------------------
"""

import shutil
import os
import pandas as pd
import logging
from .collection import *
from typing import Tuple, List
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from tqdm import tqdm
from fpdf import FPDF
from PIL import Image
import io


def read_collection(csvfile: str) -> Collection:
    return Collection(csvfile)

def process_pdf_folder(pdfs_folder: str, file_range: Tuple[int, int]) -> None:
    """
    Processes PDF files in the given folder, converts them to Markdown, and extracts images.
    
    Args:
        pdfs_folder (str): The folder containing the PDF files to be processed.
        file_range (Tuple[int, int]): The range of files (inclusive) to process (start, end).
    """
    # Initialize logging
    _initialize_logger()

    # Get the list of valid PDF files
    pdf_files = _get_valid_pdf_files(pdfs_folder)
    if not pdf_files:
        logger.warning("No valid PDF files found in the folder.")
        return

    # Select the range of files to process
    selected_files = _select_files_in_range(pdf_files, file_range)
    if not selected_files:
        logger.warning(f"No files selected in the specified range: {file_range}")
        return

    # Create the converter object for processing
    converter = PdfConverter(artifact_dict=create_model_dict())

    # Process each selected file
    for file in tqdm(selected_files, desc="Processing PDFs", unit="file"):
        try:
            logger.info(f"Processing file: {file}")
            _process_single_pdf(file, converter, pdfs_folder, logger)
        except Exception as e:
            logger.error(f"Error processing {file}: {e}")

def _initialize_logger() -> logging.Logger:
    """
    Initializes and returns the logger instance for use in the module.

    Returns:
        logging.Logger: The logger instance.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    return logging.getLogger(__name__)


def _get_valid_pdf_files(pdfs_folder: str) -> List[str]:
    """
    Retrieves a sorted list of valid PDF files in the specified folder.
    
    Args:
        pdfs_folder (str): The folder to search for PDF files.
    
    Returns:
        List[str]: A list of valid PDF file paths sorted by filename.
    """
    logger = logging.getLogger(__name__)
    files = [f for f in os.listdir(pdfs_folder) if _is_valid_pdf_filename(f)]
    
    if not files:
        logger.warning("No valid PDF files found in the folder.")
    
    # Sort files by name to ensure consistent processing
    return sorted(files)

def _is_valid_pdf_filename(filename: str) -> bool:
    """
    Checks if a filename starts with 8 alphanumeric characters and has the .pdf extension.
    
    Args:
        filename (str): The filename to check.
    
    Returns:
        bool: True if the filename matches the expected pattern, False otherwise.
    """
    return filename[:8].isalnum() and filename.endswith('.pdf')

def _select_files_in_range(files: List[str], file_range: Tuple[int, int]) -> List[str]:
    """
    Selects a subset of files based on the provided range (inclusive).
    
    Args:
        files (List[str]): A list of files to select from.
        file_range (Tuple[int, int]): A tuple containing the start and end indices (inclusive).
    
    Returns:
        List[str]: A list of files selected by the range.
    """
    start, end = file_range
    if start < 0 or end >= len(files):
        raise ValueError(f"Invalid range: {file_range}, available files: 0 to {len(files)-1}")
    return files[start:end+1]

def _process_single_pdf(pdf_file: str, converter: PdfConverter, pdfs_folder: str, logger: logging.Logger) -> None:
    """
    Converts a single PDF to Markdown and saves the output in a folder named by the first 8 characters of the filename.
    
    Args:
        pdf_file (str): The path to the PDF file to process.
        converter (PdfConverter): The converter instance used to process the PDF.
        pdfs_folder (str): The folder where the PDF file is located.
        logger (logging.Logger): The logger instance to use for logging events.
    """
    # Get the first 8 characters of the filename to use as the folder name
    folder_name = pdf_file[:8]
    output_folder = os.path.join(pdfs_folder, folder_name)
    
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Process the PDF to get rendered text and images
    try:
        rendered = converter(os.path.join(pdfs_folder, pdf_file))
        text, _, images = text_from_rendered(rendered)

        # Save the original PDF
        shutil.copy(os.path.join(pdfs_folder, pdf_file), output_folder)

        # Save the Markdown text
        markdown_file = os.path.join(output_folder, f"{folder_name}.md")
        with open(markdown_file, 'w', encoding='utf-8') as md_file:
            md_file.write(text)

        # Save extracted images
        _save_extracted_images(images, output_folder)

        logger.info(f"Successfully processed and saved files for {pdf_file}.")

    except Exception as e:
        logger.error(f"Error processing PDF {pdf_file}: {e}")

def _save_extracted_images(images: List[str], output_folder: str) -> None:
    """
    Saves the extracted images to the output folder.
    
    Args:
        images (List[str]): A list of paths to the extracted images.
        output_folder (str): The folder where the images should be saved.
    """
    for img_name, img in images.items():
        try:
            img_path = os.path.join(output_folder, f"{os.path.basename(output_folder)}{img_name}")
            img.save(img_path)
        except Exception as e:
            logging.error(f"Error saving image: {e}")


def gather_figures(pdfs_folder: str, file_range: Tuple[int, int]) -> None:
    """
    Locates the image files for the PDFs in the specified range and merges them into a single PDF.
    Exports the page ranges for each record to a CSV file.

    Args:
        pdfs_folder (str): The folder containing the PDF files.
        file_range (Tuple[int, int]): The range of files to process (start, end).
    """
    # Initialize logging
    logger = _initialize_logger()

    # Get the list of valid PDF files
    pdf_files = _get_valid_pdf_files(pdfs_folder)
    if not pdf_files:
        logger.warning("No valid PDF files found in the folder.")
        return

    # Select the range of files to process
    selected_files = _select_files_in_range(pdf_files, file_range)
    if not selected_files:
        logger.warning(f"No files selected in the specified range: {file_range}")
        return
    
    # Process the selected files
    selected_folders = [os.path.join(pdfs_folder, file[:8]) for file in selected_files]
    logger.info(f"Processing folders: {selected_folders}")

    # Merge images and export page ranges
    try:
        _merge_images_to_pdf(selected_folders, pdfs_folder, file_range)
        logger.info("Successfully gathered figures into a single PDF and exported page ranges.")
    except Exception as e:
        logger.error(f"Error during figure gathering process: {e}")

def _merge_images_to_pdf(selected_folders: List[str], pdfs_folder: str, file_range: Tuple[int, int]) -> None:
    """
    Merges all images in the selected folders into a single PDF file.
    Writes the page ranges to a CSV file.

    Args:
        selected_folders (List[str]): List of folder paths containing images to merge.
        pdfs_folder (str): The folder containing the original PDFs.
        file_range (Tuple[int, int]): The range of files (start, end) to process.
    """
    image_paths, image_indices = _gather_images_from_folders(selected_folders)

    # Create PDF from gathered images
    _create_pdf_from_images(image_paths, file_range, pdfs_folder)

    # Save the page ranges to a CSV file
    _save_page_ranges_to_csv(image_indices, file_range, pdfs_folder)


def _gather_images_from_folders(selected_folders: List[str]) -> Tuple[List[str], dict]:
    """
    Gathers image file paths from the specified folders.

    Args:
        selected_folders (List[str]): List of folder paths to scan for image files.

    Returns:
        Tuple[List[str], dict]: A list of image file paths and a dictionary of page ranges by folder.
    """
    image_paths = []
    image_indices = {}
    
    for folder in tqdm(selected_folders, desc="Gathering PDF images", unit="folder"):
        folder_images = [f for f in os.listdir(folder) if f.endswith('.jpeg')]
        start = len(image_paths)
        end = len(image_paths) + len(folder_images)
        image_paths.extend([os.path.join(folder, f) for f in folder_images])
        image_indices[os.path.basename(folder)] = (start, end)
    
    return image_paths, image_indices

def _save_page_ranges_to_csv(image_indices: dict, file_range: Tuple[int, int], pdfs_folder: str) -> None:
    """
    Saves the image page ranges to a CSV file.

    Args:
        image_indices (dict): Dictionary containing image page ranges.
        file_range (Tuple[int, int]): The range of files (start, end).
        pdfs_folder (str): The folder containing the PDFs.
    """
    page_ranges = []
    for folder, (start, end) in image_indices.items():
        page_ranges.append({'file': folder, 'start': start, 'end': end})
    
    df = pd.DataFrame(page_ranges)
    output_csv = os.path.join(pdfs_folder, f"gathered_figures_{file_range[0]}_{file_range[1]}.csv")
    df.to_csv(output_csv, index=False)

def _create_pdf_from_images(image_paths: List[str], file_range: Tuple[int, int], pdfs_folder: str) -> None:
    """
    Creates a PDF from a list of image file paths.

    Args:
        image_paths (List[str]): List of image file paths to be included in the PDF.
    """
    pdf = FPDF()

    for image_path in image_paths:
        img = Image.open(image_path)
        img = img.convert('RGB')
        
        img_width, img_height = img.size
        dpi = img.info.get('dpi', (72, 72))  # Use 72 DPI if DPI is not found
        dpi_x, dpi_y = dpi
        
        img_width_inch = img_width / dpi_x
        img_height_inch = img_height / dpi_y
        img_width_mm = img_width_inch * 25.4
        img_height_mm = img_height_inch * 25.4
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        pdf.add_page()
        pdf.image(img_byte_arr, 0, 0, img_width_mm, img_height_mm)

    output_pdf = os.path.join(pdfs_folder, f"gathered_figures_{file_range[0]}_{file_range[1]}.pdf")
    pdf.output(output_pdf)


def merge_summary_pdfs():
    # merge pdfs into a single document and make an updated
    # page range metadata file
    return

def sort_annotated():
    # locate the images based on their annotations and sort into 
    # folders accordingly - rename the figures to avoid name clashes
    return

def add_annotations():
    # add annotations to the main .csv file
    return
