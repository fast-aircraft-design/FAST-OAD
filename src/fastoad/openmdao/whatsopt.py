"""WhatsOpt-related operations."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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

import logging

import openmdao.api as om
import requests
import whatsopt.whatsopt_client as wop

from fastoad._utils.files import make_parent_dir

_LOGGER = logging.getLogger(__name__)  # Logger for this module


def write_xdsm(
    problem: om.Problem,
    xdsm_file_path: str = None,
    depth: int = 2,
    wop_server_url=None,
    api_key=None,
):
    """
    Makes WhatsOpt generate an XDSM in HTML file.

    :param problem: a Problem instance. final_setup() must have been run.
    :param xdsm_file_path: the path for HTML file to be written (will overwrite if needed)
    :param depth: the depth analysis for WhatsOpt
    :param wop_server_url: URL of WhatsOpt server
    :param api_key: the API key to connect to WhatsOpt server
    """

    make_parent_dir(xdsm_file_path)

    wop_session = wop.WhatsOpt(url=wop_server_url, login=False)

    try:
        ok = wop_session.login(api_key=api_key, echo=False)
    except requests.exceptions.ConnectionError:

        if not wop_server_url and wop_session.url == wop.INTRANET_SERVER_URL:
            used_url = wop_session.url
            # If connection failed while attempting to reach the wop default URL,
            # that is the internal ONERA server, try with the external server
            try:
                wop_session = wop.WhatsOpt(url=wop.EXTRANET_SERVER_URL)
                ok = wop_session.login(api_key=api_key, echo=False)
            except requests.exceptions.ConnectionError:
                _LOGGER.warning("Failed to connect to %s and %s", used_url, wop.EXTRANET_SERVER_URL)
                return
        else:
            _LOGGER.warning("Failed to connect to %s", wop_session.url)
            return

    if ok:
        xdsm = wop_session.push_mda(
            problem, {"--xdsm": True, "--name": None, "--dry-run": False, "--depth": depth}
        )
        wop.generate_xdsm_html(xdsm=xdsm, outfilename=xdsm_file_path)
    else:
        wop_session.logout()
        _LOGGER.warning("Could not login to %s", wop_session.url)
