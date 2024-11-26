# run resulting page locally with:
#   cd .\Projects\personal-page\
#   python -m http.server 8000

from core.site import Site
import yaml

with open('config.yaml', 'r') as stream:
    config = yaml.safe_load(stream)
Site(config).generate_static_files()
