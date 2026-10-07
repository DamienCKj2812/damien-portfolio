"""Read the card's static contact copy from the website's canonical data."""
import json
from pathlib import Path


def read_contact_details():
    source = json.loads((Path(__file__).resolve().parents[2] / 'src/data/portfolio.json').read_text(encoding='utf-8'))
    if not isinstance(source, dict) or not isinstance(source.get('contact'), dict):
        raise ValueError('Contact card requires portfolio.contact')
    contact = source['contact']

    def field(record, name):
        value = record.get(name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'Contact card requires a non-empty {name}')
        return value

    links = contact.get('links')
    if not isinstance(links, list) or any(not isinstance(item, dict) for item in links):
        raise ValueError('Contact card requires portfolio.contact.links')
    identities = [field(item, 'id') for item in links]
    if len(set(identities)) != len(identities):
        raise ValueError('Contact card requires unique contact link IDs')

    def link(identity):
        for item in links:
            if item['id'] == identity:
                return field(item, 'href')
        raise ValueError(f'Contact card requires the {identity} contact link')

    return {'name': field(source, 'name'), 'email': field(contact, 'email'), 'phone': field(contact, 'phone'),
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
