---
fontfamily: charter
linestretch: 2.0
...

# A heading

¶ In addition to the requirement of an "actionable wrong" independent
of the breach sued upon, punitive damages will only be awarded "where
the defendant's misconduct is so malicious, oppressive and high-handed
that it offends the court's sense of decency" [@hill, para. 196]. Such
behaviour has included defamation [@hill], failing to provide medical
care [@robitaille], and exceptionally abusive behaviour by an
insurance company [@whiten]. Here's another citation to _Robitaille_
with a pinpoint (the first didn't have one) [@robitaille, para. 23].

¶ Since the primary vehicle of punishment is the criminal law,
punitive damages should be scarcely used [@whiten, para. 69]. It is
also important to underline that there cannot be joint and several
responsibility for punitive damages because they arise from the
misconduct of the particular defendant against whom they are awarded.

[@hill, para. 195]

# Single-use citations

## Never used elsewhere

¶ There is no need to report a short-form when a citation is never used
elsewhere.

[@jordan]

## Use within the text is considered a use elsewhere

¶ But, if the citation is used even inline within the paragraph, [@marakah] the
short form is necessary in the paragraph note.

# Another heading

## A subheading

¶ Here, I cite to several pinpoints inline. Those pinpoints should be
collected and then reported together in the paragraph notes
below. Here's the first pinpoint [@hill, para. 5]. Here's the second
pinpoint [@hill, para. 20]. Here's the final pinpoint [@hill,
para. 80].

## Another subheading

¶ I should also be able to cite books [@haack-defending-science,
pp. 32-34]. Paragraph notes must appear in the order that their
citations appeared inline in the paragraph. [@whiten] [@robitaille]
[@hill]

## Re: the previous subheading

¶ The citation to _Hill_ sits alone on a newline, but should not be
treated as a standalone paragraph note. It is an inline citation tied
to the final sentence of that paragraph.

## Using brackets without a reference

¶ Brackets like this "[" should also be able to be used [...] as in
standard writing. They don't always imply a reference.

# Some other formatting

## Block quotations

¶ This next bit should be a block quotation. It should have a larger
left margin and a larger right margin than standard paragraphs. Here
is an example:

> (4) that the accused took, in a manner proportional to his or her
participation in the commission of the planned offence, reasonable steps
in the circumstances either to neutralize or otherwise cancel out the effects
of his or her participation or to prevent the commission of the offence.

## Lists (and inline citations)

¶ Sometimes, the factum might need to use inline citations for some
reason. I don't see how this is allowed by the formatting
requirements, but the sample factum uses them when it discusses
several cases in a list. In any case, it should not be hard to support
inline citations. I'll use `{` `@ref-id` `}` to force an inline
variant. And, I'll cite _Bird_ here so it can be used in the example below.

[@bird-scc]

¶ This is a significant substantive change to the defence. The
analysis in Canadian cases until now has turned on whether there was
timely and unequivocal communication of abandonment:

* {@bird-ca}, rev'd in {@bird-scc} --- The
Supreme Court of Canada affirmed the dissent of Costigan JA, who held
that a female accused who had helped lure the victim and her friend to
a golf course, where the victim was sexually assaulted and killed, did
not meet the requirements for abandonment. Her communication to the
principal that she was taking the victim's friend to the car because
she "doesn't need to see this" was insufficient evidence of either a
change of intention or timely and unequivocal communication.

* {@ball} --- In a case involving two accused in a
joint assault, Ryan JA ruled that abandonment was not timely because
the fatal injury had already occurred.

## Itemized lists

¶ It is well settled that the interpretation of a defence and whether
there is an air of reality to support it being considered by a jury
are both questions of law, reviewable on a standard of correctness. In
concluding that the defence of abandonment lacked an air of reality
and refusing to grant the appellant a new trial, the majority of the
Supreme Court of Canada erred in three respects:

I.  by adding a new element to the defence of abandonment,

II.  by retrospectively applying the new defence to the facts of this
case without giving the appellant a chance to address the new
requirement; and

III.  by incorrectly applying the air-of-reality test to both the old
and new elements of the defence.

## Quoting statutes

¶ I've added a special annotation that lets you indicate in the text
source when you're quoting a statute. This is needed because of the
often-nested nature of statutes and the large variety of label
types. Within the special `custom_list` environment, labels are
extracted and whitespace is used to infer the various nesting levels
of sections, subsections, paragraphs, subparagraphs, etc. For example,
this is {@car, sec. 602.07 (3)}:

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
