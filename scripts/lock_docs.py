"""Record the installed documentation dependency closure, excluding app packages."""
from importlib.metadata import distribution
from pathlib import Path
from packaging.requirements import Requirement

pending = ['zensical', 'packaging']
locked = {}
while pending:
    dist = distribution(pending.pop())
    name = dist.metadata['Name']
    if name in locked:
        continue
    locked[name] = dist.version
    for spec in dist.requires or []:
        requirement = Requirement(spec)
        if requirement.marker is None or requirement.marker.evaluate():
            pending.append(requirement.name)
Path('requirements-docs.txt').write_text(
    '# Validated documentation dependency closure; regenerate with scripts/lock_docs.py\n'
    + ''.join(f'{name}=={version}\n' for name, version in sorted(locked.items(), key=lambda x: x[0].lower()))
)
