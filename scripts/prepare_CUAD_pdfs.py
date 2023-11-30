#!/usr/bin/env python3
import os
import zipfile
import shutil

import requests
import tqdm
import fitz  # PyMuPDF

CUAD_URL = "https://zenodo.org/records/4595826/files/CUAD_v1.zip"
ZIP_DOWNLOAD_PATH = "CUAD_v1.zip"
UNZIP_DIR = "CUAD_v1"
RASTER_DIR = "CUAD_v1_rasterized"
RASTER_DPI = 80 / 72


def download_and_unzip():
    if not os.path.exists(ZIP_DOWNLOAD_PATH):
        response = requests.get(CUAD_URL, stream=True)
        with open(ZIP_DOWNLOAD_PATH, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)

    # Extract the zip file
    with zipfile.ZipFile(ZIP_DOWNLOAD_PATH, "r") as cuad_zip:
        cuad_zip.extractall(UNZIP_DIR)


def find_pdfs_in_directory(dir_with_pdfs: str) -> dict[int, str]:
    pdf_dict = {}
    for root, _, files in os.walk(dir_with_pdfs):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                index = len(pdf_dict)
                pdf_dict[index] = pdf_path

    return pdf_dict


def rasterize_pdf_pages_to_images(pdf_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        image = page.get_pixmap(matrix=fitz.Matrix(RASTER_DPI, RASTER_DPI))
        image_path = os.path.join(output_dir, f"{page_num:05}.png")
        image.save(image_path)


def rasterize_all_pdfs(pdf_dict: dict[str, int]):
    for idx, pdf_path in tqdm.tqdm(pdf_dict.items()):
        output_dir = os.path.join(RASTER_DIR, f"{idx:05}")
        rasterize_pdf_pages_to_images(pdf_path, output_dir)


def main():
    download_and_unzip()
    print("downloaded zip")
    pdf_dict = find_pdfs_in_directory(UNZIP_DIR)
    print("pdf_dict:", pdf_dict)
    # TODO: exclude undesired PDFs, if any. E.g. ones without signatures.
    rasterize_all_pdfs(pdf_dict)
    print("cleaning up files")
    clean_up_files()


def clean_up_files():
    shutil.rmtree(UNZIP_DIR, ignore_errors=True)
    os.remove(ZIP_DOWNLOAD_PATH)


if __name__ == "__main__":
    main()
