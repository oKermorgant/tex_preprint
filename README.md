# Python tool to create clean tex preprints

Run `gen_preprint.py` with the path to the article tex file or its folder, a folder `folder_preprint` will be created with:
 - cleaned bibliography files (only references from the paper, warnings on pages / strange journal or conference name)
 - only images actually used with warnings for png/jpg files that seem to be graphs (and should be PDF)
 
