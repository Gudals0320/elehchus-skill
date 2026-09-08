"""Generate explicitly synthetic edge cases inside a caller-supplied lab folder."""
from io import BytesIO
import json
from pathlib import Path
from PIL import Image


def generate(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    image = Image.new('RGB', (3, 2))
    image.putdata([(240,10,20), (10,240,20), (10,20,240),
                   (200,200,0), (0,200,200), (200,0,200)])
    descriptions = {}

    def save(name, fmt='PNG', top=None, nested=None):
        exif = Image.Exif()
        for key, value in (top or {}).items():
            exif[key] = value
        if nested:
            exif[34665] = nested
        image.save(output / name, format=fmt, exif=exif)
        descriptions[name] = {'format':fmt, 'top_tags':top, 'exif_ifd':nested}

    save('plain.png')
    for orientation in range(1,9):
        save(f'orientation-{orientation}.png', top={274:orientation})
        save(f'orientation-{orientation}.tiff', 'TIFF', top={274:orientation})
    save('invalid-orientation.png', top={274:9})
    save('bad-date.jpg', 'JPEG', nested={36867:'2024:02:30 12:00:00'})
    save('zero-date.jpg', 'JPEG', nested={36867:'0000:00:00 00:00:00'})
    save('naive-date.jpg', 'JPEG', nested={36867:'2024:07:15 00:10:00'})
    save('offset-date.jpg', 'JPEG', nested={36867:'2024:07:15 00:10:00', 36881:'+09:00',37521:'123456789'})
    save('bad-offset.jpg', 'JPEG', nested={36867:'2024:07:15 00:10:00',36881:'+99:00'})
    save('conflicting-date.jpg', 'JPEG', top={36867:'2023:01:01 00:00:00'}, nested={36867:'2024:07:15 00:10:00'})
    save('digitized-only.jpg', 'JPEG', nested={36868:'2024:07:15 00:10:00'})
    save('modified-only.tiff', 'TIFF', top={306:'2024:07:15 00:10:00'})
    save('modified-offset.jpg', 'JPEG', top={306:'2024:07:15 00:10:00'}, nested={36880:'+09:00',37520:'25'})
    save('metadata-a.png', top={270:'version A'})
    save('metadata-b.png', top={270:'version B'})
    save('filename-is-wrong.jpg', 'PNG')
    jpeg = BytesIO()
    image.resize((32,24)).save(jpeg, 'JPEG')
    (output/'missing-jpeg-eoi.jpg').write_bytes(jpeg.getvalue()[:-2])
    descriptions['missing-jpeg-eoi.jpg'] = {'injected_fault':'last two JPEG EOI bytes removed'}
    png = bytearray((output/'plain.png').read_bytes())
    position = png.find(b'IDAT')
    length = int.from_bytes(png[position-4:position], 'big')
    png[position+4+length] ^= 1
    (output/'bad-png-crc.png').write_bytes(png)
    descriptions['bad-png-crc.png'] = {'injected_fault':'IDAT CRC one bit flipped'}
    second = Image.new('RGB',(3,2),'black')
    image.save(output/'two-frame.tiff', save_all=True, append_images=[second])
    descriptions['two-frame.tiff'] = {'format':'TIFF','frames':2}
    (output/'pretend.heic').write_bytes(b'synthetic non-HEIC input, not a codec support test')
    (output/'empty.jpg').write_bytes(b'')
    (output/'fixture-manifest.json').write_text(json.dumps(descriptions,indent=2),encoding='utf-8')
    return output


if __name__=='__main__':
    import sys
    generate(sys.argv[1])
