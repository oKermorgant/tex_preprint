#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os,sys,shutil
import bibtexparser

def error(s):
    print('\033[1;31;58m    ' + s + '\033[1;37;0m')

def info(s):
    print('\033[1;34;48m    ' + s + '\033[1;37;0m')
    
abbrev = {}
abbrev['international'] = 'Int.'
abbrev['conference'] = 'Conf.'
abbrev['symposium'] = 'Symp.'
abbrev['transactions'] = 'Trans.'
abbrev['proceedings'] = 'Proc.'
keep_lower = ('on', 'and', 'of', 'et')
keep_upper = ('ieee','ieee/rsj','ifac','iarp','iet','iapr', 'spie')

def reformat(conf):
    for key in abbrev:
        dst = abbrev[key]
        for src in (key, key.upper(), key.title()):       
            conf = conf.replace(src, dst)
    new_conf = []
    for elem in conf.split():
        if elem in keep_lower:
            new_conf.append(elem)
        elif elem in keep_upper:
            new_conf.append(elem.upper())
        else:
            new_conf.append(elem[0].upper() + elem[1:])
    return ' '.join(new_conf)

# my defaults
srcFile = 'bib_Tout.bib'
dstFile = 'bib_Conf.bib'
tex = ''

if len(sys.argv) > 1:
    srcFile = sys.argv[1]
    dstFile = srcFile
    if len(sys.argv) > 2:
        dstFile = sys.argv[2]
        
if '-s' in sys.argv:
    tex = sys.argv[sys.argv.index('-s')+1]
    
if tex != '' and srcFile == dstFile:
    error('clean bib: no output file given but filtering wrt tex file')
    sys.exit(0)
        
quiet = '-q' in sys.argv
remove_pages = (tex == '' and srcFile != dstFile)

if not quiet:
    print('Original file: ' + os.path.abspath(srcFile))   
    print('Final file: ' + os.path.abspath(dstFile))
    if remove_pages:
        print('Removing volume / page / numbering')
    else:
        print('Keeping volume / page / numbering')
        
    input('  Enter to continue, Ctrl-C to cancel ')
            
shutil.copy(srcFile, srcFile + '.bak')

if os.path.lexists(srcFile):
    print('\033[1;32;48m Cleaning references from ' + srcFile + '\033[1;37;0m')
  
    with open(srcFile) as f:
        bib = f.read()
        # bug in bibtexparser if last element is without ending comma
    bib = bib.replace(',\n}', '\n}').replace('\n}', ',\n}')
    bib = bibtexparser.loads(bib)
    
    # clear double references
    ids = sorted([ref['ID'] for ref in bib.entries if 'ID' in ref])
    multiple = []
    for i in range(len(ids)-1):
        if ids[i] == ids[i+1] and ids[i] not in multiple:
            multiple.append(ids[i])
    
    for m in multiple:
        refs = [ref for ref in bib.entries if 'ID' in ref and ref['ID'] == m]
        for ref in refs[1:]:
            if ref == refs[0]:
                bib.entries.remove(ref)
                print('  Removing similar reference {}'.format(m))
            else:
                used = ref['ID'] in tex
                if used or not tex:
                    error(' Multiple reference: {}'.format(m))
                if used:
                    sys.exit(0)

    # always worth it to clean the source

    for ref in bib.entries:
        used = tex == '' or ref['ID'] in tex
        if ref['ENTRYTYPE'] == 'inproceedings' and 'booktitle' not in ref:
            if used:
                error('Bad ref in {}: no conference name'.format(ref['ID']))
        elif ref['ENTRYTYPE'] == 'article' and 'journal' not in ref:
            if used:
                error('Bad ref in {}: no journal name'.format(ref['ID']))
        else: 
            for key in ('booktitle', 'journal'):
                if key in ref:
                    conf = ref[key].lower()
                    
                    # remove conf numbers
                    for n in range(50, 0, -1):
                        if not sum(s.isdigit() for s in conf):
                            break
                        for suff in ('st','nd','th'):
                            for ext in ('.', ''):
                                number = '{}{}{}'.format(n,suff,ext)
                                if number in conf:
                                    conf = conf.replace(number, '')             
                    
                    if used:
                        if conf.endswith(' on') or ('proceedings' in conf and 'society' not in conf and 'volumes' not in conf) or sum(s.isdigit() for s in conf):
                            error('Strange title in {}: "{}"'.format(ref['ID'], ref[key]))
                        if 'pages' not in ref and 'workshop' not in conf:
                            info('No pages in {}: "{}"'.format(ref['ID'], ref[key]))
                    
                    ref[key] = reformat(conf)
                
    with open(srcFile, 'w') as f:
        bibtexparser.dump(bib, f)
        
    if not quiet:
        print('removing keys from ' + srcFile + ' to ' + dstFile)

    dNew = []
    if remove_pages:
        to_remove = ['pages', 'volume','number', 'crossref', 'url', 'doi']
    else:
        to_remove = ['crossref', 'url', 'doi']
    
    if tex:
        with open(tex) as f:
            tex = f.read()
        bib.entries = [ref for ref in bib.entries if 'ID' not in ref or ref['ID'] in tex]
        
    for ref in bib.entries:
        for key in to_remove:
            if key in ref:
                ref.pop(key)
        
    with open(dstFile, 'w') as f:
        bibtexparser.dump(bib, f)
