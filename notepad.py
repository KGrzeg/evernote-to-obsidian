import xml.etree.ElementTree as ET
import os, re, base64, hashlib

import ENML_PY

from utils import safe_open, basename_without_ext


def get_meta_extension(mime):
    try:
        return ENML_PY.MIME_TO_EXTESION_MAPPING[mime]
    except KeyError:
        return ".unkown"


class Enml_resource_finder:
    def __init__(self, note):
        self.note = note

    def save(self, hash_str, mime_type):
        res = self.note.get_resource(hash_str)

        if res != None:
            return res.get_filename()

        else:
            print("Resource not found")
            return "_undefined_resource_"


class Resource:
    def __init__(self, resource_tag, used_names=[]):
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

        base = basename_without_ext(self.filename)
        _, ext = os.path.splitext(self.filename)
        counter = 1
        while self.filename in used_names:
            self.filename = f"{base}_{counter}{ext}"
            counter += 1

        sourceurl = resource_tag.find("resource-attributes/source-url")
        if sourceurl != None and sourceurl.text:
            self.sourceurl = sourceurl.text

    def get_md(self):
        return f"![](data:image/png;base64,{self.base64})"

    def get_filename(self):
        ext = get_meta_extension(self.mime)
        if self.filename:
            file = basename_without_ext(self.filename)
            return f"{file}{ext}"

        raise RuntimeError(self.__class__.__name__ + " can't figure out filename")

    def write(self, directory):
        path = os.path.join(directory, self.get_filename())

        with safe_open(path, "wb") as file:
            file.write(self.binary)

        return path


class Note:
    def __init__(self, note_tag, used_names=[]):
        self.resources = []
        self.attributes = {}
        self.is_bookmark = False

        for property in note_tag:
            if property.tag in ("title", "created", "updated", "content"):
                setattr(self, property.tag, property.text)

            if property.tag == "resource":
                self.resources.append(Resource(property, used_names))

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
        ret += "---\n"

        return ret

    def get_resource_names(self):
        names = []
        for res in self.resources:
            names.append(res.get_filename())

        return names

    def write_as_html(self, path):
        with open(path, "w") as file:
            file.write(self.content)

    def write_resources(self, dir):
        paths = ()
        for resource in self.resources:
            path = resource.write(dir)
            paths = (*paths, path)

        return paths

    def write(self, note_dir, attachmentdir, dumpres):
        note_path = os.path.join(note_dir, self.get_filename())

        with safe_open(note_path, "w") as file:
            file.write(self.get_meta_list())
            file.write(f"\n\n{self.get_content()}")

        res_paths = ()
        if dumpres:
            res_paths = self.write_resources(attachmentdir)

        return (note_path, *res_paths)


class Notepad:
    def __init__(self, inputfile):
        self.root = ET.parse(inputfile).getroot()
        self.notes = []
        self.resource_names = []

        self.read_notes()

    def read_notes(self):
        for note_tag in self.root.findall("note"):
            note = Note(note_tag, self.resource_names)
            self.notes.append(note)

            if note.get_resource_names():
                self.resource_names.extend(note.get_resource_names())

    def write_notes(self, outputdir, attachmentdir, dumpres):
        for note in self.notes:
            paths = note.write(outputdir, attachmentdir, dumpres)

            for path in paths:
                print("Saved " + path)

    def print_note_list(self):
        for (i, note) in enumerate(self.notes):
            print(f"{i} | {note.title} {'#bookmark' if note.is_bookmark else ''}")
