#
#  Copyright (C) 2019 Bloomberg Finance LP
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library. If not, see <http://www.gnu.org/licenses/>.
# Pylint doesn't play well with fixtures and dependency injection from pytest
# pylint: disable=redefined-outer-name

import os
import pytest

from buildstream import _yaml
from buildstream._exceptions import ErrorDomain
from buildstream.testing import cli  # pylint: disable=unused-import

from tests.conftest import clean_platform_cache

pytestmark = pytest.mark.integration


DATA_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "project"
)


@pytest.mark.datafiles(DATA_DIR)
def test_force_sandbox(cli, datafiles):
    project = str(datafiles)
    element_path = os.path.join(project, 'elements', 'element.bst')

    # Write out our test target
    element = {
        'kind': 'script',
        'depends': [
            {
                'filename': 'base.bst',
                'type': 'build',
            },
        ],
        'config': {
            'commands': [
                'true',
            ],
        },
    }
    _yaml.roundtrip_dump(element, element_path)

    clean_platform_cache()

    # Build without access to host tools, this will fail
    result = cli.run(project=project, args=['build', 'element.bst'], env={'PATH': '', 'BST_FORCE_SANDBOX': 'bwrap'})
    result.assert_main_error(ErrorDomain.PLATFORM, None)
    assert "Bubblewrap not found" in result.stderr
    # we have asked for a spesific sand box, but it is not avalble so
    # bst should fail early and the element should be waiting
    assert cli.get_element_state(project, 'element.bst') == 'waiting'


@pytest.mark.datafiles(DATA_DIR)
def test_dummy_sandbox_fallback(cli, datafiles):
    project = str(datafiles)
    element_path = os.path.join(project, 'elements', 'element.bst')

    # Write out our test target
    element = {
        'kind': 'script',
        'depends': [
            {
                'filename': 'base.bst',
                'type': 'build',
            },
        ],
        'config': {
            'commands': [
                'true',
            ],
        },
    }
    _yaml.roundtrip_dump(element, element_path)

    clean_platform_cache()

    # Build without access to host tools, this will fail
    result = cli.run(project=project, args=['build', 'element.bst'], env={'PATH': '', 'BST_FORCE_SANDBOX': None})
    # But if we dont spesify a sandbox then we fall back to dummy, we still
    # fail early but only once we know we need a facny sandbox and that
    # dumy is not enough, there for element gets fetched and so is buildable

    result.assert_task_error(ErrorDomain.SANDBOX, 'unavailable-local-sandbox')
    assert cli.get_element_state(project, 'element.bst') == 'buildable'