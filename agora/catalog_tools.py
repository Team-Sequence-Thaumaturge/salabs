import os
import re
import json

tools_dir = 'C:/stella/project/web/salabs/tools'
tools = []

for f in sorted(os.listdir(tools_dir)):
    if not f.endswith('.html'):
        continue
    slug = f[:-5]
    fpath = os.path.join(tools_dir, f)
    try:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
            txt = fp.read()
        
        t_match = re.search(r'<title>(.*?)</title>', txt, re.I)
        title = t_match.group(1).split('-')[0].strip() if t_match else slug.replace('-', ' ').title()
        
        d_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', txt, re.I)
        desc = d_match.group(1).strip() if d_match else '100% Client-side pure JS utility tool.'
        
        cat = 'general_utilities'
        if slug.startswith('audio-'): cat = 'audio_dsp_spatial'
        elif slug.startswith('image-') or 'canvas' in slug: cat = 'image_graphics'
        elif 'crypto' in slug or 'hash' in slug or 'base' in slug: cat = 'security_crypto'
        elif '3d' in slug or 'mesh' in slug or 'spatial' in slug: cat = 'spatial_3d_cad'
        elif 'text' in slug or 'string' in slug or 'json' in slug or 'diff' in slug: cat = 'text_data_parsing'
        elif 'calc' in slug or 'math' in slug or 'unit' in slug: cat = 'math_scientific'
        elif 'css' in slug or 'html' in slug or 'color' in slug: cat = 'frontend_web'
        
        tools.append({
            'slug': slug,
            'title': title,
            'category': cat,
            'url': f'https://salabs.quanxs.com/tools/{f}',
            'description': desc[:120]
        })
    except Exception:
        pass

print(f'Successfully cataloged {len(tools)} tools!')
categories = {}
for t in tools:
    c = t['category']
    categories[c] = categories.get(c, 0) + 1

for k, v in sorted(categories.items()):
    print(f' - {k}: {v} tools')

out_path = 'C:/stella/project/web/salabs/agora/salabs-tools-catalog.json'
with open(out_path, 'w', encoding='utf-8') as fp:
    json.dump(tools, fp, indent=2, ensure_ascii=False)
print('Saved catalog to:', out_path)
