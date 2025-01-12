## arXiv tex concatenater
OpenAI o1 and o1-pro does not currently support pdf files for the input.
For the workaround, given the arXiv paper URL, this script concatenates the tex files from the arXiv paper into a single text (not tex!) file.

## Usage
```bash
python3 main.py https://arxiv.org/abs/2405.02968
```

output:
```
h-ishida@umejuice:~/python/arxiv-tex-concatenater$ python3 main.py https://arxiv.org/abs/2405.02968
Downloading from: https://arxiv.org/e-print/2405.02968

Root .tex file found: /home/h-ishida/.cache/arxiv_tex_concatenater/2405.02968/root.tex
Files to be concatenated in order:
  /home/h-ishida/.cache/arxiv_tex_concatenater/2405.02968/root.tex
  /home/h-ishida/.cache/arxiv_tex_concatenater/2405.02968/section/intro.tex
  /home/h-ishida/.cache/arxiv_tex_concatenater/2405.02968/section/formulation.tex
  /home/h-ishida/.cache/arxiv_tex_concatenater/2405.02968/section/method.tex
  /home/h-ishida/.cache/arxiv_tex_concatenater/2405.02968/section/setting.tex
  /home/h-ishida/.cache/arxiv_tex_concatenater/2405.02968/section/benchmark.tex
  /home/h-ishida/.cache/arxiv_tex_concatenater/2405.02968/section/discussion.tex
  /home/h-ishida/.cache/arxiv_tex_concatenater/2405.02968/section/conclusion.tex

All files have been concatenated into: /home/h-ishida/.cache/arxiv_tex_concatenater/2405.02968/cat.txt
(Located in: /home/h-ishida/.cache/arxiv_tex_concatenater/2405.02968)
```
