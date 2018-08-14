#!/usr/bin/python3

import collections
import functools
import os
import re
import shlex
import subprocess
import sys

paragraph_markers = ['◊', '¶']

usage = 'Usage: ./paranotes-filter.py input.md bibliography.yaml style.csl'

pinpoint_terms = {'para': {'singular':'para.',
                           'plural':'paras.'},
                  'page': {'singular':'p.',
                           'plural':'pp.'}}

def is_range(pinpoint_value):
  return pinpoint_value.count('-')

def detect_pinpoint_type(pinpoint):
  if pinpoint.count('para'):
    return 'para'
  if pinpoint.count('p.'):
    return 'page'
  else:
    raise NotImplementedError('Pinpoint type not handled: {}'.format(pinpoint))

def extract_pinpoint_value(pinpoint):
  pinpoint_type = detect_pinpoint_type(pinpoint)
  terms_to_strip = pinpoint_terms[pinpoint_type]
  pinpoint_value = pinpoint
  for term in sorted(terms_to_strip.values(), key=lambda s: len(s), reverse=True):
    pinpoint_value = pinpoint_value.replace(term, '', 1).strip()
  return pinpoint_value

def get_term(pinpoint_type, plural, include_dot):
  try:
    term = pinpoint_terms[pinpoint_type]['plural' if plural else 'singular']
    if term.endswith('.') and not include_dot:
      return term[:-1]
    return term
  except:
    raise NotImplementedError('Cannot get term for pinpoint type: {}'.format(pinpoint_type))

def render_note(key, content, citation_db, append_short_form):
  if 'supra' in content:
    sys.stdout.write('{}, _supra_ para {}'.format(citation_db[key]['short_form'], citation_db[key]['original_paragraph']))
  else:
    sys.stdout.write('[{}'.format(key))
  for pinpoint_type, pinpoint_list in content['pinpoints'].items():
    plural = (len(pinpoint_list) > 1 or is_range(pinpoint_list[0]))
    if 'supra' in content:
      # No period for pinpoint signal in supra context.
      sys.stdout.write(' at {} '.format(get_term(pinpoint_type, plural, False)))
      for pinpoint in pinpoint_list[:-1]:
        sys.stdout.write('{}, '.format(pinpoint))
      sys.stdout.write('{}'.format(pinpoint_list[-1]))
    else:
      # Period needed in the pinpoint signal here for Pandoc to
      # render the full note with proper pinpointing.
      sys.stdout.write(' {} '.format(get_term(pinpoint_type, plural, True)))
      for pinpoint in pinpoint_list[:-1]:
        sys.stdout.write('{}, '.format(pinpoint))
      sys.stdout.write('{}'.format(pinpoint_list[-1]))
  if not 'supra' in content:
    sys.stdout.write(']')
    if key in append_short_form:
      sys.stdout.write(' [{}]'.format(citation_db[key]['short_form']))

def print_paragraph_notes(para_notes, citation_db, append_short_form):
  if para_notes.items():
    sys.stdout.write('\n')
    sys.stdout.write('\\setlength{\\originalparskip}{\\parskip}\n')
    sys.stdout.write('\\setstretch{1.0}\n')
    sys.stdout.write('\\setlength{\\leftskip}{2.5em}\n\n')
  num_notes = len(para_notes.items())
  for note_id, (key, content) in enumerate(para_notes.items(), 1):
    if note_id != 1:
      sys.stdout.write('\\setlength{\\parskip}{0.25em}\n\n')
    render_note(key, content, citation_db, append_short_form)
    sys.stdout.write('.')
    if note_id != num_notes:
      # sys.stdout.write('\n\n\\vspace{-20pt}\n\n')
      sys.stdout.write('\n\n')
      pass
    else:
      sys.stdout.write('\n\n')
  if para_notes.items():
    sys.stdout.write('\n\\setlength{\\leftskip}{0em}\n')
    sys.stdout.write('\\setstretch{\\mainstretch}\n')
    sys.stdout.write('\\setlength{\\parskip}{\\originalparskip}\n\n')

@functools.lru_cache(maxsize=None)
def get_short_form(citation_key, bibliography_path, csl_path):
  temp_path = 'temp.md'
  with open(temp_path, 'w') as temp_file:
    temp_file.write('[{}]\n\n[{}]\n'.format(citation_key, citation_key))
  pandoc_command = 'pandoc temp.md --bibliography {} --csl {} -t plain'.format(bibliography_path, csl_path)
  pandoc_output = subprocess.check_output(shlex.split(pandoc_command)).decode('utf-8')
  try:
    os.remove(temp_path)
  except:
    pass
  forms = pandoc_output.splitlines()
  short_form = forms[-1]
  return short_form

def detect_duplicate_citations(input_path):
  citation_counts = collections.defaultdict(int)
  with open(input_path, 'r', encoding='utf-8') as f:
    content = f.read()
    # Finding all citations to be at most marked inline but rendered
    # more fully as paragraph notes.
    for m in re.finditer('\[(@[^\s,\]]+)', content):
      citation_key = m.group(1)
      citation_counts[citation_key] += 1
    # Finding all citations to be rendered fully inline {@ref-id},
    # without a paragraph note.
    for m in re.finditer('\{(@[^\s,\}]+)', content):
      citation_key = m.group(1)
      citation_counts[citation_key] += 1
  return list(map(lambda x: x[0], filter(lambda kv: kv[1] >= 2, citation_counts.items())))

def handle_newlines(raw_source):
  # Don't mess with newlines in the pandoc header.
  header = re.search(r'---.*?\.\.\.', raw_source, re.DOTALL)
  if header:
    raw_source = raw_source.replace(header.group(0), '')
  paragraphed = re.sub(r'(.)\n(.)', r'\1 \2', raw_source)
  if header:
    paragraphed = header.group(0) + paragraphed
  return paragraphed

def run_filter(input_path, bibliography_path, csl_path):
  citation_db = {}

  append_short_form = detect_duplicate_citations(input_path)

  raw_source = open(input_path, 'r', encoding='utf-8').read()

  paragraphed_source = handle_newlines(raw_source)

  para_number = 0
  possibly_in_a_citation = False
  in_a_citation = False
  possibly_in_an_inline_citation = False
  in_an_inline_citation = False
  para_notes = {}
  explicit_paragraph_note = True
  for char in paragraphed_source:
    if char == '\n' and not possibly_in_a_citation:
      explicit_paragraph_note = True
    elif char != ' ' and char != '[' and not possibly_in_a_citation:
      explicit_paragraph_note = False
    if char in paragraph_markers or char == '#':
      # Whenever we encounter a new paragraph or heading level, dump
      # any paragraph-level notes from the previous paragraph.
      print_paragraph_notes(para_notes, citation_db, append_short_form)
      # Resetting the paragraph notes for the forthcoming paragraph.
      para_notes = {}
      if char in paragraph_markers:
        para_number += 1
        sys.stdout.write('{}.'.format(para_number))
      elif char == '#':
        sys.stdout.write(char)
    elif char == '[':
      possibly_in_a_citation = True
      citation = ''
    elif char == '@' and possibly_in_a_citation:
      in_a_citation = True
      citation += char
    elif not in_a_citation and possibly_in_a_citation and char != '@':
      possibly_in_a_citation = False
      sys.stdout.write('[')
      sys.stdout.write(char)
    elif in_a_citation and char != ']':
      # Keep building up the citation content.
      citation += char
    elif in_a_citation and char == ']':
      # The citation is over.
      citation_key = citation.split()[0].rstrip(',')
      citation_pinpoint = ' '.join(citation.split()[1:]).strip()
      if citation_key not in para_notes:
        para_notes[citation_key] = {'pinpoints':{}}
      if (citation_pinpoint):
        pinpoint_type = detect_pinpoint_type(citation_pinpoint)
        pinpoint_value = extract_pinpoint_value(citation_pinpoint)
        if pinpoint_type not in para_notes[citation_key]['pinpoints']:
          para_notes[citation_key]['pinpoints'][pinpoint_type] = []
        para_notes[citation_key]['pinpoints'][pinpoint_type].append(pinpoint_value)
      if citation_key not in citation_db:
        # This is the first mention. Track the paragraph number. We'll
        # also need to print the full citation in a section right
        # before the next paragraph.
        citation_db[citation_key] = {}
        citation_db[citation_key]['original_paragraph'] = para_number
        short_form = get_short_form(citation_key, bibliography_path, csl_path)
        citation_db[citation_key]['short_form'] = short_form
        if not explicit_paragraph_note:
          sys.stdout.write('({})'.format(short_form))
          append_short_form.append(citation_key)
      else:
        # This citation key has been mentioned before.
        original_paragraph = citation_db[citation_key]['original_paragraph']
        if original_paragraph != para_number:
          para_notes[citation_key]['supra'] = True
        if not explicit_paragraph_note:
          short_form = citation_db[citation_key]['short_form']
          sys.stdout.write('({})'.format(short_form))
      in_a_citation = False
      possibly_in_a_citation = False
      in_an_inline_citation = False
      possibly_in_an_inline_citation = False
    elif char == '{':
      possibly_in_an_inline_citation = True
      citation = ''
    elif char == '@' and possibly_in_an_inline_citation:
      in_an_inline_citation = True
      citation += char
    elif not in_an_inline_citation and possibly_in_an_inline_citation and char != '@':
      possibly_in_an_inline_citation = False
      sys.stdout.write('{')
      sys.stdout.write(char)
    elif in_an_inline_citation and char != '}':
      # Keep building up the citation content.
      citation += char
    elif in_an_inline_citation and char == '}':
      # The citation is over.
      inline_note = {}
      citation_key = citation.split()[0].rstrip(',')
      citation_pinpoint = ' '.join(citation.split()[1:]).strip()
      if citation_key not in inline_note:
        inline_note[citation_key] = {'pinpoints':{}}
      if (citation_pinpoint):
        pinpoint_type = detect_pinpoint_type(citation_pinpoint)
        pinpoint_value = extract_pinpoint_value(citation_pinpoint)
        if pinpoint_type not in inline_note[citation_key]['pinpoints']:
          inline_note[citation_key]['pinpoints'][pinpoint_type] = []
        inline_note[citation_key]['pinpoints'][pinpoint_type].append(pinpoint_value)
      if citation_key not in citation_db:
        # This is the first mention. Track the paragraph number. We'll
        # also need to print the full citation in a section right
        # before the next paragraph.
        citation_db[citation_key] = {}
        citation_db[citation_key]['original_paragraph'] = para_number
        short_form = get_short_form(citation_key, bibliography_path, csl_path)
        citation_db[citation_key]['short_form'] = short_form
        render_note(citation_key, inline_note[citation_key], citation_db, append_short_form)
      else:
        # This citation key has been mentioned before.
        original_paragraph = citation_db[citation_key]['original_paragraph']
        inline_note[citation_key]['supra'] = True
        render_note(citation_key, inline_note[citation_key], citation_db, append_short_form)
      in_a_citation = False
      possibly_in_a_citation = False
      in_an_inline_citation = False
      possibly_in_an_inline_citation = False
    else:
      sys.stdout.write(char)

  print_paragraph_notes(para_notes, citation_db, append_short_form)

if (__name__ == '__main__'):
  try:
    input_path = sys.argv[1]
    bibliography_path = sys.argv[2]
    csl_path = sys.argv[3]
  except:
    print(usage)
    exit(1)

  if (not input_path.endswith('.md') or not os.path.isfile(input_path) or
      not csl_path.endswith('.csl') or not os.path.isfile(csl_path) or
      not bibliography_path.endswith('.yaml') or not os.path.isfile(bibliography_path)):
    print(usage)
    sys.exit(1)

  run_filter(input_path, bibliography_path, csl_path)
