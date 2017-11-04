# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 23:28:15 2017

@author: marzipan
"""

import asyncio
import unittest
import inspect
import logging
import sys

from AlphaScanClientServer.Server.Errors import CommunicationErrors
from AlphaScanClientServer.Stubs.stub_websockets import stub_websockets

def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

class ErrorsTestCase(unittest.TestCase):
    def setUp(self):
        self.ws = stub_websockets()
        self.err = CommunicationErrors(self.ws)

        # Get all of the member names and functions in the error class        
        self.err_members = inspect.getmembers(self.err, predicate=inspect.ismethod)
        self.err_member_names = [name_str for name_str,func in self.err_members if name_str != "__init__"]
        self.err_member_functions = [func for name_str,func in self.err_members if name_str != "__init__"]

    def test_ErrorCodeListContainsAllErrorFunctions(self):        
        # Make sure the length of the list of members is equal to the length of the ERRORS array
        self.assertEqual(len(self.err_member_names), len(self.err.ERRORS))
        # If it is, then as long as all functions are in the list (b/c function names are unique)
        # then they are equal
        for n in self.err_member_names:
            self.assertIn(n, self.err.ERRORS)
            
    def test_ErrorFunctionsSendCorrectErrorCodes(self):
        for name, func in self.err_members:
            if name != "__init__":
                _run(func()) #send error code to dummy WS object
                self.assertEqual(name, self.ws.last_sent)
    
    def test_ErrorFunctionsReturnCorrectErrorCodes(self):
        for name, func in self.err_members:
            if name != "__init__":
                self.assertEqual(self.err.ERRORS[name][0], _run(func()))
        
            
if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger( "SomeTest.testSomething" ).setLevel( logging.INFO )
    unittest.main()