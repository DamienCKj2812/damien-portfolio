"""Generate exhibit metadata from the approved project catalogue.

The short display titles, summaries and tags are deliberately fitted to physical
cards. Full reviewed text, role qualifiers and result context remain verbatim in
the meeting-room sections. Repository URLs are explicit, never inferred from IDs.
"""
import hashlib
import json
from pathlib import Path
import re
import textwrap

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/project-catalogue.md'
OUTPUT = Path(__file__).resolve().parent / 'projects.json'
GITHUB = 'https://github.com/'


def repo(identity, title, path):
    return {'id': identity, 'title': title, 'url': GITHUB + path}


DESCRIPTORS = [
    {'id':'agent-property','title':'Agent Property','summary':'Bilingual property website\nand CMS integration.',
     'video':{'preview':'videos/myrumawip-preview.mp4','full':'videos/myrumawip-full.mp4',
              'previewFallback':'videos/myrumawip-preview-h264.mp4','fullFallback':'videos/myrumawip-full-h264.mp4',
              'poster':'videos/myrumawip-poster.jpg','width':4.6,'height':2.5875},
     'liveUrl':'https://myrumawip.com/','liveLabel':'Website','liveStatus':'public',
     'tags':['Next.js / TypeScript','Strapi / PostgreSQL','Docker / Ansible'],
     'repositories':[repo('agent-property','Repository','DamienCKj2812/agent-limenghar-property')]},
    {'id':'report-automation','title':'MyReport','summary':'WhatsApp customer workspace\nand reviewed AI assistance.',
     'video':{'preview':'videos/myreport-preview.mp4','full':'videos/myreport-full.mp4',
              'previewFallback':'videos/myreport-preview-h264.mp4','fullFallback':'videos/myreport-full-h264.mp4',
              'poster':'videos/myreport-poster.jpg','width':4.6,'height':2.5875},
     'liveStatus':'private','liveNote':'Hosted privately via Tailscale; not publicly accessible.',
     'tags':['Next.js / TypeScript','Supabase / WAHA','Google Calendar'],
     'repositories':[repo('report-automation','Repository','DamienCKj2812/report-automation')]},
    {'id':'Aria','title':'DWMLight / ANVA CMS','summary':'Multilingual product website\nand custom CMS backend.',
     'video':{'preview':'videos/dwmlight-preview.mp4','full':'videos/dwmlight-full.mp4',
              'previewFallback':'videos/dwmlight-preview-h264.mp4','fullFallback':'videos/dwmlight-full-h264.mp4',
              'poster':'videos/dwmlight-poster.jpg','width':4.6,'height':2.5875},
     'liveUrl':'https://dwmlight.com/en','liveLabel':'Website','liveStatus':'public',
     'tags':['TypeScript / Express','MongoDB / AJV','PM2 / OpenTelemetry'],
     'repositories':[repo('Aria','DWMLight website','maxscale-io/Aria'),repo('anva-cms','ANVA CMS backend','maxscale-io/anva-cms')]},
    {'id':'amplifii','title':'AMPLYFII (Ampress)','summary':'Influencer partnerships\nand campaign management.',
     'liveUrl':'https://amplyfii.io/login?redirect=%2F','liveLabel':'Preview (unreleased)','liveStatus':'unreleased',
     'tags':['Influencer marketing','Product development','Team collaboration'],
     'repositories':[]},
    {'id':'fyp','title':'FYP / Hybrid Anomaly\nDetection','featured':True,'summary':'Hybrid anomaly detection for\nmicroservice observability.',
     'tags':['Go / Python','XGBoost / LOF','OpenTelemetry / Redis'],
     'repositories':[repo('logging-loading','Load and chaos tooling','DamienCKj2812/logging-loading'),repo('logging-microservice','Backend and ML','DamienCKj2812/logging-microservice'),repo('logging-microservice-ui','Observability dashboard','DamienCKj2812/logging-microservice-ui')]},
    {'id':'ConcurrentProgrammingAssignment','title':'Concurrent Programming\nAirport Simulation','summary':'Aircraft threads and shared\nrunway, gate and fuel resources.',
     'tags':['Java / Maven','Threads / Semaphores','Concurrency'],
     'repositories':[repo('ConcurrentProgrammingAssignment','Repository','DamienCKj2812/ConcurrentProgrammingAssignment')]},
    {'id':'DSTRAssignment','title':'Data Structures\nAnalytics and Tournaments','summary':'Two-part data structures:\nanalytics and tournaments.',
     'tags':['C++ / Templates','Lists / Queues / Stacks','Searching / Sorting'],
     'repositories':[repo('DSTRAssignment','Part 1 / Analytics','DamienCKj2812/DSTRAssignment'),repo('DSTRAssignmentPart2','Part 2 / Tournaments','DamienCKj2812/DSTRAssignmentPart2')]},
    {'id':'DTMAssignment','title':'DTM / Coupon Data\nPreparation and EDA','summary':'Coupon-data preprocessing\nand exploratory analysis.',
     'tags':['R / dplyr','mice / ggplot2','Data preparation'],
     'repositories':[repo('DTMAssignment','Repository','DamienCKj2812/DTMAssignment')]},
    {'id':'Java-Programming-G18-','title':'Java G18 / Service\nCentre Management','summary':'Service jobs, appointments,\npayments and feedback.',
     'tags':['Java / Swing','File persistence','Desktop workflows'],
     'repositories':[repo('Java-Programming-G18-','Repository','DamienCKj2812/Java-Programming-G18-')]},
    {'id':'OODJ','title':'OODJ / Purchasing\nand Inventory','summary':'Role-based purchasing and\ninventory management.',
     'tags':['Java / Swing','Object-oriented','File persistence'],
     'repositories':[repo('OODJ','Repository','DamienCKj2812/OODJ')]},
    {'id':'PFDAGroupAssignment','title':'PFDA / Credit-risk\nData Analysis','summary':'Credit-risk cleaning, EDA\nand predictive experiments.',
     'tags':['R / dplyr','caret / randomForest','Statistical analysis'],
     'repositories':[repo('PFDAGroupAssignment','Repository','DamienCKj2812/PFDAGroupAssignment')]},
    {'id':'txsa-group-assignment','title':'TXSA / Comparative\nText Preprocessing','summary':'Compare tokenization,\nstop words and punctuation.',
     'tags':['Python / Jupyter','NLTK / TextBlob','Text preprocessing'],
     'repositories':[repo('txsa-group-assignment','Repository','DamienCKj2812/txsa-group-assignment')]},
    {'id':'SDMGroupAssignment','title':'SDM / Recruitment\nWorkflow Prototype','summary':'Multi-role recruitment and\nemployment UI prototype.',
     'tags':['React / Vite','React Router / Recoil','Frontend prototype'],
     'repositories':[repo('SDMGroupAssignment','Repository','DamienCKj2812/SDMGroupAssignment')]},
    {'id':'rust-gcs-ocs-assignment','title':'RTS / Ground and\nOnboard Control','summary':'Timed commands, telemetry\nand control-state simulation.',
     'tags':['Rust / Cargo','TCP / Scheduling','GCS contribution'],
     'repositories':[repo('rust-gcs-ocs-assignment','Repository','BaconCoding74/rust-gcs-ocs-assignment'),repo('gcs-branch','GCS branch','BaconCoding74/rust-gcs-ocs-assignment/tree/gcs-branch'),repo('ocs-branch','OCS branch / context','BaconCoding74/rust-gcs-ocs-assignment/tree/ocs-branch')]},
    {'id':'fedora-dotfiles','title':'Fedora Dotfiles\nWayland Desktop','summary':'Customized Fedora desktop,\nshell and sharing tools.',
     'tags':['Fedora / Hyprland','Quickshell / QML','Python / PyQt6'],
     'repositories':[repo('fedora-dotfiles','Repository','DamienCKj2812/fedora-dotfiles')]},
    {'id':'damien-portfolio','title':'Damien Portfolio','summary':'This immersive 3D portfolio:\nBlender-authored web spaces.',
     'tags':['React / Three.js','Blender / Python','Demand rendering'],
     'repositories':[repo('damien-portfolio','GitHub / currently empty','DamienCKj2812/damien-portfolio')]},
]


def build():
    source = SOURCE.read_text()
    entries = re.findall(r'^### (\d+)\. ([^\n]+)\n(.*?)(?=^### \d+\.|^---\s*$|\Z)', source, re.M | re.S)
    assert len(entries) == len(DESCRIPTORS) == 16, 'Update the explicit exhibit mapping when the catalogue inventory changes.'
    projects = []
    for descriptor, (number, title, body) in zip(DESCRIPTORS, entries):
        number = int(number)
        section = 'client' if number <= 4 else 'academic' if number <= 14 else 'personal'
        pieces = re.split(r'^#### ([^\n]+)\n', body, flags=re.M)
        sections = [{'heading': pieces[index].strip(), 'markdown': pieces[index+1].strip()}
                    for index in range(1, len(pieces), 2)]
        overview = next(item['markdown'] for item in sections if item['heading'] == 'Overview')
        for repository in descriptor['repositories']:
            url = repository['url']
            verified = url in body or '/tree/' in url and url.split('/tree/')[0] in body and url.split('/tree/')[1] in body
            assert verified, f'Unverified catalogue link: {url}'
        if descriptor.get('liveUrl'):
            assert descriptor['liveUrl'] in body, f'Website URL missing from catalogue: {descriptor["id"]}'
        summary = '\n'.join(line for paragraph in descriptor['summary'].split('\n') for line in textwrap.wrap(paragraph, width=29))
        projects.append({**descriptor, 'summary':summary, 'section':section,
                         'category': 'FEATURED / FINAL YEAR PROJECT' if descriptor.get('featured') else 'CLIENT / REAL WORLD' if section == 'client' else 'ACADEMIC ASSIGNMENT' if section == 'academic' else 'PERSONAL PROJECT',
                         'catalogueNumber':number, 'catalogueTitle':title, 'overview':overview,
                          'catalogueSections':sections, 'url':descriptor['repositories'][0]['url'] if descriptor['repositories'] else None})
    output = {'source':'docs/project-catalogue.md', 'reviewed':'2026-10-06',
              'catalogueSourceHash': hashlib.sha256(source.encode()).hexdigest(),
              'description':'Generated from the approved project catalogue; full role, evidence and recorded-result qualifiers are retained.',
              'categories':[{'id':'client','title':'Client / real world project','number':1},
                            {'id':'academic','title':'Academic Assignment','number':2},
                            {'id':'personal','title':'Personal Project','number':3}], 'projects':projects}
    OUTPUT.write_text(json.dumps(output, indent=2, ensure_ascii=False)+'\n')
    print(f'PROJECT CATALOGUE: {len(projects)} exhibits / approved descriptions, roles and links')


if __name__ == '__main__':
    build()
