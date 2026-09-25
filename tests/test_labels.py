"""Independently rasterize the exported SVG paths and decode with ZXing-C++."""
import json
import re
import sys
import unittest
import xml.etree.ElementTree as ET
import build
sys.path.insert(0, str(build.registry.ROOT / '.tools'))
from PIL import Image, ImageDraw
import zxingcpp

class LabelTests(unittest.TestCase):
    def test_every_published_label_decodes_to_exact_stable_address(self):
        root = build.registry.ROOT
        config = json.loads((root/'config.json').read_text())
        data = build.registry.load(root/'data/registry.json')
        for record in data['records']:
            expected = config['resolver_base']+'#id='+record['id']
            svg = ET.fromstring(build.label_svg(expected))
            size = int(svg.attrib['viewBox'].split()[-1])
            path = svg.find('{http://www.w3.org/2000/svg}path').attrib['d']
            for scale in (3,8):
                image = Image.new('RGB',(size*scale,size*scale),'white'); draw=ImageDraw.Draw(image)
                for x,y in re.findall(r'M(\d+),(\d+)h1v1h-1z',path):
                    x,y=int(x),int(y);draw.rectangle((x*scale,y*scale,(x+1)*scale-1,(y+1)*scale-1),fill='black')
                codes=zxingcpp.read_barcodes(image)
                self.assertEqual([code.text for code in codes],[expected])
                self.assertEqual(image.getpixel((0,0)),(255,255,255))

if __name__ == '__main__': unittest.main()
