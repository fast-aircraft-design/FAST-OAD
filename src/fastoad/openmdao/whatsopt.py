"""WhatsOpt-related operations."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
#  FAST is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from os import PathLike
from typing import Union

import openmdao.api as om
import whatsopt.whatsopt_client as wop

from fastoad import __version__ as fastoad_version
from fastoad._utils.files import make_parent_dir


def write_xdsm(
    problem: om.Problem,
    xdsm_file_path: Union[str, PathLike] = None,
    depth: int = 2,
    wop_server_url: str = None,
    dry_run: bool = False,
):
    """
    Makes WhatsOpt generate a XDSM in HTML file.

    :param problem: a Problem instance. final_setup() must have been run.
    :param xdsm_file_path: the path for HTML file to be written (will overwrite if needed)
    :param depth: the depth analysis for WhatsOpt
    :param wop_server_url: URL of WhatsOpt server (if None, ether.onera.fr/whatsopt will be used)
    :param dry_run: if True, will run wop without sending any request to the server. Generated
                    XDSM will be empty. (for test purpose only)
    """

    make_parent_dir(xdsm_file_path)

    if not wop_server_url:
        wop_server_url = wop.EXTRANET_SERVER_URL

    wop_session = wop.WhatsOpt(url=wop_server_url)

    xdsm = wop_session.push_mda(
        problem, {"--xdsm": True, "--name": None, "--depth": depth, "--dry-run": dry_run}
    )
    wop.generate_xdsm_html(f"FAST-OAD {fastoad_version}", xdsm=xdsm, outfilename=xdsm_file_path)
