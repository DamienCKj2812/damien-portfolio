"""Read the card's static contact copy from the website's canonical data."""
import re
from pathlib import Path


def read_contact_details():
    source = (Path(__file__).resolve().parents[2] / 'src/data/portfolio.js').read_text()

    def field(name):
        match = re.search(rf"^\s*{name}:\s*'([^']+)'", source, re.MULTILINE)
        if not match:
            raise ValueError(f'Contact card requires a literal portfolio.{name}')
        return match.group(1)

    def link(identity):
        match = re.search(r"\{\s*id:\s*'" + re.escape(identity) + r"'[^}]*href:\s*'([^']+)'", source)
        if not match:
            raise ValueError(f'Contact card requires the {identity} contact link')
        return match.group(1)

    return {'name': field('name'), 'email': field('email'), 'phone': field('phone'),
            'github': link('github'), 'whatsapp': link('whatsapp')}


def contact_card_lines(details):
    return [
        ('name', details['name'].upper(), .016, .008),
        ('invitation', "LET'S CONNECT", .0085, .0028),
        ('email', details['email'], .0015, .0026),
        ('phone', details['phone'], -.0045, .0026),
        ('whatsapp', 'WhatsApp / ' + details['whatsapp'].removeprefix('https://'), -.0105, .0024),
        ('contact link', details['github'].removeprefix('https://'), -.0165, .00225),
        ('contact label', 'CONTACT / VIEW DETAILS', -.023, .0017),
    ]
