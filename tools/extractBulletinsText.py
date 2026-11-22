import os
import PyPDF2
import docx2txt
import concurrent.futures
from tqdm import tqdm

def convert_pdf(input_path):
    with open(input_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        return '\n\n'.join(page.extract_text() for page in pdf_reader.pages if page.extract_text())

def convert_docx(input_path):
    return docx2txt.process(input_path)

def convert_txt(input_path):
    with open(input_path, 'r', encoding='utf-8') as src_file:
        return src_file.read()

def convert_file(args):
    input_path, output_path = args
    converters = {
        '.pdf': convert_pdf,
        '.docx': convert_docx,
        '.txt': convert_txt
    }

    ext = os.path.splitext(input_path)[1].lower()
    if ext in converters:
        try:
            text = converters[ext](input_path)
            with open(output_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(text)
        except Exception as e:
            print(f"Error converting {input_path}: {e}")

def convert_to_txt(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    files_to_convert = [
        (os.path.join(input_dir, filename), os.path.join(output_dir, os.path.splitext(filename)[0] + ".txt"))
        for filename in os.listdir(input_dir)
        if not os.path.exists(os.path.join(output_dir, os.path.splitext(filename)[0] + ".txt"))
    ]

    with concurrent.futures.ProcessPoolExecutor() as executor:
        list(tqdm(executor.map(convert_file, files_to_convert),
                  total=len(files_to_convert),
                  desc="Converting files",
                  unit="file"))

if __name__ == "__main__":
    input_directory = "bulletins/2024"
    output_directory = "bulletins-analysis/txt"
    convert_to_txt(input_directory, output_directory)