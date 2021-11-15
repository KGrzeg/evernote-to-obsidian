import xml.etree.ElementTree as ET
import os, re, base64, hashlib
from datetime import datetime

import ENML_PY
import pdfkit

from utils import safe_open, basename_without_ext

MAX_FILENAME_LENGTH = 90
ENEX_DATATIME_FORMAT = "%Y%m%dT%H%M%SZ"
NOTE_DATE_PREFIX_FORMAT = "%Y-%m-%d"


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
        if len(base) > MAX_FILENAME_LENGTH:
            base = base[:MAX_FILENAME_LENGTH]

        _, ext = os.path.splitext(self.filename)
        self.filename = f"{base}{ext}"

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
                res = Resource(property, used_names)
                self.resources.append(res)
                used_names.append(res.filename)

            if property.tag == "note-attributes":
                for attr in property:
                    self.attributes[attr.tag] = attr.text
                    if attr.tag == "source-url":
                        self.is_bookmark = True

        self.filename = re.sub('[*"\/<>:|?]', "", self.title)
        if len(self.filename) > MAX_FILENAME_LENGTH:
            self.filename = self.filename[:MAX_FILENAME_LENGTH]
            self.attributes["original_title"] = self.title

    def get_resource_by_filename(self, filename):
        for res in self.resources:
            if res.get_filename() == filename:
                return res
        return None

    def get_filename(self, ext="md"):
        created = datetime.strptime(self.created, ENEX_DATATIME_FORMAT)
        datestr = created.strftime(NOTE_DATE_PREFIX_FORMAT)

        if ext:
            return f"{datestr}-{self.filename}.{ext}"

        return f"{datestr}-{self.filename}"

    def get_resource(self, hash):
        for resource in self.resources:
            if resource.hash == hash:
                return resource
        return None

    def get_content_md(self):
        content = ENML_PY.ENMLToText(
            self.content, media_store=Enml_resource_finder(self)
        )
        return re.sub(r"\n\s*\n", "\n\n", content)

    def filename_to_b64(self, match):
        res = self.get_resource_by_filename(match.group(1))

        if not res:
            return match.group(0)

        return f'src="data:{res.mime};base64,{res.base64}"'

    def get_content_html(self):
        content = ENML_PY.ENMLToHTML(
            self.content, media_store=Enml_resource_finder(self)
        )
        html = content.decode("utf-8")

        # transform images' srcs to base64
        html = re.sub(r'src="([^"]+)"', self.filename_to_b64, html)

        return re.sub(r"\n\s*\n", "\n\n", html)

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

    def write_resources(self, dir):
        paths = ()
        for resource in self.resources:
            path = resource.write(dir)
            paths = (*paths, path)

        return paths

    def write_pdf(self, pdf_dir):
        pdf_path = os.path.join(pdf_dir, self.get_filename(ext="pdf"))
        html = self.get_content_html()

        try:
            ok = pdfkit.from_string(html, pdf_path, options={"quiet": ""})

            if not ok:
                raise self.__class__.__name__ + RuntimeError(
                    "Error while saving PDF " + pdf_path
                )

        # Any idea how to catch ProtocolUnknownError only?
        except:
            pass

        return (pdf_path,)

    def write_md(self, note_dir, prefix=""):
        note_path = os.path.join(note_dir, self.get_filename())

        with safe_open(note_path, "w") as file:
            file.write(self.get_meta_list())
            if prefix:
                file.write(f"\n\n{prefix}")
            file.write(f"\n\n{self.get_content_md()}")

        return (note_path,)

    def write(self, note_dir, attachmentdir, dumpres):
        pdf_path, note_path, res_paths = (), (), ()

        if self.is_bookmark:
            pdf_path = self.write_pdf(attachmentdir)
            prefix = f'![[{ self.get_filename(ext="pdf") }]]'
            note_path = self.write_md(note_dir, prefix)
        else:
            note_path = self.write_md(note_dir)

        if dumpres:
            res_paths = self.write_resources(attachmentdir)

        return (*note_path, *pdf_path, *res_paths)


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
        for (i, note) in enumerate(self.notes, start=1):
            paths = note.write(outputdir, attachmentdir, dumpres)

            for path in paths:
                print("Saved " + path)
                print(f"Progress {i}/{len(self.notes)}")

    def print_note_list(self):
        for (i, note) in enumerate(self.notes):
            print(f"{i} | {note.title} {'#bookmark' if note.is_bookmark else ''}")
