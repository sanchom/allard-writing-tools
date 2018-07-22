#!/usr/bin/python3

import os
import shlex
import subprocess
import sys

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

def print_paragraph_notes(para_notes, citation_db):
  if para_notes.items():
    sys.stdout.write('\n')
  for key, content in para_notes.items():
    sys.stdout.write('    ')
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
    sys.stdout.write('.')
    sys.stdout.write('\n\n')

def run_filter(input_path, bibliography_path, csl_path):
  citation_db = {}

  para_number = 0
  with open(input_path, 'r', encoding='utf-8') as f:
    in_a_citation = False
    para_notes = {}
    explicit_paragraph_note = True
    for char in f.read():
      # TODO: There's a bug here. A citation that begins on a new line
      # will be considered an explicit paragraph note, even if it's in
      # the middle of a body of text.
      if char == '\n' and not in_a_citation:
        explicit_paragraph_note = True
      elif char != ' ' and char != '[' and not in_a_citation:
        explicit_paragraph_note = False
      if char == '¶' or char == '#':
        # Whenever we encounter a new paragraph or heading level, dump
        # any paragraph-level notes from the previous paragraph.
        print_paragraph_notes(para_notes, citation_db)
        # Resetting the paragraph notes for the forthcoming paragraph.
        para_notes = {}
        if char == '¶':
          para_number += 1
          sys.stdout.write('{}.'.format(para_number))
        elif char == '#':
          sys.stdout.write(char)
      elif char == '[':
        in_a_citation = True
        citation = ''
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
          # Getting the short form.
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
          citation_db[citation_key]['short_form'] = short_form
          if not explicit_paragraph_note:
            sys.stdout.write('({})'.format(short_form))
          else:
            sys.stdout.write('[{} {}]\n'.format(citation_key, citation_pinpoint))
        else:
          # This citation key has been mentioned before.
          original_paragraph = citation_db[citation_key]['original_paragraph']
          if original_paragraph != para_number:
            para_notes[citation_key]['supra'] = True
          if not explicit_paragraph_note:
            short_form = citation_db[citation_key]['short_form']
            sys.stdout.write('({})'.format(short_form))
        in_a_citation = False
      else:
        sys.stdout.write(char)

  print_paragraph_notes(para_notes, citation_db)

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
