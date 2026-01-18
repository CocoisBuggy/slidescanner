# Coco's Scanner

rationale: Why build this?

I have a canon camera, along with an adapter for my macro lens that lets
me capture very good stills of old film slides. My Father has boxes
and boxes of these film slides, and I was unsatisfied with the pipeline of

  1. capture on camera
  1. organise these photos after the fact

For this many slides, I felt it would be invaluable to automate the picture taking
(focus and fire) along with the organization of the photos.

As I am scanning I can read the labels on the casette box and the ideal flow for me
is to be able to fill out that data as I go along rather than flailing around with
disorganized boxes after the fact.

## Hence, an application

The application has a couple of context fields that can be filled out

### Casette name context

Some, but not all, of the casettes have names on them. things like 'Russia, 1994'.
I want to be able to be able to assert at the start

> "Hey, this is russia, 1994 that I am busy capturing"

Rather than doing it after the fact.

### Casette date

Usually, precise dates are missing from a slide (although it could be written on the slide
in some cases) and for all of these slides that have no precise date, it should suffice to
take a year and assign that to its metadata. Why do this? Well, it's optional, but I
prefer to have my photos show up in chronological order.

It also doesn't get rid of all date information since the file itself has metadata we
don't touch, we only change the EXIF data which is reader-specific.


### Slide Label

In the EXIF `Description` field

In the event that the slide actually does have a label, this context can be added as well.
When it is present, it will be written as a comment to the exif data. This is helpful to me
in particular because I am quite paranoid that anything written on these little slides might
become magically meaningful to me as I go through the process of digitization. I notice that
MANY slides end up with abbreviations that are utterly useless to a bystander unless they come
accross a slide with the expanded abbreviation, at which point you might wish you'd kept track
of the abbreviations after all.

The program is built to keep track of slides **in their boxes** since they are organized that way
in my instance, but even then locating the 'Kilamanjaro 1965, Blue Box' is a real ordeal since
it could be anywhere in the massive box of boxes that I am faced with. This is infinitely more
challenging when the lable on the box is something like "Special 02" or "serial: 0010234238w6q7d6w"


### Image Quality

When we are capturing, we can also use the numpad to give a 1-5 star rating that will also
appear in the exif metadata - and immediately get reset everytime we take the photo
