# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 23:28:15 2017

@author: marzipan
"""

import unittest
import inspect
import logging
import sys

from AlphaScanClientServer.Server.Errors import CommunicationErrors
from AlphaScanClientServer.Stubs.stub_websockets import stub_websockets

class ErrorsTestCase(unittest.TestCase):
    def setUp(self):
        self.ws = stub_websockets()
        self.err = CommunicationErrors(self.ws)
    def test_ErrorCodeListContainsAllErrorFunctions(self):
        # Get all of the member names in the class
        members = inspect.getmembers(self.err, predicate=inspect.ismethod)
        member_names = [m for m,_ in members]
        # Remove init, it doesn't represent an error code
        member_names.remove("__init__")
        
        # Make sure the length of the list of members is equal to the length of the ERRORS array
        self.assertEqual(len(member_names), len(self.err.ERRORS))
        # If it is, then as long as all functions are in the list (b/c function names are unique)
        # then they are equal
        for m in member_names:
            self.assertIn(m, self.err.ERRORS)
            
    def test_ErrorFunctionsSendCorrectErrorCodes(self):
        pass
    
    def test_ErrorFunctionsReturnCorrectErrorCodes(self):
        members = inspect.getmembers(self.err, predicate=inspect.ismethod)
        for m, func in members:
            if m != "__init__":
                self.assertEqual(self.err.ERRORS[m][0], func())
        
            
if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger( "SomeTest.testSomething" ).setLevel( logging.INFO )
    unittest.main()