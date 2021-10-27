import xml.etree.ElementTree as ET
import os, re

import html2text

HTML_PATH = "html"


class Resource:
    def __init__(self, resource_tag):
        data = resource_tag.find("data")
        if data.attrib["encoding"] != "base64":
            raise NotImplementedError(
                self.__class__.__name__ + " not base64 encoded resource"
            )

        self.base64 = data.text.replace("\n", "").strip()

    def get_md(self):
        return f"![](data:image/png;base64,{self.base64})"


class Note:
    def __init__(self, note_tag):
        self.resource = None
        self.attributes = {}
        self.is_bookmark = False

        for property in note_tag:
            if property.tag in ("title", "created", "updated", "content"):
                setattr(self, property.tag, property.text)

            if property.tag == "resource":
                self.resource = Resource(property)

            if property.tag == "note-attributes":
                for attr in property:
                    self.attributes[attr.tag] = attr.text
                    if attr.tag == "source-url":
                        self.is_bookmark = True

    def get_filename(self, ext="md"):
        filename = re.sub('[*"\/<>:|?]', "_", self.title)
        if ext:
            filename += "." + ext

        return filename

    def get_content(self):
        return html2text.html2text(self.content)

    def get_meta_list(self):
        ret = ""
        for k, v in self.attributes.items():
            ret += f"- **{k}**: {v}\n"

        return ret

    def write_as_html(self, path):
        with open(path, "w") as file:
            file.write(self.content)

    def write(self, note_dir):
        target_path = os.path.join(note_dir, self.get_filename())

        if self.is_bookmark:
            html_path = os.path.join(note_dir, HTML_PATH, self.get_filename("html"))

            # TODO: create html directory if not exist
            with open(target_path, "w") as file:
                file.write(self.get_meta_list())
                file.write(
                    f"\n\nI will be connected to `{HTML_PATH}/{self.get_filename('html')}`"
                )

            self.write_as_html(html_path)

        else:
            with open(target_path, "w") as file:
                file.write(self.get_content())

                if self.resource:
                    file.write(f"\n\n{self.resource.get_md()}")


class Notepad:
    def __init__(self, inputfile):
        self.root = ET.parse(inputfile).getroot()
        self.notes = []

        self.read_notes()

    def read_notes(self):
        for note_tag in self.root.findall("note"):
            note = Note(note_tag)
            self.notes.append(note)

    def print_notes(self):
        for (i, note) in enumerate(self.notes):
            print(f"{i} | {note.title} {'#bookmark' if note.is_bookmark else ''}")
