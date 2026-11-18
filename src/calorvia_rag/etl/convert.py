from calorvia_rag.config import settings
from calorvia_rag.db import start_run, end_run, insert_log, is_file_processed, list_files_to_convert

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions

from time import perf_counter

import hashlib

ALLOWED_INPUT_FORMAT = [
    InputFormat.PDF, InputFormat.DOCX, InputFormat.HTML, InputFormat.PPTX,
    InputFormat.MD, InputFormat.CSV, InputFormat.XLSX,
]

TRUNCATE_EXPORT_FOLDER = False

def get_converter(models_folder, device, num_threads):
    options = PdfPipelineOptions(
        artifacts_path = (models_folder / 'docling'),
        accelerator_options = AcceleratorOptions(
            device = device,
            num_threads = num_threads
        ),
        do_ocr = False,   # les scans sont écartés : pas besoin d'OCR
        generate_page_images = True
    )

    converter = DocumentConverter(
        allowed_formats = ALLOWED_INPUT_FORMAT,
        format_options= {
            InputFormat.PDF: PdfFormatOption(pipeline_options=options)
        }
    )

    return converter

def get_hash(file_path):
    return hashlib.sha256(file_path.read_bytes()).hexdigest()

def convert_file(file_path, converter, export_folder, file_hash):
    log = {
        'file_path': str(file_path.absolute().as_posix()),
        'export_folder': (export_folder.absolute().as_posix()),
        'file_name': file_path.name,
        'file_format_': file_path.suffix.lstrip('.'),
        'file_hash': file_hash,
        'status_': None,
        'page_count': None,
        'text_count': None,
        'table_count': None,
        'image_count': None,
        'process_time': None,
        'error': None
    }

    start = perf_counter()

    try:
        result = converter.convert(file_path)
        doc = result.document
        doc.save_as_json(export_folder / f'{file_hash}.json')
        doc.save_as_markdown(export_folder / f'{file_hash}.md')
        log.update(
            status_ = result.status.value,
            page_count = doc.num_pages(),
            text_count = len(doc.texts),
            table_count = len(doc.tables),
            image_count =  len(doc.pictures),
        )
    except Exception as e:
        log.update(status_='failure', error=f'{type(e).__name__}: {e}')
    finally:
        log.update(process_time = perf_counter() - start)

    return log

def convert_corpus():
    converter = get_converter(
        settings.models_folder,
        settings.ocr_device,
        settings.ocr_num_threads,
    )

    conversion_parameters = {
        'device': settings.ocr_device,
        'threads': settings.ocr_num_threads,
        'allowed_formats': ','.join(f.value for f in ALLOWED_INPUT_FORMAT),
        'do_ocr': False

    }

    run_id = start_run(conversion_parameters)

    files = list_files_to_convert()

    settings.processed_documents_folder.mkdir(exist_ok = True)

    run_logs = []

    doc_processed = doc_ignored = doc_failed = 0

    try:
        for relative_path, file_hash in files:
            file_path = settings.corpus_folder / relative_path
            if not is_file_processed(file_path, file_hash):
                log = convert_file(file_path, converter, settings.processed_documents_folder, file_hash)
                doc_processed += 1

                insert_log(run_id, log)

                run_logs.append(log)

                if log.get('status_') == 'failure':
                    doc_failed += 1
            else:
                doc_ignored += 1
    finally:
        end_run(run_id, doc_processed, doc_ignored, doc_failed)

if __name__ == '__main__':
    convert_corpus()
