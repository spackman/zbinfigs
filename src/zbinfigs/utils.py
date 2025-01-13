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
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
from PyPDF2 import PdfMerger, PdfReader
import glob



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

def _get_pdf_page_count(pdf_path: str) -> int:
    """
    Retrieves the total number of pages in a PDF file using PdfReader.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        int: The total number of pages in the PDF.
    """
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            return len(reader.pages)  # Returns the number of pages
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return 0  # Return 0 if there's an error (e.g., file not found or invalid)

def _save_page_ranges_to_csv(image_indices: dict, file_range: Tuple[int, int], pdfs_folder: str) -> None:
    """
    Saves the image page ranges to a CSV file, including the total number of pages in the corresponding PDF.

    Args:
        image_indices (dict): Dictionary containing image page ranges.
        file_range (Tuple[int, int]): The range of files (start, end).
        pdfs_folder (str): The folder containing the PDFs.
    """
    page_ranges = []

    for folder, (start, end) in image_indices.items():
        # Use glob to find the PDF file that starts with 'folder' and ends with '.pdf'
        pdf_files = glob.glob(os.path.join(pdfs_folder, f"{folder}*.pdf"))
        
        if pdf_files:
            # Take the first match (assuming there is only one match)
            pdf_path = pdf_files[0]
            total_pages = _get_pdf_page_count(pdf_path)
            
            page_ranges.append({
                'file': folder,
                'start': start,
                'end': end,
                'total_pages': total_pages
            })
        else:
            print(f"No PDF found for folder: {folder}")
            page_ranges.append({
                'file': folder,
                'start': start,
                'end': end,
                'total_pages': 0  # If no PDF is found, mark as 0 pages
            })
    
    # Create the DataFrame and save to CSV
    df = pd.DataFrame(page_ranges)
    output_csv = os.path.join(pdfs_folder, f"gathered_figures_{file_range[0]}_{file_range[1]}.csv")
    df.to_csv(output_csv, index=False)

def _create_pdf_from_images(image_paths: List[str], file_range: Tuple[int, int], pdfs_folder: str) -> None:
    """
    Creates a PDF from a list of image file paths, where each page is the size of the corresponding image.

    Args:
        image_paths (List[str]): List of image file paths to be included in the PDF.
        file_range (Tuple[int, int]): Range of the images (for naming the output file).
        pdfs_folder (str): The folder where the generated PDF should be saved.
    """
    output_pdf = os.path.join(pdfs_folder, f"gathered_figures_{file_range[0]}_{file_range[1]}.pdf")
    
    c = canvas.Canvas(output_pdf)

    for image_path in image_paths:
        img = Image.open(image_path)
        img_width, img_height = img.size
        
        # Convert image dimensions to points (1 inch = 72 points)
        img_width_pts = img_width * 72 / img.info.get('dpi', (72, 72))[0]
        img_height_pts = img_height * 72 / img.info.get('dpi', (72, 72))[1]
        
        c.setPageSize((img_width_pts, img_height_pts))
        c.drawImage(image_path, 0, 0, img_width_pts, img_height_pts)
        c.showPage()

    c.save()


def _collect_pdf_and_csv_paths(pdfs_folder: str) -> Tuple[List[str], List[str]]:
    """
    Collects the paths to all PDF and CSV files in the specified folder.

    Args:
        pdfs_folder (str): The folder containing the PDF and CSV files.

    Returns:
        Tuple[List[str], List[str]]: Lists of paths to PDF and CSV files.
    """
    pdf_paths = []
    csv_paths = []

    for file in os.listdir(pdfs_folder):
        pdf_file_path = os.path.join(pdfs_folder, file)
        csv_file_path = os.path.join(pdfs_folder, file).split(".")[0] + ".csv"
        if file.endswith(".pdf") and os.path.exists(csv_file_path) and "gathered_figures" in file:
            pdf_paths.append(pdf_file_path)
            csv_paths.append(csv_file_path)
    
    return pdf_paths, csv_paths

def _merge_pdfs(pdf_paths: List[str], output_pdf: str) -> None:
    """
    Merges multiple PDF files into a single PDF document.

    Args:
        pdf_paths (List[str]): List of paths to the PDF files to be merged.
        output_pdf (str): Path to the output merged PDF file.
    """
    pdf_merger = PdfMerger()

    for pdf_path in tqdm(pdf_paths, desc="Merging PDFs", unit="file"):
        pdf_merger.append(pdf_path)

    pdf_merger.write(output_pdf)
    pdf_merger.close()

def _update_page_ranges_for_csv(csv_path: str, current_page_count: int) -> pd.DataFrame:
    """
    Updates the page range information in the CSV based on the current page count.

    Args:
        csv_path (str): Path to the CSV file containing the page ranges.
        current_page_count (int): The current total page count to update the CSV ranges.

    Returns:
        pd.DataFrame: The updated DataFrame with new page ranges.
    """
    df = pd.read_csv(csv_path)
    
    # Update 'start' and 'end' columns based on the current page count
    df['start'] += current_page_count
    df['end'] += current_page_count
    
    return df

def _merge_csvs(csv_paths: List[str], output_csv: str) -> None:
    """
    Merges multiple CSV files into a single CSV file and updates the page ranges.

    Args:
        csv_paths (List[str]): List of paths to the CSV files to be merged.
        output_csv (str): Path to the output merged CSV file.
    """
    combined_df = pd.DataFrame()
    current_page_count = 0

    for csv_path in tqdm(csv_paths, desc="Merging CSVs", unit="file"):
        updated_df = _update_page_ranges_for_csv(csv_path, current_page_count)
        
        # Add the source CSV file name to the dataframe
        updated_df['gathered_file'] = os.path.basename(csv_path).split(".")[0]
        
        combined_df = pd.concat([combined_df, updated_df], ignore_index=True)
        
        # Update the page count
        current_page_count += updated_df.iloc[-1]['end']

    combined_df.to_csv(output_csv, index=False)

def merge_summary_pdfs(pdfs_folder: str) -> None:
    """
    Merges all PDFs in the specified folder and updates the corresponding CSV metadata.
    
    Args:
        pdfs_folder (str): The folder containing the PDFs and CSV files to be merged.
    """
    # Collect PDF and CSV paths
    pdf_paths, csv_paths = _collect_pdf_and_csv_paths(pdfs_folder)

    # Define the output file paths
    merged_pdf_path = os.path.join(pdfs_folder, "figure_summary.pdf")
    combined_csv_path = os.path.join(pdfs_folder, "figure_summary.csv")

    # Merge the PDFs
    _merge_pdfs(pdf_paths, merged_pdf_path)

    # Merge the CSVs and update page ranges
    _merge_csvs(csv_paths, combined_csv_path)

    print(f"Merged PDF saved as: {merged_pdf_path}")
    print(f"Updated CSV saved as: {combined_csv_path}")

def sort_annotated():
    # locate the images based on their annotations and sort into 
    # folders accordingly - rename the figures to avoid name clashes
    return

def add_annotations():
    # add annotations to the main .csv file
    return
