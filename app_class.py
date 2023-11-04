from ebooklib import epub
import base64
import fitz
import re


class EbookMaker:
    def __init__(self, file_name, blocked_strings) -> None:

        self.chapter_data_list = []
        self.initiateNewChapter("Introduction")
        self.page_index = -1
        self.page_limit = 50
        self.skip_till = -1
        self.skip_trim = 4
        self.blocked_strings = blocked_strings
        self.file_name = file_name

        common_blocked_index = [-1]
        even_blocked_index = []
        odd_blocked_index = []

        number_regex = "([1-9]|[1-9][0-9]|[1-9][0-9][0-9]|[1-9][0-9][0-9][0-9])"
        self.title_re = "CHAPTER " + number_regex

        self.even_blocked_index = even_blocked_index + common_blocked_index
        self.odd_blocked_index = odd_blocked_index + common_blocked_index

    def initiateNewChapter(self, header):
        self.current_header = header
        self.current_html = ""
        print("chapter started: ", header)

    def startBookRead(self):
        doc = fitz.open(self.file_name+".pdf")
        total_pages = len(doc)

        for page in doc:
            self.page_index += 1
            print(
                f"current = {self.page_index}, limit = {self.page_limit}, total = {total_pages}")

            if (self.page_index <= self.skip_till):
                continue

            if (self.page_index == self.page_limit):
                break

            blocks = page.get_text("dict", sort=True)["blocks"]
            block_len = len(blocks)

            for i_block in range(block_len):
                self.processBlock(i_block, blocks)

        self.addChapter()
        self.initiateNewChapter("")

    def processBlock(self, i_block, blocks):
        block_len = len(blocks)

        # added filters to remove unwanted blocks like header, footer
        if (self.skip_trim < self.page_index):
            if (self.page_index + 1) % 2 == 0:
                if i_block in self.even_blocked_index:
                    return

                if (i_block - block_len) in self.even_blocked_index:
                    return
            else:
                if i_block in self.odd_blocked_index:
                    return

                if (i_block - block_len) in self.odd_blocked_index:
                    return

        block = blocks[i_block]
        if "lines" in block:
            self.createTextBlock(block)
        elif "image" in block:
            self.createImageBlock(block)

    def createTextBlock(self, block):
        lines = block["lines"]
        line_text = ""

        for line in lines:
            if "spans" in line:
                for span in line["spans"]:
                    span_text = span["text"]
                    if span_text in self.blocked_strings:
                        continue

                    # new chapter found
                    if self.title_re and re.search(self.title_re, span_text):
                        # !pass old style here or skip if line-index is 0
                        self.addTextBlock(line_text, span)
                        self.addChapter()
                        self.initiateNewChapter(span_text)

                    # adding span here
                    span_el = f'''<span 
                        style="color:{span["color"]}; 
                        font-weight: {"bold" if span["flags"] & 2**4 else "normal"};
                        font-style: {"italic" if span["flags"] & 2**1 else "normal"};
                        ">
                        {span_text}
                        </span>'''
                    line_text += span_el

        self.addTextBlock(line_text, span)

    def addTextBlock(self, line_text, span):
        ele = f'''<div style="
                font-size:{span["size"]}; 
                font-family:Sans-Serif;
                padding-top:{span["size"]/2}px;
                padding-bottom:{span["size"]/2}px;
                text-align: justify;
                text-justify: inter-word;
                " >{line_text}</div>'''
        self.current_html += ele

    def addChapter(self):
        self.chapter_data_list.append({
            "title": self.current_header,
            "html": self.current_html
        })

    def createImageBlock(self, block):
        image = block["image"]
        base64EncodedStr = base64.b64encode(image)
        ele = '<img src="data:image/jpeg;base64,' + \
            base64EncodedStr.decode() + '" width="100%">'
        self.current_html = self.current_html + ele

    def exportToEpub(self):
        book = epub.EpubBook()
        book.set_title(self.file_name)
        book.set_language("en")

        print("Epub gen started")

        chapter_list = []

        for chapter in self.chapter_data_list:
            title = chapter["title"]
            html = chapter["html"]

            chap = epub.EpubHtml(title=title,
                                 file_name=title+".xhtml", lang="en")
            chap.content = html

            book.add_item(chap)
            chapter_list.append(chap)
            chap = None

        book.toc = (
            *chapter_list,
        )

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

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
        book.spine = ["nav", *chapter_list,]

        # write to the file
        epub.write_epub(self.file_name + ".epub", book, {})
        print("epub created")


ebookMaker = EbookMaker("AVR Book")
ebookMaker.startBookRead()
ebookMaker.exportToEpub()
