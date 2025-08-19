import numpy as np
import pandas as pd
import pytest

from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import AbstractFuelPropulsion
from fastoad.models.performances.mission.polar import Polar


@pytest.fixture
def polar() -> Polar:
    """Returns a dummy polar where max L/D ratio is around 16."""
    cl = np.arange(0.0, 1.5, 0.01)
    cd = 0.5e-1 * cl**2 + 0.01
    return Polar(cl, cd)


def print_dataframe(df):
    """Utility for correctly printing results"""
    # Not used if all goes well. Please keep it for future test setting/debugging.
    with pd.option_context(
        "display.max_rows", 20, "display.max_columns", None, "display.width", None
    ):
        print()
        print(df)


class DummyEngine(AbstractFuelPropulsion):
    def __init__(self, max_thrust, max_sfc):
        """
        Dummy engine model.

        Max thrust does not depend on flight conditions.
        SFC varies linearly with thrust_rate, from max_sfc/2. at thrust rate is 0.,
        to max_sfc when thrust_rate is 1.0

        :param max_thrust: thrust when thrust rate = 1.0
        :param max_sfc: SFC when thrust rate = 1.0
        """
        self.max_thrust = max_thrust
        self.max_sfc = max_sfc

    def compute_flight_points(self, flight_point: FlightPoint):
        if flight_point.thrust_is_regulated or flight_point.thrust_rate is None:
            flight_point.thrust_rate = flight_point.thrust / self.max_thrust
        else:
            flight_point.thrust = self.max_thrust * flight_point.thrust_rate

        flight_point.sfc = self.max_sfc * (1.0 + flight_point.thrust_rate) / 2.0


class DummyUnpickableEngine(DummyEngine):
    def __init__(self, max_thrust, max_sfc, file_name):
        """
        Unpickable dummy engine model, inherites from DummyEngine.
        """
        DummyEngine.__init__(self, max_thrust, max_sfc)
        self.data = open(file_name, "r")

    def close_file(self):
        """Utility function to manually close the datafile."""
        self.data.close()
