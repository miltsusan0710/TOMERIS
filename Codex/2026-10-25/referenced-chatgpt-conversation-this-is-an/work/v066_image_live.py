import sys,struct,zlib,json
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
from tomeris_multimodal import image_answer
p=Path('work/v066_red.png')
def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
p.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',128,128,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\xff\0\0'*128)*128))+chunk(b'IEND',b''))
answer=image_answer(p,'画像の色を短く答えてください。','gemma3:4b')
Path('work/v066_image_live.txt').write_text(answer,encoding='utf-8')
print(answer)
