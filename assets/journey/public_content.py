"""Strip non-public/organization repository links from published room content."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = set(json.loads((ROOT / 'src/data/repository-visibility.json').read_text())['publicRepositories'])


def is_public_link(href):
    if not href:
        return False
    url = urlparse(href)
    if url.scheme not in {'https', 'http', 'mailto', 'tel'}:
        return False
    host = (url.hostname or '').lower()
    parts = [part for part in url.path.split('/') if part]
    if host in {'gitlab.com', 'bitbucket.org'}:
        return False
    if host in {'github.com', 'www.github.com', 'raw.githubusercontent.com', 'api.github.com'}:
        if host == 'api.github.com' and parts and parts[0] == 'repos':
            parts.pop(0)
        if host in {'github.com', 'www.github.com'} and len(parts) < 2:
            return True
        return '/'.join(parts[:2]).lower() in PUBLIC
    return True


def public_content(value):
    if isinstance(value, list):
        return [public_content(item) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key == 'repositories':
                result[key] = [public_content(repo) for repo in item if is_public_link(repo.get('url'))]
            elif key == 'url' and item and not is_public_link(item):
                result[key] = None
            elif key == 'markdown':
                result[key] = public_markdown(item, value.get('heading', '').lower().startswith('links'))
            else:
                result[key] = public_content(item)
        if 'repositories' in result and 'url' in result and not result['url']:
            result['url'] = result['repositories'][0]['url'] if result['repositories'] else None
        if value.get('repositories') and not result['repositories']:
            result['repositoryLinksRestricted'] = True
        if result.get('repositoryLinksRestricted') and 'catalogueSections' in result:
            sites = result.get('siteLinks', [])
            if result.get('liveUrl'):
                sites = [*sites, {'url': result['liveUrl'], 'label': result.get('liveLabel', 'Website')}]
            unique = {site['url']: site for site in sites if is_public_link(site.get('url'))}
            site_markdown = '\n'.join(f'- [{site["label"]}]({site["url"]})' for site in unique.values())
            result['catalogueSections'] = [{**section, 'markdown': site_markdown} if section['heading'].lower().startswith('links') else section
                                         for section in result['catalogueSections'] if not section['heading'].lower().startswith('links') or site_markdown]
        if 'catalogueSections' in result:
            result['catalogueSections'] = [section for section in result['catalogueSections'] if section['markdown'].strip()]
        return result
    if isinstance(value, str):
        # Preserve explanatory source labels, but never publish the restricted
        # href, including deep blob/tree links and file references in Markdown.
        return public_markdown(value)
    return value


def public_markdown(value, hide_source_rows=False):
    lines = value.split('\n')
    if hide_source_rows:
        lines = [line for line in lines if not re.match(r'^\s*[-*]\s', line)
                 or not any(not is_public_link(match.group(2)) for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', line))]
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                  lambda match: match.group(0) if is_public_link(match.group(2)) else match.group(1), '\n'.join(lines))
