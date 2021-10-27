import xml.etree.ElementTree as ET
import os, re, base64, hashlib

import ENML_PY

RESOURCE_PATH = "res"


class Enml_resource_finder:
    def __init__(self, note):
        self.note = note

    def save(self, hash_str, mime_type):
        res = self.note.get_resource(hash_str)

        if res != None:
            return res.filename

        else:
            print("Resource not found")
            return "_undefined_resource_"


class Resource:
    def __init__(self, resource_tag):
        data = resource_tag.find("data")
        if data.attrib["encoding"] != "base64":
            raise NotImplementedError(
                self.__class__.__name__ + " not base64 encoded resource"
            )

        self.mime = resource_tag.find("mime").text
        self.base64 = data.text.replace("\n", "").strip()
        self.binary = base64.b64decode(self.base64)
        self.hash = hashlib.md5(self.binary).hexdigest()
        self.filename = self.hash

        filename = resource_tag.find("resource-attributes/file-name")
        if filename != None and filename.text:
            self.filename = filename.text

        sourceurl = resource_tag.find("resource-attributes/source-url")
        if sourceurl != None and sourceurl.text:
            self.sourceurl = sourceurl.text

    def get_md(self):
        return f"![](data:image/png;base64,{self.base64})"

    def write(self, path):
        with open(path, "wb") as file:
            file.write(self.binary)


class Note:
    def __init__(self, note_tag):
        self.resources = []
        self.attributes = {}
        self.is_bookmark = False

        for property in note_tag:
            if property.tag in ("title", "created", "updated", "content"):
                setattr(self, property.tag, property.text)

            if property.tag == "resource":
                self.resources.append(Resource(property))

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

    def get_resource(self, hash):
        for resource in self.resources:
            if resource.hash == hash:
                return resource
        return None

    def get_content(self):
        con = ENML_PY.ENMLToText(self.content, media_store=Enml_resource_finder(self))
        return re.sub(r"\n\s*\n", "\n\n", con)

    def get_meta_list(self):
        ret = "---\n"
        for k, v in self.attributes.items():
            ret += f"{k}: {v}\n"
        ret += "---\n\n"

        return ret

    def write_as_html(self, path):
        with open(path, "w") as file:
            file.write(self.content)

    def write(self, note_dir):
        target_path = os.path.join(note_dir, self.get_filename())

        with open(target_path, "w") as file:
            file.write(self.get_meta_list())
            file.write(f"\n\n{self.get_content()}")

        return target_path


class Notepad:
    def __init__(self, inputfile):
        self.root = ET.parse(inputfile).getroot()
        self.notes = []

        self.read_notes()

    def read_notes(self):
        for note_tag in self.root.findall("note"):
            note = Note(note_tag)
            self.notes.append(note)

    def write_notes(self, outputdir):
        for note in self.notes:
            path = note.write(outputdir)
            print("Wrote " + path)

    def print_note_list(self):
        for (i, note) in enumerate(self.notes):
            print(f"{i} | {note.title} {'#bookmark' if note.is_bookmark else ''}")
