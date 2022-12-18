from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict, astuple
from typing import Dict
from datetime import datetime
from pathlib import Path
import requests
import hashlib
import json


@dataclass
class SourceBase:
    """Something."""

    title: str
    filename: str
    foldername: str
    folders: list[str]
    description: str
    installed: datetime
    added: datetime
    updated: datetime
    checksum: str
    size: str
    url: str
    download_url: str

    @classmethod
    def from_url(cls, url: str):
        raise NotImplementedError()

    @classmethod
    def from_dict(cls, entry: Dict[str, str]):
        """Initialize from a dictionary."""
        raise NotImplementedError()

    def to_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "filename": self.filename,
            "foldername": self.foldername,
            "folders": self.folders,
            "description": self.description,
            "installed": str(self.installed),
            "added": str(self.added),
            "updated": str(self.updated),
            "size": self.size,
            "checksum": self.checksum,
            "url": self.url,
            "download_url": self.download_url,
        }

    def update(self):
        raise NotImplementedError()

    def check_if_file_exists(self, downloaded_file: Path):
        try:
            if self.checksum:
                # check if the file is actually downloaded
                with open(downloaded_file, "rb") as fp:
                    file_bytes = fp.read()
                    readable_hash = hashlib.md5(file_bytes).hexdigest()
                    if readable_hash == self.checksum:
                        return True
        except FileNotFoundError:
            return False

    def get_download_url(self) -> str:
        raise NotImplementedError()

    def download_file(self, write_folder: Path):
        """Download a file."""
        write_path = write_folder / self.filename

        r = requests.get(self.get_download_url())
        with open(write_path, "wb") as fp:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    fp.write(chunk)
        return


@dataclass
class SourceModdb(SourceBase):
    """Something."""

    BASE_URL = "https://www.moddb.com"

    @classmethod
    def from_url(cls, url: str, folders: list[str] = None):
        """Initialize from url."""
        site_content = requests.get(url).text
        site = BeautifulSoup(site_content, "html.parser")
        try:
            updated = datetime.fromisoformat(
                site.find(text="Updated").parent.parent.time["datetime"]
            )
        except AttributeError:
            updated = None
        return cls(
            title=site.head.title.string,
            filename=site.find(text="Filename").parent.parent.span.text.strip(),
            description=site.find(attrs={"name": "description"})["content"],
            added=datetime.fromisoformat(
                site.find(text="Added").parent.parent.time["datetime"]
            ),
            installed="1900-01-01 00:00:00+00:00",
            updated=updated,
            size=site.find(text="Size").parent.parent.span.text.strip(),
            checksum=site.find(text="MD5 Hash").parent.parent.span.text.strip(),
            url=url,
            download_url=site.find(id="downloadmirrorstoggle")["href"].strip(),
            foldername=site.get("foldername", ""),
            folders=folders,
        )

    @classmethod
    def from_dict(cls, entry: Dict[str, str]):
        """Initialize from a dictionary."""
        return cls(
            title=entry.get("title"),
            filename=entry.get("filename"),
            foldername=entry.get("foldername", ""),
            folders=entry.get("folders"),
            description=entry.get("description"),
            installed=entry.get("installed", "1900-01-01 00:00:00+00:00"),
            added=entry.get("added"),
            updated=entry.get("updated", entry.get("added")),
            size=entry.get("size"),
            checksum=entry.get("checksum"),
            url=entry.get("url"),
            download_url=entry.get("download_url"),
        )

    def update(self):
        """Update object with information from source."""
        site_content = requests.get(self.url).text
        site = BeautifulSoup(site_content, "html.parser")
        self.title = site.head.title.string
        self.filename = site.find(text="Filename").parent.parent.span.text.strip()
        if not self.foldername:
            self.foldername = self.filename.rsplit(".", 1)[0]
        self.description = site.find(attrs={"name": "description"})["content"]
        self.added = datetime.fromisoformat(
            site.find(text="Added").parent.parent.time["datetime"]
        )

        try:
            self.updated = datetime.fromisoformat(
                site.find(text="Updated").parent.parent.time["datetime"]
            )
        except AttributeError:
            self.updated = None
        self.size = site.find(text="Size").parent.parent.span.text.strip()
        self.checksum = site.find(text="MD5 Hash").parent.parent.span.text.strip()
        self.download_url = site.find(id="downloadmirrorstoggle")["href"].strip()

    def get_download_url(self) -> str:
        """Retrieve the actual download link."""
        download = self.BASE_URL + str(self.download_url)
        mirror_site = BeautifulSoup(requests.get(download).text, "html.parser")
        target_href = mirror_site.body.p.a["href"]
        target_url = self.BASE_URL + str(target_href)
        print(f"Got {target_url=}")
        return target_url


@dataclass
class SourceGitHub(SourceBase):
    """Class for handling mods from github."""

    BASE_URL = "https://www.github.com"
    BASE_API_URL = "https://api.github.com"
    html_url: str

    @classmethod
    def parse_api_url(cls, url: str):
        if cls.BASE_API_URL in url:
            return url
        user = url.split("/")[-2]
        project = url.split("/")[-1]
        testing = f"https://api.github.com/repos/{user}/{project}"
        return testing

    @classmethod
    def from_url(cls, url: str, folders: list[str] = None):

        """Initialize from url."""
        api_url = cls.parse_api_url(url)
        content = requests.get(api_url).text
        x = json.loads(content)

        return cls(
            title=x.get("name"),
            filename=f"{x.get('name')}_git.zip",
            description=x.get("description"),
            added=datetime.fromisoformat(x.get("created_at")),
            updated=datetime.fromisoformat(x.get("pushed_at")),
            size=f"{x.get('size')}kb",
            checksum="",
            html_url=x.get("html_url"),
            url=x.get("url"),
            download_url=f"{api_url}/zipball",
            foldername=x.get("name"),
            folders=folders,
            installed="1900-01-01 00:00:00+00:00",
        )

    @classmethod
    def from_dict(cls, entry: Dict[str, str]):
        return cls(
            title=entry.get("title"),
            filename=entry.get("filename"),
            foldername=entry.get("foldername", ""),
            folders=entry.get("folders"),
            description=entry.get("description"),
            installed=entry.get("installed", "1900-01-01 00:00:00+00:00"),
            added=entry.get("added"),
            updated=entry.get("updated", entry.get("added")),
            size=entry.get("size"),
            checksum=entry.get("checksum"),
            url=entry.get("url"),
            html_url=entry.get("html_url"),
            download_url=entry.get("download_url"),
        )

    def update(self):
        """Update object with information from source."""
        content = requests.get(self.url).text
        x = json.loads(content)
        self.title = x.get("name")
        if not self.foldername:
            self.foldername = self.filename.rsplit(".", 1)[0]
        self.description = x.get("description")
        self.added = datetime.fromisoformat(x.get("created_at"))

        try:
            self.updated = datetime.fromisoformat(x.get("pushed_at"))
        except AttributeError:
            self.updated = None
        self.size = x.get("size")
        self.checksum = ""
        self.download_url = f"{x.get('url')}/zipball"

    def get_download_url(self) -> str:
        """Retrieve the actual download link."""
        return self.download_url


def get_class_classifier(url: str) -> SourceBase:
    if "moddb.com" in url:
        return SourceModdb
    if "github.com" in url:
        return SourceGitHub
