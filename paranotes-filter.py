#!/usr/bin/python3

import os
import shlex
import subprocess
import sys

def strip_period(pinpoint):
  return pinpoint.replace('para.', 'para').replace('paras.', 'para')

def detect_pinpoint_type(pinpoint):
  if pinpoint.count('para'):
    return 'para'
  else:
    return 'other'

def extract_pinpoint_value(pinpoint):
  if pinpoint.count('paras.'):
    return pinpoint.lstrip('paras. ')
  elif pinpoint.count('para.'):
    return pinpoint.lstrip('para. ')
  else:
    raise NotImplementedError('Cannot extract pinpoint value for {}'.format(pinpoint))

def get_term(pinpoint_type, plural, period):
  term = ''
  if pinpoint_type == 'para' and plural:
    term = 'paras'
  elif pinpoint_type == 'para' and not plural:
    term = 'para'
  else:
    raise NotImplementedError('Cannot get term for pinpoint type: {}'.format(pinpoint_type))
  if period:
    term += '.'
  return term

usage = 'Usage: ./paranotes-filter.py input.md bibliography.yaml style.csl'

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

citation_db = {}
  
para_number = 0
with open(input_path, 'r', encoding='utf-8') as f:
  transformed_content = ""
  cite_context = False
  para_notes = {}
  standalone = True
  for char in f.read():
    if char == '\n' and not cite_context:
      standalone = True
    elif char != ' ' and char != '[' and not cite_context:
      standalone = False
    if char == '\n' and not cite_context:
      transformed_content += '\n'
    elif char == "¶" or char == "#":
      for key, content in para_notes.items():
        transformed_content += '    '
        if 'supra' in content:
          transformed_content += '{}, _supra_ para {} '.format(citation_db[key]['short_form'], citation_db[key]['original_paragraph'])
        else:
          transformed_content += '[{} '.format(key)
        for pinpoint_type, pinpoint_list in content['pinpoints'].items():
          plural = (len(pinpoint_list) > 1) # Need to test for range in solo pinpoint.
          if 'supra' in content:
            transformed_content += 'at {} '.format(get_term(pinpoint_type, plural, False)) # No period in supra context.
            for pinpoint in pinpoint_list[:-1]:
              transformed_content += '{}, '.format(pinpoint)
            transformed_content += '{}'.format(pinpoint_list[-1])
          else:
            transformed_content += '{} '.format(get_term(pinpoint_type, plural, True)) # Period needed here for Pandoc.
            for pinpoint in pinpoint_list[:-1]:
              transformed_content += '{}, '.format(pinpoint)
            transformed_content += '{}'.format(pinpoint_list[-1])
        if not 'supra' in content:
          transformed_content += ']\n'
        else:
          transformed_content += '\n'
        transformed_content += '\n'
      para_notes = {}
      if char == "¶":
        para_number += 1
        transformed_content += '{}.'.format(para_number)
      elif char == "#":
        transformed_content += char
    elif char == "[":
      cite_context = True
      citation = ""
    elif cite_context and char != "]":
      citation += char
    elif cite_context and char == "]":
      citation_key = citation.split()[0].rstrip(",")
      citation_pinpoint = " ".join(citation.split()[1:]).strip()
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
        temp_path = "temp.md"
        with open(temp_path, 'w') as temp_file:
          temp_file.write('[{}]\n\n[{}]\n'.format(citation_key, citation_key))
        pandoc_command = 'pandoc temp.md --bibliography {} --csl {} -t plain'.format(bibliography_path, csl_path)
        pandoc_output = subprocess.check_output(shlex.split(pandoc_command)).decode('utf-8')
        try:
          os.remove(temp_path)
        except:
          pass
        forms = pandoc_output.splitlines()
        long_form = forms[0]
        short_form = forms[-1]
        citation_db[citation_key]['short_form'] = short_form
        if not standalone:
          transformed_content += '({})'.format(short_form)
        else:
          transformed_content += '[{} {}]\n'.format(citation_key, citation_pinpoint)
      else:
        if not standalone:
          short_form = citation_db[citation_key]['short_form']
          original_paragraph = citation_db[citation_key]['original_paragraph']
          transformed_content += '({})'.format(short_form)
          if original_paragraph != para_number:
            para_notes[citation_key]['supra'] = True
        else:
          original_paragraph = citation_db[citation_key]['original_paragraph']
          para_notes[citation_key]['supra'] = True
        
      cite_context = False
    else:
      transformed_content += char

for key, content in para_notes.items():
  transformed_content += '    '
  if 'supra' in content:
    transformed_content += '{}, _supra_ para {} '.format(citation_db[key]['short_form'], citation_db[key]['original_paragraph'])
  else:
    transformed_content += '[{} '.format(key)
  for pinpoint_type, pinpoint_list in content['pinpoints'].items():
    plural = (len(pinpoint_list) > 1) # Need to test for range in solo pinpoint.
    if 'supra' in content:
      transformed_content += 'at {} '.format(get_term(pinpoint_type, plural, False)) # No period in supra context.
      for pinpoint in pinpoint_list[:-1]:
        transformed_content += '{}, '.format(pinpoint)
      transformed_content += '{}'.format(pinpoint_list[-1])
    else:
      transformed_content += '{} '.format(get_term(pinpoint_type, plural, True)) # Period needed here for Pandoc.
      for pinpoint in pinpoint_list[:-1]:
        transformed_content += '{}, '.format(pinpoint)
      transformed_content += '{}'.format(pinpoint_list[-1])
  if not 'supra' in content:
    transformed_content += ']\n'
  else:
    transformed_content += '\n'
  transformed_content += '\n'
      
print(transformed_content)
