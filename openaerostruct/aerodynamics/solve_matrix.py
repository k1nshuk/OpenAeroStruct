from __future__ import print_function
import numpy as np
from scipy.linalg import lu_factor, lu_solve

from openmdao.api import ImplicitComponent


class SolveMatrix(ImplicitComponent):

    def initialize(self):
        self.options.declare('surfaces', types=list)

    def setup(self):
        surfaces = self.options['surfaces']

        system_size = 0

        for surface in self.options['surfaces']:
            nx = surface['num_x']
            ny = surface['num_y']

            system_size += (nx - 1) * (ny - 1)

        self.system_size = system_size

        self.add_input('mtx', shape=(system_size, system_size), units='1/m')
        self.add_input('rhs', shape=system_size, units='m/s')
        self.add_output('circulations', shape=system_size, units='m**2/s')

        self.declare_partials('circulations', 'circulations',
            rows=np.outer(np.arange(system_size), np.ones(system_size, int)).flatten(),
            cols=np.outer(np.ones(system_size, int), np.arange(system_size)).flatten(),
        )
        self.declare_partials('circulations', 'mtx',
            rows=np.outer(np.arange(system_size), np.ones(system_size, int)).flatten(),
            cols=np.arange(system_size ** 2),
        )
        self.declare_partials('circulations', 'rhs', val=-1.,
            rows=np.arange(system_size),
            cols=np.arange(system_size),
        )

    def apply_nonlinear(self, inputs, outputs, residuals):
        residuals['circulations'] = inputs['mtx'].dot(outputs['circulations']) - inputs['rhs']

    def solve_nonlinear(self, inputs, outputs):
        self.lu = lu_factor(inputs['mtx'])

        outputs['circulations'] = lu_solve(self.lu, inputs['rhs'])

    def linearize(self, inputs, outputs, partials):
        system_size = self.system_size

        self.lu = lu_factor(inputs['mtx'])

        partials['circulations', 'circulations'] = inputs['mtx'].flatten()
        partials['circulations', 'mtx'] = \
            np.outer(np.ones(system_size), outputs['circulations']).flatten()

    def solve_linear(self, d_outputs, d_residuals, mode):
        if mode == 'fwd':
            d_outputs['circulations'] = lu_solve(self.lu, d_residuals['circulations'], trans=0)
        else:
            d_residuals['circulations'] = lu_solve(self.lu, d_outputs['circulations'], trans=1)
