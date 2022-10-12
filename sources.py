from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict, astuple
from typing import Dict
from datetime import datetime
from pathlib import Path
import requests

BASE_URL = "https://www.moddb.com"

@dataclass
class SourceModdb:
    """Something."""

    title: str
    filename: str
    foldername: str
    folders: list[str]
    description: str
    installed: datetime
    added: datetime
    updated: datetime
    size: str
    url: str
    download_url: str

    @classmethod
    def from_url(cls, url: str):
        """Initialize from url."""
        site_content = requests.get(url).text
        site = BeautifulSoup(site_content, 'html.parser')
        return cls(
                   title = site.head.title.string,
                   filename = site.find(text="Filename").parent.parent.span.text.strip(),
                   description = site.find(attrs={'name': 'description'})['content'],
                   added = datetime.fromisoformat(site.find(text="Added").parent.parent.time['datetime']),
                   updated = datetime.fromisoformat(site.find(text="Updated").parent.parent.time['datetime']),
                   size = site.find(text="Size").parent.parent.span.text.strip(),
                   url = url,
                   download_url = site.find(id='downloadmirrorstoggle')['href'].strip()
                   )

    @classmethod
    def from_dict(cls, entry: Dict[str, str]):
        """Initialize from a dictionary."""
        return cls(
                   title = entry.get('title'),
                   filename = entry.get('filename'),
                   foldername = entry.get('foldername', ""),
                   folders = entry.get('folders'),
                   description = entry.get('description'),
                   installed = entry.get('installed', "1900-01-01 00:00:00+00:00"),
                   added = entry.get('added'),
                   updated = entry.get('updated', entry.get('added')),
                   size = entry.get('size'),
                   url = entry.get('url'),
                   download_url = entry.get('download_url')
                   )

    def to_dict(self) -> Dict[str, str]:
        return {
                'title': self.title,
                'filename': self.filename,
                'foldername': self.foldername,
                'folders': self.folders,
                'description': self.description,
                'installed': str(self.installed),
                'added': str(self.added),
                'updated': str(self.updated),
                'size': self.size,
                'download_url': self.download_url
                }

    def update(self):
        """Update object with information from source."""
        site_content = requests.get(self.url).text
        site = BeautifulSoup(site_content, 'html.parser')
        self.title = site.head.title.string
        self.filename = site.find(text="Filename").parent.parent.span.text.strip()
        if not self.foldername:
            self.foldername = self.filename.rsplit(".", 1)[0]
        self.description = site.find(attrs={'name': 'description'})['content']
        self.added = datetime.fromisoformat(site.find(text="Added").parent.parent.time['datetime'])

        try:
            self.updated = datetime.fromisoformat(site.find(text="Updated").parent.parent.time['datetime'])
        except AttributeError:
            self.updated = None
        self.size = site.find(text="Size").parent.parent.span.text.strip()
        self.download_url = site.find(id='downloadmirrorstoggle')['href'].strip()


    def get_download_url(self) -> str:
        """Retrieve the actual download link."""
        download = BASE_URL + str(self.download_url)
        mirror_site = BeautifulSoup(requests.get(download).text, 'html.parser')
        target_href = mirror_site.body.p.a['href']
        target_url = BASE_URL + str(target_href)
        print(f'Got {target_url=}')
        return target_url
    
    def download_file(self, write_folder: Path):
        """Download a file."""
        write_path = write_folder / self.filename
        
        r = requests.get(self.get_download_url())
        with open(write_path, 'wb') as fp:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    fp.write(chunk)
        return
            
