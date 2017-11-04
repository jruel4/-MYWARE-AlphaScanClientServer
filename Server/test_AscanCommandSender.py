# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 23:27:54 2017

@author: marzipan
"""

import asyncio
import unittest
import inspect
import logging
import sys

from AlphaScanClientServer.Server.Errors import CommunicationErrors
from AlphaScanClientServer.Server.AscanCommandSender import AscanCommandSender, validate_json
from AlphaScanClientServer.Stubs.stub_websockets import stub_websockets

def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

class ValidateJSONTest(unittest.TestCase):
    def setUp(self):
        self.ws = stub_websockets()
        self.err_handler = CommunicationErrors(self.ws)

    def test_decoratorBadParameterChecking(self):        
        # Should only accept one input non-keyword argument
        self.assertRaises(TypeError, validate_json, *[ {}, {} ], **{"json_error_handler_dec_param":None})
        
        # Input must be a dictionary
        self.assertRaises(AssertionError, validate_json, *[ [] ])
        
        # Dictionary keys must be strings
        self.assertRaises(AssertionError, validate_json, *[ {"a":1, 1:1, } ])
        
        # Dictionary values should be either type or list with first element as type
        self.assertRaises(AssertionError, validate_json, *[ {"a":1, } ] )
        self.assertRaises(AssertionError, validate_json, *[ {"a":[], } ])
#        with self.assertRaises(AssertionError):

    @validate_json({}, json_error_handler_dec_param=1)
    def _bad_error_handler(self):
        return

    @validate_json({"x":int})
    def _one_arg(self,x):
        return x

    

    # JSON error handler MUST be CommunicationErrors instance
    def test_badErrorHandler(self):

        # Test when we give the decorator an incorrect handle
        self.assertRaises(AssertionError, _run, *[ self._bad_error_handler('{}') ], **{})

        # Test when the instance in the class is incorrect
        tmp_handle = self.err_handler
        self.err_handler = 1
        self.assertRaises(AssertionError, _run, *[ self._one_arg('{"x": 100}') ], **{})
        self.err_handler = tmp_handle

    def test_badJSON(self):
        self.assertEqual(_run(self._one_arg('GARBAGE_JSON')), self.err_handler.ERRORS["ERR_OTHER"][0])

    # NOTE: NO ERROR WILL BE RAISED IF WE RECEIVE TOO MANY PARAMETERS, only not enough
    # for example, _run(self.one_arg('{"x": 100, "y": 100}')) will not raise any errors
    def test_incorrectNumberOfParameters(self):
        self.assertEqual(_run(self._one_arg('{}')), self.err_handler.ERRORS["ERR_BAD_NUM_PARAMS"][0])
        
    def test_inccorectParameterType(self):
        pass
    def test_incorrectParameterShouldNotBeList(self):
        pass
    def test_incorrectParameterShouldBeList(self):
        pass

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger( "SomeTest.testSomething" ).setLevel( logging.INFO )
    unittest.main()