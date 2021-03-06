from __future__ import division, print_function

import numpy as np
from six import iteritems

from openmdao.api import ExplicitComponent

from dymos.utils.constants import INF_BOUND


class BoundaryConstraintComp(ExplicitComponent):

    def initialize(self):
        self.options.declare('loc', values=('initial', 'final'),
                             desc='the location in the phase of this boundary constraint '
                                  '(either \'initial\' or \'final\'')
        self._constraints = []
        self._vars = {}

    def setup(self):
        """
        Define the independent variables as output variables.
        """
        for (name, kwargs) in self._constraints:
            input_name = '{0}_value_in:{1}'.format(self.options['loc'], name)
            output_name = '{0}_value:{1}'.format(self.options['loc'], name)
            self._vars[name] = {'input_name': input_name,
                                'output_name': output_name,
                                'shape': kwargs['shape']}

            # self._vars.append((input_name, output_name, kwargs['shape']))

            input_kwargs = {k: kwargs[k] for k in ('units', 'shape', 'desc')}
            self.add_input(input_name, **input_kwargs)

            output_kwargs = {k: kwargs[k] for k in ('units', 'shape', 'desc')}
            self.add_output(output_name, **output_kwargs)

            constraint_kwargs = {k: kwargs.get(k, None)
                                 for k in ('lower', 'upper', 'equals', 'ref', 'ref0', 'adder',
                                           'scaler', 'indices', 'linear')}
            self.add_constraint(output_name, **constraint_kwargs)

        # Setup partials
        for name, options in iteritems(self._vars):
            size = int(np.prod(options['shape']))

            rs = np.arange(size)
            cs = np.arange(size)

            self.declare_partials(of=options['output_name'],
                                  wrt=options['input_name'],
                                  val=np.ones(size),
                                  rows=rs,
                                  cols=cs)

    def compute(self, inputs, outputs):

        for name, options in iteritems(self._vars):
            outputs[options['output_name']] = inputs[options['input_name']]

    def _add_constraint(self, name, shape=(1,), units=None, res_units=None, desc='',
                        lower=None, upper=None, equals=None,
                        scaler=None, adder=None, ref=1.0, ref0=0.0,
                        linear=False, res_ref=1.0, distributed=False):
        """
        Add an initial constraint to this component

        Parameters
        ----------
        name : str
            name of the variable in this component's namespace.
        val : float or list or tuple or ndarray
            The initial value of the variable being added in user-defined units. Default is 1.0.
        shape : int or tuple or list or None
            Shape of this variable, only required if val is not an array.
            Default is None.
        units : str or None
            Units in which the output variables will be provided to the component during execution.
            Default is None, which means it has no units.
        res_units : str or None
            Units in which the residuals of this output will be given to the user when requested.
            Default is None, which means it has no units.
        desc : str
            description of the variable
        lower : float or list or tuple or ndarray or None
            lower bound(s) in user-defined units. It can be (1) a float, (2) an array_like
            consistent with the shape arg (if given), or (3) an array_like matching the shape of
            val, if val is array_like. A value of None means this output has no lower bound.
            Default is None.
        upper : float or list or tuple or ndarray or None
            upper bound(s) in user-defined units. It can be (1) a float, (2) an array_like
            consistent with the shape arg (if given), or (3) an array_like matching the shape of
            val, if val is array_like. A value of None means this output has no upper bound.
            Default is None.
        scaler : float or None
            A multiplicative scaler on the constraint value for the optimizer.
        adder : float or None
            A parameter which is added to the value before scaler is applied to produce
            the value seen by the optimizer.
        ref : float or None
            Scaling parameter. The value in the user-defined units of this output variable when
            the scaled value is 1. Default is 1.
        ref0 : float or None
            Scaling parameter. The value in the user-defined units of this output variable when
            the scaled value is 0. Default is 0.
        linear : bool
            True if the *total* derivative of the constrained variable is linear, otherwise False.
        res_ref : float
            Scaling parameter. The value in the user-defined res_units of this output's residual
            when the scaled value is 1. Default is 1.
        distributed : bool
            If True, this variable is distributed across multiple processes.
        """
        lower = -INF_BOUND if upper is not None and lower is None else lower
        upper = INF_BOUND if lower is not None and upper is None else upper
        kwargs = {'shape': shape, 'units': units, 'res_units': res_units, 'desc': desc,
                  'lower': lower, 'upper': upper, 'equals': equals,
                  'scaler': scaler, 'adder': adder, 'ref': ref, 'ref0': ref0, 'linear': linear,
                  'res_ref': res_ref, 'distributed': distributed}
        self._constraints.append((name, kwargs))
