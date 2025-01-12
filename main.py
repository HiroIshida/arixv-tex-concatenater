#!/usr/bin/env python3

import requests
import os
import re
import tarfile
import zipfile
import tempfile
import shutil
import sys

def download_arxiv_source(arxiv_url, outdir):
    """
    Download the source from the given arXiv URL and save it into 'outdir'.
    Return the local path of the downloaded file.
    """
    print(f"Downloading from: {arxiv_url}")
    local_filename = os.path.join(outdir, "arxiv_source")
    r = requests.get(arxiv_url, stream=True)
    r.raise_for_status()
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    return local_filename

def extract_archive(archive_path, extract_to):
    """
    Detect the file type (.tar.gz, .tar, .zip, etc.) and extract it into 'extract_to'.
    """
    # Try to guess the type from the extension first.
    # arXiv often provides tar or tar.gz archives, 
    # but we handle zip as well just in case.
    if archive_path.endswith(".tar.gz") or archive_path.endswith(".tgz"):
        with tarfile.open(archive_path, 'r:gz') as tf:
            tf.extractall(path=extract_to)
    elif archive_path.endswith(".tar"):
        with tarfile.open(archive_path, 'r:') as tf:
            tf.extractall(path=extract_to)
    elif archive_path.endswith(".zip"):
        with zipfile.ZipFile(archive_path, 'r') as zf:
            zf.extractall(path=extract_to)
    else:
        # If no extension or something else, 
        # try opening as a tar and if that fails, try as a zip
        try:
            with tarfile.open(archive_path, 'r:*') as tf:
                tf.extractall(path=extract_to)
        except tarfile.ReadError:
            try:
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    zf.extractall(path=extract_to)
            except zipfile.BadZipFile:
                raise ValueError("Unknown file format or broken archive.")

def find_main_texfile(root_dir):
    """
    Search all .tex files under 'root_dir'.

    1) If there is a file named 'main.tex', return it immediately.
    2) Otherwise, look for the first file containing '\\begin{document}' and return that.
    3) If none is found, return the first .tex file found (fallback).
    4) If no .tex files are found, return None.
    """
    tex_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for fn in filenames:
            if fn.lower().endswith(".tex"):
                full_path = os.path.join(dirpath, fn)
                tex_files.append(full_path)

    # 1) main.tex
    for f in tex_files:
        if os.path.basename(f).lower() == "main.tex":
            return f

    # 2) look for a file containing \begin{document}
    for f in tex_files:
        with open(f, 'r', encoding="utf-8", errors="ignore") as fp:
            content = fp.read()
            if r"\begin{document}" in content:
                return f

    # 3) fallback to the first .tex if anything exists
    if tex_files:
        return tex_files[0]

    return None

def parse_includes(tex_content):
    """
    Parse the content of a .tex file to find any referenced files via
    \\input or \\include. This function handles both:
      - Bracketed syntax: \\input{myfile} or \\include{myfile}
      - Space-separated syntax: \\input myfile or \\include myfile

    Return a list of the file paths (as written, possibly missing '.tex').
    """
    include_files = []

    # Go line by line. If a '%' symbol appears, everything after it is treated as a comment.
    lines = tex_content.splitlines()
    for line in lines:
        # Strip leading/trailing whitespace
        stripped_line = line.strip()
        # If there's a comment, cut it off at the first '%'
        if '%' in stripped_line:
            comment_index = stripped_line.index('%')
            stripped_line = stripped_line[:comment_index]

        # Pattern for bracketed syntax: \input{file} or \include{file}
        # capturing group is what's inside the braces.
        pattern_brackets = r'\\(?:include|input)\{([^}]*)\}'

        # Pattern for space-separated syntax: \input file or \include file
        # capturing group is the filename right after the command.
        pattern_space = r'\\(?:include|input)\s+([^\s]+)'

        # Find all bracketed references
        matches_bracketed = re.findall(pattern_brackets, stripped_line)
        # Find all space-separated references
        matches_space = re.findall(pattern_space, stripped_line)

        # Combine both
        for m in matches_bracketed:
            include_files.append(m)
        for m in matches_space:
            include_files.append(m)

    return include_files

def resolve_includes(root_tex_path, visited=None):
    """
    Recursively follow \input / \include references starting from 'root_tex_path'.
    Return a list of absolute .tex file paths in the order they should be concatenated.

    'visited' is used to avoid infinite loops if there's a recursive reference.
    """
    if visited is None:
        visited = set()

    results = []
    abspath = os.path.abspath(root_tex_path)

    if abspath in visited:
        return results  # prevent infinite loop

    visited.add(abspath)

    # Add the current file to the result list first
    results.append(abspath)

    # Read the content
    with open(abspath, 'r', encoding='utf-8', errors='ignore') as fp:
        content = fp.read()

    # Parse for includes/inputs
    includes = parse_includes(content)
    base_dir = os.path.dirname(abspath)

    # Resolve each included file
    for inc in includes:
        # inc could be like "chapter1", "chapter1.tex", "sections/chapter1", etc.
        candidates = []
        if inc.lower().endswith(".tex"):
            # If there's already .tex, just keep it
            candidates.append(os.path.join(base_dir, inc))
        else:
            # Otherwise, try inc + ".tex" and also inc (in case it has some extension)
            candidates.append(os.path.join(base_dir, inc + ".tex"))
            candidates.append(os.path.join(base_dir, inc))

        found_path = None
        for c in candidates:
            if os.path.isfile(c):
                found_path = c
                break

        if found_path:
            # Recursively resolve includes in that file
            results.extend(resolve_includes(found_path, visited))

    return results

def main(arxiv_url):

    # Create a temporary directory for the download and extraction
    tmpdir = tempfile.mkdtemp(prefix="arxiv_")
    try:
        # 1) Download
        archive_path = download_arxiv_source(arxiv_url, tmpdir)

        # 2) Extract
        extract_archive(archive_path, tmpdir)

        # 3) Find the main (root) tex file
        root_tex = find_main_texfile(tmpdir)
        if root_tex is None:
            print("No .tex file found. Aborting.")
            return

        print(f"Root .tex file found: {root_tex}")

        # 4) Resolve all included files in the correct order
        all_tex_files = resolve_includes(root_tex)
        print("Files to be concatenated in order:")
        for f in all_tex_files:
            print("  " + f)

        # 5) Concatenate everything into cat.txt
        cat_txt_path = os.path.join(tmpdir, "cat.txt")
        with open(cat_txt_path, "w", encoding="utf-8") as outfp:
            for texf in all_tex_files:
                with open(texf, "r", encoding="utf-8", errors="ignore") as infp:
                    outfp.write(f"% >>>>>>>> BEGIN {texf}\n")
                    outfp.write(infp.read())
                    outfp.write(f"\n% <<<<<<<< END {texf}\n\n")

        print(f"\nAll files have been concatenated into: {cat_txt_path}")
        print(f"(Located in: {tmpdir})")

        # If needed, you can move or copy 'cat.txt' elsewhere. 
        # By default, it's in the temporary directory which can be deleted.

    finally:
        # Uncomment if you want to automatically remove the temp directory after finishing.
        # shutil.rmtree(tmpdir, ignore_errors=True)
        pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <arxiv_url>")
        sys.exit(1)
    arxiv_url = sys.argv[1]
    is_latex_url = re.match(r"https://arxiv.org/e-print/\d{4}\.\d{5}", arxiv_url)
    if not is_latex_url:
        paper_id = arxiv_url.split("/")[-1]
        arxiv_url = f"https://arxiv.org/e-print/{paper_id}"
    main(arxiv_url)
