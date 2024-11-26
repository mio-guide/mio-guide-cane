import os
import shutil
import pandas as pd

from tqdm import tqdm
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from treepoem import generate_barcode
from gtts import gTTS


BASE_PATH     = '.'
INPUT_PATH    = f'{BASE_PATH}/input'
OUTPUT_PATH   = f'{BASE_PATH}/output'
TEMPLATE_PATH = f'{BASE_PATH}/template'

TUTORIAL      = f'{TEMPLATE_PATH}/tutorial.mp3'
TEMPLATE      = f'{TEMPLATE_PATH}/template.html'
STYLING       = f'{TEMPLATE_PATH}/style.css'
BEEPS         = f'{TEMPLATE_PATH}/beeps'

CODES_PATH    = f'{OUTPUT_PATH}/codes'
TRACKS_PATH   = f'{OUTPUT_PATH}/tracks'


DIRECTIONS = ['N', 'O', 'S', 'W']


class Resource():
    
    def __init__(self, path, file):
        self.path = path
        self.file = file
    
    def save(self):
        pass


class Node():
    
    def __init__(self, path, id, name, content=None):
        
        self.id      = id
        self.name    = name
        self.content = content

        self.code = Code(f'{path}/codes', id, id)

        self.tracks = TrackFactory.create(f'{path}/tracks', id, name, content) if content else []

        self.resources = [self.code] + self.tracks


class Code(Resource):
    
    def __init__(self, path, file, data):
        super().__init__(path, file)

        self.data = data
    
    def save(self):
        img = generate_barcode(
          barcode_type='datamatrix',
          data=self.data,
          scale=5
        )

        img.save(f'{self.path}/{self.file}.png')
    
    def to_tag(self, prefix):
        img = soup.new_tag('img', src=f'{prefix}/{self.file}.png')

        p = soup.new_tag('p')
        p.string = self.file

        outer_div = soup.new_tag('div')
        inner_div = soup.new_tag('div')
        inner_div.append(img)
        outer_div.append(inner_div)
        outer_div.append(p)

        return outer_div


class Track(Resource):
    
    def __init__(self, path, file, text):
        super().__init__(path, file)

        self.text = text
    
    def save(self):
        tts = gTTS(self.text, lang='de')
        tts.save(f'{self.path}/{self.file}.mp3')


class TrackFactory():
    
    DIRECTION_TEMPLATE = '%s: %s.'
    DIRECTION_NAME     = ['geradeaus', 'rechts', 'zurück', 'links']
    
    def create(path, id, name, content):
        if len(content) == 1: return [Track(path, id, f'{name}. {content[0]}')]
        if len(content) == 4: return [
            Track(path, f'{id}_{DIRECTIONS[i]}', f'{name}. %s' % ' '.join([
                TrackFactory.DIRECTION_TEMPLATE % (text, TrackFactory.DIRECTION_NAME[j])
                for j, text in zip(range(4), content[4 - i:] + content[:4 - i])
                if j != 2 and text != '.'
            ]))
            for i in range(4)
        ]


def generate_ids(min, max=int(1e8 - 1)):
    return map(lambda id: f'{id}', iter(range(min, max + 1)))


def parse_content(content):
    inline, *_ = content.children
    return inline.content


def parse_list(list):
    for item in list.children:
        paragraph, *_ = item.children
        inline,    *_ = paragraph.children
        yield inline.content


# setup

shutil.rmtree(OUTPUT_PATH, ignore_errors=True)

for path in [OUTPUT_PATH, CODES_PATH, TRACKS_PATH]: os.mkdir(path)

shutil.copyfile(STYLING, f'{OUTPUT_PATH}/style.css')
shutil.copytree(BEEPS, f'{OUTPUT_PATH}/tracks', dirs_exist_ok=True)


# input

with open(TEMPLATE, 'r') as f: template = f.read()

soup = BeautifulSoup(template, 'html.parser')

content = []

for file in os.listdir(INPUT_PATH):
    if file.endswith('.md'):
        path = f'{INPUT_PATH}/{file}'
        with open(path, 'r') as f:
            content.append(f.read())

input = '\n'.join(content)


# parsing

md     = MarkdownIt()
tokens = md.parse(input)
root   = SyntaxTreeNode(tokens)

direction_ids = generate_ids(0, 99)
simple_ids    = generate_ids(100)

tutorial = Node(OUTPUT_PATH, next(simple_ids), 'Tutorial')

shutil.copyfile(TUTORIAL, f'{TRACKS_PATH}/{tutorial.id}.mp3')

nodes = [tutorial]

headings = []

for curr in root.children:
    if curr.type == 'heading':
        text  = parse_content(curr)
        level = int(curr.tag[1])

        headings = [
            heading for heading in headings
            if heading['level'] < level
        ]

        headings.append({
            'text':  text,
            'level': level
        })

    elif curr.type == 'paragraph':
        prev = curr.previous_sibling

        id   = next(simple_ids)
        name = '. '.join(map(lambda h: h['text'], headings))
        data = [parse_content(curr)]

        node = Node(OUTPUT_PATH, id, name, data)

        nodes.append(node)

    elif curr.type == 'bullet_list':
        prev = curr.previous_sibling

        id   = next(direction_ids)
        name = '. '.join(map(lambda h: h['text'], headings))
        data = list(parse_list(curr))

        node = Node(OUTPUT_PATH, id, name, data)

        nodes.append(node)


# output

mappings = []

for node in tqdm(nodes):
    soup.div.append(node.code.to_tag('codes'))
    mappings.append((node.id, node.name))
    
    for resource in node.resources: resource.save()

table = pd.DataFrame(mappings, columns=['ID', 'Name'])
table.to_excel(f'{OUTPUT_PATH}/mapping.xlsx', index=False)

with open(f'{OUTPUT_PATH}/codes.html', 'w') as f: f.write(soup.prettify())
