from ebooklib import epub
import base64
import fitz
import re
file_name = "AVR Book"
doc = fitz.open(file_name+".pdf")

page_limit = 100
common_blocked_index = [-1]
even_blocked_index = []
odd_blocked_index = []
skip_till = -1
page_index = -1
number_regex = "([1-9]|[1-9][0-9]|[1-9][0-9][0-9]|[1-9][0-9][0-9][0-9])"
title_re = "CHAPTER " + number_regex


even_blocked_index = even_blocked_index + common_blocked_index
odd_blocked_index = odd_blocked_index + common_blocked_index


blocked_strings = [
    "10 Steps to Earning Awesome Grades (While Studying Less)"
]

total_pages = len(doc)

current_header = "Introduction"

html_chapter_list = []
html = ""


image_index = 0
for page in doc:
    page_index += 1

    print(
        f"current = {page_index}, limit = {page_limit}, total = {total_pages}")

    if (page_index <= skip_till):
        continue

    if (page_index == page_limit):
        break

    text = page.get_text("dict", sort=True)
    block_len = len(text["blocks"])

    for i_block in range(block_len):
        if (page_index+1) % 2 == 0:
            if i_block in even_blocked_index:
                continue

            if (i_block - block_len) in even_blocked_index:
                continue
        else:
            if i_block in odd_blocked_index:
                continue

            if (i_block - block_len) in odd_blocked_index:
                continue

        block = text["blocks"][i_block]

        if "lines" in block:
            lines = block["lines"]
            line_text = ""

            for line in lines:
                if "spans" in line:
                    for span in line["spans"]:

                        span_text = span["text"]

                        if span_text in blocked_strings:
                            continue

                        if title_re and re.search(title_re, span_text):

                            ele = f'''<div style="
                            font-size:{span["size"]}; 
                            font-family:Sans-Serif;
                            padding-top:{span["size"]/2}px;
                            padding-bottom:{span["size"]/2}px;
                            text-align: justify;
                            text-justify: inter-word;
                            " >{line_text}</div>'''

                            html = html + ele + "\n\n"

                            html_chapter_list.append({
                                "title": current_header,
                                "html": html
                            })

                            print("chapter found: ", span_text)

                            html = ""
                            current_header = span_text

                        span_el = f'''<span 
                            style="color:{span["color"]}; 
                            font-weight: {"bold" if span["flags"] & 2**4 else "normal"};
                            font-style: {"italic" if span["flags"] & 2**1 else "normal"};
                            ">
                            {span_text}
                            </span>'''
                        line_text += span_el

            ele = f'''<div style="
                font-size:{span["size"]}; 
                font-family:Sans-Serif;
                padding-top:{span["size"]/2}px;
                padding-bottom:{span["size"]/2}px;
                text-align: justify;
                text-justify: inter-word;
                " >{line_text}</div>'''

            html = html + ele + "\n\n"

        elif "image" in block:
            image = block["image"]
            base64EncodedStr = base64.b64encode(image)
            ele = '<img src="data:image/jpeg;base64,' + \
                base64EncodedStr.decode() + '" width="100%">'
            html = html + ele

        else:
            print(block)


book = epub.EpubBook()
book.set_title("file_name")
book.set_language("en")
chapter_list = []
for chapter in html_chapter_list:
    title = chapter["title"]
    html = chapter["html"]
    print(title)
    c1 = epub.EpubHtml(title=title,
                       file_name=title+".xhtml", lang="en")
    c1.content = html
    book.add_item(c1)
    chapter_list.append(c1)


book.toc = (
    epub.Link(title+".xhtml", title, title),
    (epub.Section(file_name), (*chapter_list,)),
)

book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())

# define CSS style
style = "BODY {color: white;}"
nav_css = epub.EpubItem(
    uid="style_nav",
    file_name="style/nav.css",
    media_type="text/css",
    content=style,
)

# add CSS file
book.add_item(nav_css)

# basic spine
book.spine = ["nav", c1]

# write to the file
epub.write_epub(file_name + ".epub", book, {})
