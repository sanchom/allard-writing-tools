I want to write in as close to plain text as possible. I don't want to
think about formatting or citation layout while I'm writing. Those
things should be automatic. These are some tools that I'm trying to
use to get me there.

# Example

Document source      |  Result
:-------------------------:|:-------------------------:
[![What the text that you're writing will look like](examples/source1.png)](examples/source1.png)  |  [![Rendered PDF](examples/render1.png)](examples/render1.png)

# Another example

* [Source text](https://raw.githubusercontent.com/sanchom/allard-writing-tools/master/examples/gale_cup_reproduction/source.md)
* [Bibliography file](https://github.com/sanchom/allard-writing-tools/blob/master/examples/gale_cup_reproduction/bibliography.yaml)
* [Rendered PDF](https://github.com/sanchom/allard-writing-tools/blob/master/examples/gale_cup_reproduction/factum.pdf)

This system also generates a title page, table of contents, and table
of authorities as required by the moot court.

A lot of errors can creep in when you try to manually lay out
citations, insert pinpoints, back-references, and create tables of
authorities. This can all be automated. LaTex and BibTex have done
this for decades for more standard citation formats. And, those
solutions are certainly adequate for law journal articles with
citations presented in standard footnotes. But, I haven't found
something adequate for writing a factum in plain text that can then be
converted to a nicely typeset PDF that matches the formatting
requirements of UBC or the BC Court of Appeals.

These tools try to replicate the formatting from the guidance and
examples listed here, in roughly the priority listed. That is, if
there is any conflicting guidance, I follow requirements of the
higher-listed guide, but will look to lower-listed guides when a
higher-listed guide leaves something ambiguous.

1. http://www.allard.ubc.ca/sites/www.allard.ubc.ca/files/uploads/moots/first-year-moot-court-rules-2018.pdf
2. http://www.allard.ubc.ca/sites/www.allard.ubc.ca/files/uploads/first%20year/factum_citation_guide.pdf
3. http://guides.library.ubc.ca/legalcitation
4. http://www.bclaws.ca/Recon/document/ID/freeside/297_2001a
5. https://www.courts.gov.bc.ca/Court_of_Appeal/practice_and_procedure/Forms/Checklist_Court_of_Appeal_Factums.pdf
6. https://store.thomsonreuters.ca/product-detail/canadian-guide-to-uniform-legal-citation-9th-edition-manuel-canadien-de-la-reference-juridique-9e-edition-mcgill-guide-hc-print/
7. https://www.chicagomanualofstyle.org/home.html
8. http://www.allard.ubc.ca/sites/www.allard.ubc.ca/files/uploads/moots/sample_appellants_factum_0.pdf
9. http://www.allard.ubc.ca/sites/www.allard.ubc.ca/files/uploads/moots/sample_respondents_factum_0.pdf

# Technical details

Dependencies include: LaTex (texlive), Pandoc, Python 3, probably
more.

This is a work in progress. I'll be adding citation types as I need
them. Right now, it only works for legal cases, legislation, and
books. My python pre-processor for per-paragraph notes is a quick
hack. I want that to be a proper Pandoc filter and I want to re-write
it in Haskell or Racket.

When writing markdown for this style, you need to use paragraph
markings (¶, or ◊). This is the only way the pre-processor can know where to
insert the per-paragraph notes. "Paragraphs" don't necessarily end
when there's a double linebreak. You may be making a quotation or some
text from a statute, but that isn't the end of the "paragraph" for the
purposes of the factum's structure or for inserting citations.

```
  ./paranotes-filter.py sample-factum-1.md sample-bibliography-1.yaml allard-factum.csl \
  | pandoc --bibliography sample-bibliography-1.yaml --csl allard-factum.csl --template=factum.latex -o sample-factum-1.pdf
```

Or, with a table-of-contents:

```
  ./paranotes-filter.py sample-factum-2.md sample-bibliography-2.yaml allard-factum.csl \
  | pandoc --bibliography sample-bibliography-2.yaml --csl allard-factum.csl --template=factum.latex --toc -o sample-factum-2.pdf
```
