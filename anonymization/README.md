# Anonymization

This tool takes in a directory of submitted exams (fighting with the scanner is something best talked about offline, but maybe some quick notes below), and will rename them to a random number and then redact the name (assuming the name field is in the same location every time).
This will prep the exam for grading in a digital way and reduce bias as much as possible (hopefully).

## Usage

`python split_and_redact.py --input_dir sample_input`

## Notes about scanners

Our scanner on campus has two weird things about it:
1. You can only scan up to ~35 pages in one go before it runs out of memory
2. It will automatically remove blank pages, so if some pages are blank sometimes the splitting function won't work as expected.

Based on this I recommend breaking exams up into some set that results in pages of less than 35 and then splitting manually.
I use preview and it goes reasonable well.