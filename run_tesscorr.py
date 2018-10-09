# -*- coding: utf-8 -*-
"""
Command-line utility to run TESS detrend correction from command-line.

Note:
    This file is intended as an addition to the code
    `tess_detrend` by Derek Buzasi <dbuzasi@fgcu.edu>

    It allows for small tests of single target inputs from
    a variety of formats, including FITS and text files,
    and provides an option for debugging and maintenance
Structure inspired by `tessphot` by Rasmus Handberg <rasmush@phys.au.dk>

"""

# photometry runs under Python 2, so compatibility is an issue without this
from __future__ import with_statement, print_function
import os
import argparse
import fnmatch
import logging
import functools
from corrections import tesscorr, taskmanager

#------------------------------------------------------------------------------
if __name__ == '__main__':

	# Parse command line arguments:
	parser = argparse.ArgumentParser(description='Run TESS Corrector pipeline on single star.')
	parser.add_argument('-m', '--method', help='Corrector method to use.', default=None, choices=('ensemble', 'cbv'))
	parser.add_argument('-d', '--debug', help='Print debug messages.', action='store_true')
	parser.add_argument('-q', '--quiet', help='Only report warnings and errors.', action='store_true')
	parser.add_argument('-p', '--plot', help='Save plots when running.', action='store_true')
	parser.add_argument('-a', '--all', help='Run on random target from TODO-list.', action='store_true')
	parser.add_argument('-t', '--test', help='Use test data and ignore TESSCORR_INPUT environment variable.', action='store_true')
	parser.add_argument('starid', type=int, help='TIC identifier of target.', nargs='?', default=None)
	args = parser.parse_args()

	# Make sure at least one setting is given:
	if args.starid is None and not args.random:
		parser.error("Please select either a specific STARID or ALL.")

	# Set logging level:
	logging_level = logging.INFO
	if args.quiet:
		logging_level = logging.WARNING
	elif args.debug:
		logging_level = logging.DEBUG

	# Setup logging:
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	console = logging.StreamHandler()
	console.setFormatter(formatter)
	logger = logging.getLogger(__name__)
	logger.addHandler(console)
	logger.setLevel(logging_level)
	logger_parent = logging.getLogger('corrector')
	logger_parent.addHandler(console)
	logger_parent.setLevel(logging_level)

	# Get input and output folder from environment variables:
	test_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'tests', 'input'))
	if args.test:
		input_folder = test_folder
	else:
		input_folder = os.environ.get('TESSCORR_INPUT', test_folder)
	output_folder = os.environ.get('TESSCORR_OUTPUT', os.path.abspath('.'))
	logger.info("Loading input data from '%s'", input_folder)
	logger.info("Putting output data in '%s'", output_folder)

	# Create partial function of tesscorr, setting the common keywords:
	f = functools.partial(tesscorr, input_folder=input_folder, output_folder=output_folder, plot=args.plot)

	# Run the program:
	with taskmanager.TaskManager(input_folder) as tm:
		if args.starid is not None:
			task = tm.get_task(starid=args.starid)
		elif args.all:	
			task = tm.get_all()

		corr = f(**task)

	# Write out the results?
	if not args.quiet:
		print("=======================")
		print("STATUS: {0}".format(corr.status.name))

