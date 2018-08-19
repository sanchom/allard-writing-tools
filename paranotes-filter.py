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

ref_counts = collections.defaultdict(int)

def convert_into_node(node_source):
  label_pattern = re.compile(r'^(\S+)  ')
  label_match = label_pattern.search(node_source)
  label = label_match.group(1)
  content = node_source[label_match.end():]
  subnode_start_pattern = re.compile(r' +\S+  ')
  subnode_start_match = subnode_start_pattern.search(content)
  subnodes = []
  if subnode_start_match:
    subnode_source = content[subnode_start_match.start():]
    content = content[:subnode_start_match.start()]
    # How many spaces lead this subnode's labels?
    num_leading_spaces = subnode_start_match.group(0).rstrip().count(' ')
    stripper = re.compile(r'^[\s]{{{0}}}(\S+  )'.format(num_leading_spaces), re.MULTILINE)
    subnode_source = stripper.sub(r'\1', subnode_source)
    subnodes = get_nodes(subnode_source)
  content = re.sub(r'\s+', ' ', content).strip()

  return (label, content, subnodes)

def split_into_nodes(raw_quote_source):
  # Split at newline, non-whitespace, then two spaces.
  node_start_pattern = re.compile(r'^\S+  ', re.MULTILINE)

  node_sources = []
  remaining_source = raw_quote_source
  while True:
    this_node_index = node_start_pattern.search(remaining_source).start()
    next_node_match = node_start_pattern.search(remaining_source, this_node_index + 1)
    if next_node_match:
      next_node_index = next_node_match.start()
      node_source = remaining_source[this_node_index:next_node_index]
      node_sources.append(node_source)
      remaining_source = remaining_source[next_node_index:]
    else:
      break
  node_source = remaining_source[this_node_index:]
  node_sources.append(node_source)
  return node_sources

def get_nodes(text_source):
  node_sources = split_into_nodes(text_source)
  nodes = []
  for node_source in node_sources:
    nodes.append(convert_into_node(node_source))
  return nodes

def get_transformed_nodes(nodes):
  result = ''
  result += '\\begin{quote}\n'
  for node in nodes:
    result = append_transformed_node(result, node, level=0)
  result += '\\end{quote}\n'
  return result

def append_transformed_node(result, top_level_node, level):
  label = top_level_node[0]
  content = top_level_node[1]
  subnodes = top_level_node[2]
  result += '\\begin{{enumerate}}[labelindent={}in, leftmargin={}in]\n'.format(0.25 * level, 0.25 * level)
  result += '\\item [{}]\n'.format(label)
  result += content + '\n'
  result += '\\end{enumerate}\n'
  result += '\n'
  for node in subnodes:
    result = append_transformed_node(result, node, level + 1)
  return result

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
  ref_counts[key] += 1
  count = ref_counts[key]
  sys.stdout.write('\n\\label{{ref:{}-{}}}\n'.format(key, count))
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

def transform_custom_list(raw_quote_source):
  """ This is what the incoming source looks like:

custom_list{
(3)  The pilot-in-command of a VFR aircraft operating in Class B
     airspace in accordance with an air traffic control clearance
     shall, when it becomes evident that it will not be possible to
     operate the aircraft in VMC at the altitude or along the route
     specified in the air traffic control clearance,
     (a)  where the airspace is a control zone, request authorization
          to operate the aircraft in special VFR flight; and
     (b)  in any other case,
          (i)  request an amended air traffic control clearance that
               will enable the aircraft to be operated in VMC to the
               destination specified in the flight plan or to an
               alternate aerodrome, or
          (ii)  request an air traffic control clearance to operate
                the aircraft in IFR flight.
}

  """
  raw_quote_source = raw_quote_source.replace(r'custom_list{', '').rstrip('}').strip('\n')
  nodes = get_nodes(raw_quote_source)
  return get_transformed_nodes(nodes)

def special_preprocessing(raw_source):
  # Don't mess with newlines in the pandoc header.
  header = re.search(r'---.*?\.\.\.', raw_source, re.DOTALL)
  preformatted_regions = re.findall(r'```.*?```', raw_source, re.DOTALL)
  for i, r in enumerate(preformatted_regions):
    raw_source = raw_source.replace(r, '<preformatted_{}>'.format(i))
  custom_lists = re.findall(r'custom_list\{.*?\}', raw_source, re.DOTALL)
  for i, r in enumerate(custom_lists):
    raw_source = raw_source.replace(r, '<custom_list_{}>'.format(i))
  if header:
    raw_source = raw_source.replace(header.group(0), '<header>')
  paragraphed = re.sub(r'(.)\n(.)', r'\1 \2', raw_source)
  # Reattaching the header
  if header:
    paragraphed = re.sub(r'\<header\>', header.group(0), paragraphed)
  for i, r in enumerate(preformatted_regions):
    paragraphed = paragraphed.replace('<preformatted_{}>'.format(i), r)
  for i, r in enumerate(custom_lists):
    paragraphed = paragraphed.replace('<custom_list_{}>'.format(i), transform_custom_list(r))
  return paragraphed

def bracket_lists(raw_source):
  # Looking for newline, whitespace, then roman numeral then two spaces.
  pass

def run_filter(input_path, bibliography_path, csl_path):
  citation_db = {}

  append_short_form = detect_duplicate_citations(input_path)

  raw_source = open(input_path, 'r', encoding='utf-8').read()

  paragraphed_source = special_preprocessing(raw_source)

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

def add_table_of_authorities():
  sys.stdout.write('\n\n')
  for key, count in ref_counts.items():
    sys.stdout.write('{}: '.format(key.lstrip('@')))
    sys.stdout.write('\n\\pagelist{{ref:{}}}{{{}}}'.format(key, count))
    sys.stdout.write('\n\n')

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
  add_table_of_authorities()
