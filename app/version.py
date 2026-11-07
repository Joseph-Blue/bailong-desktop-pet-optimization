# Preserve the upstream version; increment the branch's build metadata for
# each local iteration (0.5.1+optimization.1, 0.5.1+optimization.2, ...).
BASE_VERSION = '0.5.1'
BRANCH = 'joseph/optimization'
BRANCH_REVISION = 3
VERSION = f'{BASE_VERSION}+optimization.{BRANCH_REVISION}'
