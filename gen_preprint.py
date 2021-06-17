#!/usr/bin/python3

import os, sys, shutil
import bibtexparser

CHECK_IMAGES = True

# remove highlights
NEW_STUFF_CMD = 'newStuff'

class Color:
    PURPLE = '\033[1;35;48m'
    CYAN = '\033[1;36;48m'
    BOLD = '\033[1;37;48m'
    BLUE = '\033[1;34;48m'
    GREEN = '\033[1;32;48m'
    YELLOW = '\033[1;33;48m'
    RED = '\033[1;31;58m'
    BLACK = '\033[1;30;48m'
    UNDERLINE = '\033[4;37;48m'
    END = '\033[1;37;0m'
    def print(s, color):
        print(getattr(Color, color.upper()) + s + Color.END)
    def error(s):
        Color.print(s, 'red')
    def info(s):
        Color.print(s, 'blue')  
    def ok(s):
        Color.print(s, 'green') 
        
def dict_replace(s, d):
    for key in d:
        s = s.replace(key, d[key])
    return s

def tex_arg(s):
    return s.split('{')[1].split('}')[0]

def extract_bib_info(line):
    d = {'bibliographystyle': 'bst', 'bibliography': 'bib'}
    src = []
    dst = [] 
    rep = {}
    for key in d:
        tag = '\\' + key + '{'
        if tag in line:
            for arg in tex_arg(line).split(','):
                arg = arg.strip()
                src.append(get_file(arg + '.' + d[key]))
                dst.append(preprint_dir + os.path.basename(src[-1]))
                rep[arg] = os.path.basename(arg + '.' + d[key])
    return src, dst, rep

def copy_image(src, dest):
    shutil.copy(src, dest)
    if src.endswith('pdf'):
        os.system('sed -i -e "/^\/Group 4 0 R$/d" "{}"'.format(dest))
        
if len(sys.argv) == 1:
    Color.error('Give a tex file or directory containing it')
    sys.exit(0)
    
tex = sys.argv[1]
if not os.path.exists(tex):
    Color.error('File does not exists: ' + tex)
    sys.exit(0)
    
candidates = []
if os.path.isdir(tex):
    for ti in os.listdir(tex):
        if ti.endswith('.tex') and os.path.exists(tex + '/' + ti.replace('.tex','.bbl')):
            candidates.append(tex + '/' + ti)
else:
    candidates = [tex]

if len(candidates) != 1:
    Color.error('Cannot guess target TeX file: ')
    for t in candidates:
        Color.info('   ' + t)
    sys.exit(0)
        
tex = os.path.abspath(candidates[0])
base_dir = os.path.dirname(os.path.abspath(tex))
preprint_dir = base_dir + '_preprint/'
fig_dir = preprint_dir + 'fig/'
base_dir += '/'


if os.path.exists(preprint_dir):
    if '-c' in sys.argv:
        shutil.rmtree(preprint_dir)
    else:
        Color.info(f'Directory already exists: {preprint_dir}')
        r = input('Create zip file (z) or erase (e) [Z/e] ').lower()

        if r not in ('', 'z','e'):
            sys.exit(0)
            
        if r in ('z',''):
            os.chdir(preprint_dir)
            
            dest = 'FINAL_VERSION'
            
            if os.path.exists(dest + '.zip'):
                os.remove(dest + '.zip')
            
            cmd = f'zip -r "{dest}.zip" . -x "{dest}.PDF"'
            for f in os.listdir(preprint_dir):
                ext = os.path.splitext(f)[-1][1:]
                if ext in ('PDF','pdf','bbl', 'blg','gz','out','log','aux','zip','odt','bak','xlsx'):
                    cmd += f' -x "{f}"'
            if os.path.exists(dest + '.pdf'):
                shutil.move(dest + '.pdf', dest + '.PDF')
            Color.info('Running: ' + cmd)
            os.system(cmd)
            Color.ok(f'Created {dest}.zip')
            sys.exit(0)
            
        shutil.rmtree(preprint_dir)

os.mkdir(preprint_dir)
os.mkdir(fig_dir)

Color.ok('Creating preprint from ' + tex)

try:
    texinputs =  os.environ['TEXINPUTS'].split(':')
    texinputs[0] = base_dir
except:
    texinputs = [base_dir]

def get_file(tag):
    for src in texinputs:
        if os.path.exists(src + tag):
            return src + tag    
    Color.error('File not found: ' + tag)
    sys.exit(0)
    
def read_tex(tex):
    with open(tex) as f:
        content = f.read().splitlines()
    for i,line in enumerate(content):
        # keep comment symbol but remove the actual comment
        comm = line.find('%')
        if comm != -1:
            line = line[:comm+1]
            
        if '\\input' in line:
            content[i] = read_tex(get_file(tex_arg(line) + '.tex'))
        else:
            content[i] = line
            
    content = '\n'.join(content)
    
    for s,d in (('\n\n\n', '\n\n'), ('%\n%', '%'), ('  %', ' %')):
        while s in content:
            content = content.replace(s, d)
    return content
            
content = read_tex(tex).replace('.eps}', '}')

new_content = []
for key, n in (('pdfsuppresswarningpagegroup', '1'), ('pdfminorversion', '7')):
    new_content.append('\\{}={}'.format(key,n))
    if key in content:
        idx = content.index('\\'+key)
        content = content.replace(content[idx:idx+len(key)+3], '')
        
# remove newStuff
new_stuff_idx = content.find(NEW_STUFF_CMD)
if new_stuff_idx != -1:
    after = new_stuff_idx + len(NEW_STUFF_CMD)
    content = content[:new_stuff_idx] + NEW_STUFF_CMD + content[after:].replace(f'\\{NEW_STUFF_CMD}', '')
        
# add this graphics path anyway
if '\\graphicspath' not in content:
    content = content.replace('\\title', '\\graphicspath{{fig/}}\n\\title', 1)
    
content = content.splitlines()
    
# get where pictures may be coming from

for line in content:
    if '\\graphicspath' in line:
        for d in line.split('{'):
            dest = os.path.abspath(base_dir + d.replace('}','')) + '/'
            if os.path.exists(dest) and dest not in texinputs:
                texinputs.append(dest)

texinputs.append(texinputs[1] + 'authors/')
# look for a relative picture
img_ext = '.png,.pdf,.jpg,.mps,.jpeg,.jbig2,.jb2,.PNG,.PDF,.JPG,.JPEG,.JBIG2,.JB2'.split(',')

def check_image(path):
    
    if not CHECK_IMAGES:
        return path
    from cv2 import imread
    from numpy import sum as np_sum
    from numpy import prod
    
    ext = os.path.splitext(path)[1].lower()[1:]
    if ext in ('png','jpg','jpeg'):
        if ext == 'png':
            from cv2 import IMREAD_UNCHANGED, COLOR_BGR2GRAY, COLOR_BGRA2GRAY, cvtColor
            from numpy import where
            im = imread(path, IMREAD_UNCHANGED)
            if im[0,0].shape[0] == 4:
                im[where(im[:,:,3] == 0)] = [255, 255, 255, 255]
                im = cvtColor(im, COLOR_BGRA2GRAY)
            else:
                im = cvtColor(im, COLOR_BGR2GRAY)
        else:
            from cv2 import IMREAD_GRAYSCALE
            im = imread(path, IMREAD_GRAYSCALE)
            
        if np_sum(im==255)/prod(im.shape) > 0.5:
            Color.info(f'    Image {os.path.basename(path)} seems to be a graph but is a {ext} image')        
        
    return path
    
    

def get_image(tag):
    for name in (tag, tag+'-eps-converted-to'):
        for ext in img_ext:
            if name.endswith(ext):
                ext = ''
                break
        if ext == '':
            for src in texinputs:
                if os.path.exists(src + name):
                    return check_image(src+name)
        for ext in img_ext:
            for src in texinputs:
                if os.path.exists(src + name + ext):
                    return check_image(src+name+ext)
    Color.error('    Image not found: ' + tag)
    sys.exit(0)
    
images = []
for line in content:

    if '\\graphicspath' in line:
        line = '\\graphicspath{{fig/}}'
        Color.ok('  extracting images...')
    elif '\\includegraphics' in line:
        tags = {}
        figs = [s.split('}')[0] for s in line.split('{')]
        for i,f in enumerate(figs[1:]):
            if '\\includegraphics' in figs[i]:
                src = get_image(f)
                tags[f] = os.path.basename(src)
                copy_image(src, fig_dir + tags[f])
                if tags[f] in images:
                    print(f'Image {tags[f]} appears several times')
                images.append(tags[f])
        line = dict_replace(line, tags)
    elif '\\begin{overpic}' in line:
        f = tex_arg(line.replace('{overpic}', ''))
        src = get_image(f)
        tag = os.path.basename(src)
        if tag in images:
            print(f'Image {tag} appears several times')
        images.append(tag)
        copy_image(src, fig_dir + tag)
        line = line.replace(f, tag)
    else:
        src, dst, rep = extract_bib_info(line)
        if src:
            for i,s in enumerate(src):
                s = src[i]
                d = dst[i]
                if d.endswith('bib') and not d.endswith('IEEEabrv.bib'):
                    os.system(f'python3 {os.path.dirname(__file__)}/clean_bib.py "{s}" "{d}" -q -s "{tex}"')
                else:
                    shutil.copy(s, d)                
            line = dict_replace(line, rep)
    new_content.append(line)
        
with open(preprint_dir + 'FINAL_VERSION.tex', 'w') as f:
    f.write('\n'.join(new_content))
